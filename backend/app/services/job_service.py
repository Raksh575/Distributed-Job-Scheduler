import uuid
import traceback
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.core import Job, JobExecution, Queue, DeadLetterQueue, RetryPolicy
from app.repositories.core import JobRepository, JobExecutionRepository, QueueRepository

class JobService:
    """
    JobService orchestrates background task lifecycle transitions, atomic locks,
    parent-child dependency evaluations, and backoff retry calculations.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.job_repo = JobRepository(db_session)
        self.execution_repo = JobExecutionRepository(db_session)
        self.queue_repo = QueueRepository(db_session)

    async def submit_job(
        self,
        queue_id: uuid.UUID,
        name: str,
        payload: Dict[str, Any],
        parent_id: Optional[uuid.UUID] = None,
        delay_seconds: Optional[int] = None,
        priority: int = 0,
        max_retries: int = 3,
        timeout: Optional[int] = None,
        creator_id: Optional[uuid.UUID] = None
    ) -> Job:
        """Submit a job, evaluating dependencies and delays to set status (created, queued, or scheduled)."""
        # Ensure queue exists and is active
        queue = await self.queue_repo.get_by_id(queue_id)
        if not queue:
            raise NotFoundException(message="Target queue not found.", code="QUEUE_NOT_FOUND")

        # Determine run_at timestamp
        run_at = datetime.now(timezone.utc)
        if delay_seconds:
            run_at += timedelta(seconds=delay_seconds)

        # Set initial status
        if parent_id:
            # Check parent status
            parent = await self.job_repo.get_by_id(parent_id)
            if not parent:
                raise NotFoundException(message="Parent job dependency not found.", code="PARENT_NOT_FOUND")
            
            if parent.status == "success":
                # Parent succeeded already, proceed to queued or scheduled
                status = "scheduled" if delay_seconds else "queued"
            elif parent.status in ("failed", "cancelled"):
                raise BadRequestException(
                    message="Cannot chain job to a failed or cancelled parent dependency.",
                    code="PARENT_DEPENDENCY_FAILED"
                )
            else:
                # Parent is pending, child starts in 'created' state waiting for success trigger
                status = "created"
        else:
            status = "scheduled" if delay_seconds else "queued"

        job = Job(
            queue_id=queue_id,
            name=name,
            status=status,
            payload=payload,
            parent_id=parent_id,
            run_at=run_at,
            priority=priority,
            max_retries=max_retries,
            retries_count=0,
            timeout=timeout,
            created_by=creator_id
        )
        return await self.job_repo.create(job)

    async def get_job(self, job_id: uuid.UUID) -> Job:
        """Fetch job, raising error if not found."""
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundException(message="Job not found.", code="JOB_NOT_FOUND")
        return job

    async def cancel_job(self, job_id: uuid.UUID, updater_id: Optional[uuid.UUID] = None) -> Job:
        """Cancel a queued, scheduled, or created job."""
        job = await self.get_job(job_id)
        if job.status in ("success", "failed", "cancelled"):
            raise BadRequestException(
                message=f"Cannot cancel job in terminal status '{job.status}'.",
                code="TERMINAL_STATUS"
            )

        job = await self.job_repo.update(job, {"status": "cancelled", "updated_by": updater_id})

        if job.workflow_id:
            from app.services.workflow_service import WorkflowService
            workflow_svc = WorkflowService(self.db)
            await workflow_svc.check_and_update_workflow_status(job.workflow_id)
            
        return job

    async def claim_next_job(self, worker_id: uuid.UUID, allowed_queue_ids: List[uuid.UUID]) -> Optional[Job]:
        """
        Atomically claim the next eligible job from the database using SELECT FOR UPDATE SKIP LOCKED.
        Verifies queue is active and evaluates parent dependency success.
        """
        if not allowed_queue_ids:
            return None

        # 1. Fetch active queue IDs
        active_queues_stmt = (
            select(Queue.id)
            .where(Queue.id.in_(allowed_queue_ids), Queue.is_active == True, Queue.deleted_at == None)
        )
        active_queue_results = await self.db.execute(active_queues_stmt)
        active_ids = [r[0] for r in active_queue_results.all()]
        
        if not active_ids:
            return None

        # 2. Select next eligible job
        # Filter rules:
        # - Status is 'queued'
        # - run_at is in the past
        # - Belongs to an active, unsubscribed queue
        # - Parent is resolved (parent_id is null or parent status is 'success')
        parent_success_stmt = (
            select(Job.id).where(Job.status == "success", Job.deleted_at == None)
        )
        
        stmt = (
            select(Job)
            .where(
                Job.status == "queued",
                Job.run_at <= datetime.now(timezone.utc),
                Job.queue_id.in_(active_ids),
                Job.deleted_at == None
            )
            .where(
                (Job.parent_id == None) |
                Job.parent_id.in_(parent_success_stmt)
            )
            .order_by(Job.priority.desc(), Job.run_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        
        result = await self.db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            return None

        # 3. Transition status to 'claimed'
        await self.job_repo.update(job, {"status": "claimed"})

        # 4. Create JobExecution record
        execution = JobExecution(
            job_id=job.id,
            worker_id=worker_id,
            status="running",
            started_at=datetime.now(timezone.utc)
        )
        await self.execution_repo.create(execution)

        return job

    async def update_job_progress(self, job_id: uuid.UUID, progress: int) -> None:
        """Update job completion progress percentage (0-100)."""
        job = await self.get_job(job_id)
        await self.job_repo.update(job, {"progress": min(max(progress, 0), 100)})

    async def finish_job(
        self,
        job_id: uuid.UUID,
        worker_id: uuid.UUID,
        status: str, # success or failed
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> None:
        """
        Transition job state to completed or evaluate retries and DLQ routing on failure.
        Unlocks waiting child jobs matching success/failure conditional executions.
        """
        job = await self.get_job(job_id)
        now = datetime.now(timezone.utc)

        # 1. Update active JobExecution details
        execution_stmt = (
            select(JobExecution)
            .where(JobExecution.job_id == job_id, JobExecution.worker_id == worker_id, JobExecution.completed_at == None)
            .order_by(JobExecution.started_at.desc())
            .limit(1)
        )
        exec_res = await self.db.execute(execution_stmt)
        execution = exec_res.scalar_one_or_none()
        
        if execution:
            await self.execution_repo.update(
                execution,
                {
                    "status": status,
                    "completed_at": now,
                    "error_message": error_message,
                    "duration_ms": duration_ms
                }
            )

        # 2. State Machine Transitions
        if status == "success":
            await self.job_repo.update(
                job,
                {
                    "status": "success",
                    "result": result,
                    "progress": 100,
                    "error_message": None
                }
            )
            
            # Trigger downstream children dependencies matching 'success' condition
            child_stmt = select(Job).where(Job.parent_id == job_id, Job.status == "created", Job.deleted_at == None)
            child_res = await self.db.execute(child_stmt)
            children = child_res.scalars().all()
            for child in children:
                execute_on = child.payload.get("execute_on", "success")
                if execute_on in ("success", "always"):
                    await self.job_repo.update(child, {"status": "queued", "run_at": now})
                else:
                    await self.job_repo.update(child, {"status": "cancelled", "error_message": "Skipped due to workflow condition filter."})

            if job.workflow_id:
                from app.services.workflow_service import WorkflowService
                workflow_svc = WorkflowService(self.db)
                await workflow_svc.check_and_update_workflow_status(job.workflow_id)
        else: # failed status
            # Run failure analyzer
            from app.services.failure_analyzer import failure_analyzer
            import json
            
            analysis = failure_analyzer.analyze_failure(error_message, job.payload)
            error_payload = {
                "message": error_message or "Unknown execution failure.",
                "analysis": analysis
            }
            serialized_error = json.dumps(error_payload)
            
            # Save the analysis directly onto the current execution row
            if execution:
                await self.execution_repo.update(execution, {"ai_analysis": analysis})

            # Evaluate retry policies
            if job.retries_count < job.max_retries:
                # Calculate backoff delay
                delay = await self._calculate_retry_backoff(job)
                next_run = now + timedelta(seconds=delay)
                
                await self.job_repo.update(
                    job,
                    {
                        "status": "queued", # Move back to queued for execution retry
                        "retries_count": job.retries_count + 1,
                        "run_at": next_run,
                        "error_message": serialized_error
                    }
                )
            else:
                # Retries exhausted. Move to Dead Letter Queue.
                await self.job_repo.update(
                    job,
                    {
                        "status": "failed",
                        "error_message": serialized_error
                    }
                )
                
                dlq_record = DeadLetterQueue(
                    job_id=job.id,
                    failed_at=now,
                    reason=serialized_error,
                    payload=job.payload
                )
                self.db.add(dlq_record)
                await self.db.flush()

                # Trigger downstream children dependencies matching 'failure' condition
                child_stmt = select(Job).where(Job.parent_id == job_id, Job.status == "created", Job.deleted_at == None)
                child_res = await self.db.execute(child_stmt)
                children = child_res.scalars().all()
                for child in children:
                    execute_on = child.payload.get("execute_on", "success")
                    if execute_on in ("failure", "always"):
                        await self.job_repo.update(child, {"status": "queued", "run_at": now})
                    else:
                        await self.job_repo.update(child, {"status": "cancelled", "error_message": "Skipped due to workflow condition filter."})

                if job.workflow_id:
                    from app.services.workflow_service import WorkflowService
                    workflow_svc = WorkflowService(self.db)
                    await workflow_svc.check_and_update_workflow_status(job.workflow_id)
    async def replay_job(self, job_id: uuid.UUID) -> Job:
        """Re-enqueue a completed, failed, or cancelled job."""
        job = await self.get_job(job_id)
        now = datetime.now(timezone.utc)
        
        updated_job = await self.job_repo.update(
            job,
            {
                "status": "queued",
                "retries_count": 0,
                "run_at": now,
                "error_message": None,
                "result": None,
                "progress": 0
            }
        )
        
        # Remove from DLQ if exists
        from app.models.core import DeadLetterQueue
        from sqlalchemy import delete
        stmt = delete(DeadLetterQueue).where(DeadLetterQueue.job_id == job_id)
        await self.db.execute(stmt)
        
        return updated_job

    async def _calculate_retry_backoff(self, job: Job) -> int:
        """Calculate next execution delay based on retry policies (exponential backoff fallback)."""
        # Fetch retry policy for job or queue
        stmt = (
            select(RetryPolicy)
            .where(
                (RetryPolicy.job_id == job.id) |
                (RetryPolicy.queue_id == job.queue_id)
            )
            .order_by(RetryPolicy.job_id.desc()) # prioritize job-specific policies
            .limit(1)
        )
        res = await self.db.execute(stmt)
        policy = res.scalar_one_or_none()

        # Fallback parameters
        max_retries = policy.max_retries if policy else 3
        backoff_factor = policy.backoff_factor if policy else 2.0
        initial_delay = policy.delay if policy else 5

        # Compute exponential backoff: initial_delay * (factor ** retry_index)
        delay = int(initial_delay * (backoff_factor ** job.retries_count))
        return min(delay, 86400) # Cap at 24 hours max backoff
