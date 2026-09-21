import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, BadRequestException
from app.models.core import Workflow, Job
from app.services.job_service import JobService

class WorkflowService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.job_service = JobService(db_session)

    async def get_workflow(self, workflow_id: uuid.UUID) -> Workflow:
        stmt = (
            select(Workflow)
            .where(Workflow.id == workflow_id)
            .options(selectinload(Workflow.jobs))
        )
        res = await self.db.execute(stmt)
        workflow = res.scalar_one_or_none()
        if not workflow:
            raise NotFoundException("Workflow not found.", "WORKFLOW_NOT_FOUND")
        return workflow

    async def list_workflows(self, project_id: uuid.UUID) -> List[Workflow]:
        stmt = (
            select(Workflow)
            .where(Workflow.project_id == project_id)
            .order_by(Workflow.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def submit_workflow(self, project_id: uuid.UUID, name: str, nodes: List[Dict[str, Any]], creator_id: uuid.UUID) -> Workflow:
        """
        Creates a Workflow and its jobs atomically.
        `nodes` should be a list of dictionaries with:
        - temp_id: string (local reference id)
        - name: string
        - queue_id: uuid string
        - payload: dict
        - dependencies: list of temp_ids
        - priority: int
        - max_retries: int
        """
        workflow = Workflow(project_id=project_id, name=name, status="running", created_by=creator_id)
        self.db.add(workflow)
        await self.db.flush() # flush to get workflow.id
        
        # We need to map temp_ids to real Job UUIDs to set up parent_id relationships
        job_map: Dict[str, uuid.UUID] = {}
        created_jobs = []

        # Topological sorting or resolving dependencies is left to the frontend to pass in correct order,
        # but to be safe we iterate nodes. Since we can create records with parent_id before the parent exists in DB (as long as we generate the ID),
        # wait, Job has an auto-generated UUID, but we can pre-generate it to satisfy foreign keys.
        
        for node in nodes:
            job_id = uuid.uuid4()
            job_map[node["temp_id"]] = job_id
            
            # For simplicity in this example, we assume each node has at most one parent dependency (chain).
            # If multiple dependencies exist, our current DB schema `parent_id` only supports a single parent.
            # To strictly support DAGs with multiple parents per node, we would need a many-to-many relationship,
            # but for this example, we'll use `parent_id` mapping to the primary/last dependency in the list.
            parent_id = None
            if node.get("dependencies"):
                parent_id = job_map.get(node["dependencies"][-1])

            status = "created" if parent_id else "queued"
            
            job = Job(
                id=job_id,
                queue_id=uuid.UUID(node["queue_id"]),
                name=node["name"],
                status=status,
                payload=node.get("payload", {}),
                parent_id=parent_id,
                workflow_id=workflow.id,
                priority=node.get("priority", 0),
                max_retries=node.get("max_retries", 3),
                created_by=creator_id
            )
            self.db.add(job)
            created_jobs.append(job)

        await self.db.commit()
        
        return await self.get_workflow(workflow.id)

    async def cancel_workflow(self, workflow_id: uuid.UUID, updater_id: uuid.UUID) -> Workflow:
        workflow = await self.get_workflow(workflow_id)
        if workflow.status in ("success", "failed", "cancelled"):
            raise BadRequestException("Cannot cancel a completed workflow.", "WORKFLOW_COMPLETED")

        # Cancel all pending or running jobs
        for job in workflow.jobs:
            if job.status not in ("success", "failed", "cancelled"):
                await self.job_service.cancel_job(job.id, updater_id)
        
        workflow.status = "cancelled"
        workflow.updated_by = updater_id
        await self.db.commit()
        return workflow

    async def retry_workflow(self, workflow_id: uuid.UUID, updater_id: uuid.UUID) -> Workflow:
        workflow = await self.get_workflow(workflow_id)
        if workflow.status == "success":
            raise BadRequestException("Cannot retry a successful workflow.", "WORKFLOW_SUCCESSFUL")

        # Replay failed jobs or cancelled jobs
        for job in workflow.jobs:
            if job.status in ("failed", "cancelled"):
                await self.job_service.replay_job(job.id)
                # Ensure the parent dependencies are handled correctly, replay_job sets status to "queued".
                # If a parent is still pending, this might need to be set to "created".
                if job.parent_id:
                    parent = await self.job_service.get_job(job.parent_id)
                    if parent.status != "success":
                        job.status = "created"
        
        workflow.status = "running"
        workflow.updated_by = updater_id
        await self.db.commit()
        return workflow

    async def check_and_update_workflow_status(self, workflow_id: uuid.UUID) -> None:
        """Evaluates if the workflow is complete and updates its status."""
        workflow = await self.get_workflow(workflow_id)
        
        all_success = True
        any_failed = False
        any_cancelled = False
        
        for job in workflow.jobs:
            if job.status == "failed":
                any_failed = True
            elif job.status == "cancelled":
                any_cancelled = True
            elif job.status != "success":
                all_success = False

        new_status = workflow.status
        if any_failed:
            new_status = "failed"
        elif any_cancelled:
            new_status = "cancelled"
        elif all_success:
            new_status = "success"

        if new_status != workflow.status:
            workflow.status = new_status
            await self.db.commit()
