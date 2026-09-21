import asyncio
import importlib
import logging
import os
import psutil
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionFactory
from app.models.core import Worker, WorkerHeartbeat, Job, JobLog
from app.services.job_service import JobService
from app.workers.base import BaseWorker

logger = logging.getLogger("app.worker.runner")

# Example tasks dictionary for dynamic registration (can also be loaded dynamically)
REGISTERED_TASKS = {
    "system_cleanup": "app.tasks.system.run_cleanup",
    "send_email": "app.tasks.communication.dispatch_email",
    "generate_reports": "app.tasks.analytics.compile_report",
}

class WorkerRunner(BaseWorker):
    """
    WorkerRunner implements concurrent task consumption, atomic claiming,
    dynamic task function executions, and diagnostic telemetry reporting.
    """

    def __init__(self, worker_name: str, queue_name: str, concurrency_limit: int = 10):
        # We generate a unique UUID for internal DB tracking
        self.db_worker_id: Optional[uuid.UUID] = None
        self.worker_name = worker_name
        self.concurrency_limit = concurrency_limit
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.active_tasks_count = 0
        
        super().__init__(worker_id=worker_name, queue_name=queue_name)

    async def start(self) -> None:
        """Startup sequence: register node, run heartbeat daemon, and initiate worker poll loop."""
        # 1. Register worker in DB
        await self._register_worker()
        
        # 2. Spawn background heartbeat loop
        self._heartbeat_task = asyncio.create_task(self._run_heartbeat_loop())
        
        # 3. Call start on base worker (starts worker loop)
        await super().start()

    async def shutdown(self) -> None:
        """Gracefully shut down: stop loop, cancel heartbeat, and update DB status."""
        logger.info("Graceful shutdown initiated...")
        self._running = False
        
        # Cancel heartbeat loop
        if hasattr(self, "_heartbeat_task"):
            self._heartbeat_task.cancel()
            
        # Update status in DB
        if self.db_worker_id:
            async with AsyncSessionFactory() as session:
                async with session.begin():
                    stmt = (
                        update(Worker)
                        .where(Worker.id == self.db_worker_id)
                        .values(status="offline", last_heartbeat=datetime.now(timezone.utc))
                    )
                    await session.execute(stmt)
                    
        logger.info("Worker runner stopped successfully.")

    async def _register_worker(self) -> None:
        """Create a Worker record in the database."""
        async with AsyncSessionFactory() as session:
            async with session.begin():
                # Check if worker name already exists
                stmt = select(Worker).where(Worker.name == self.worker_name)
                res = await session.execute(stmt)
                db_worker = res.scalar_one_or_none()
                
                system_info = {
                    "cpu_count": psutil.cpu_count(),
                    "total_memory_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
                    "os": os.name
                }
                
                if db_worker:
                    db_worker.status = "idle"
                    db_worker.last_heartbeat = datetime.now(timezone.utc)
                    db_worker.system_info = system_info
                    db_worker.deleted_at = None  # Un-delete if previously soft deleted
                else:
                    db_worker = Worker(
                        name=self.worker_name,
                        status="idle",
                        system_info=system_info
                    )
                    session.add(db_worker)
                
                await session.flush()
                self.db_worker_id = db_worker.id
                logger.info(f"Worker registered in database with ID: {self.db_worker_id}")

    async def _run_heartbeat_loop(self) -> None:
        """Periodic background task that logs status and CPU/RAM usage to DB."""
        while self._running:
            try:
                await asyncio.sleep(10)
                if not self.db_worker_id:
                    continue

                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory().percent
                
                async with AsyncSessionFactory() as session:
                    async with session.begin():
                        # 1. Update Worker table heartbeat timestamp and status
                        status = "active" if self.active_tasks_count > 0 else "idle"
                        stmt = (
                            update(Worker)
                            .where(Worker.id == self.db_worker_id)
                            .values(status=status, last_heartbeat=datetime.now(timezone.utc))
                        )
                        await session.execute(stmt)
                        
                        # 2. Write telemetry to WorkerHeartbeats
                        heartbeat = WorkerHeartbeat(
                            worker_id=self.db_worker_id,
                            status=status,
                            cpu_usage=cpu,
                            memory_usage=ram,
                            active_jobs_count=self.active_tasks_count
                        )
                        session.add(heartbeat)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop exception: {str(e)}")

    async def _fetch_next_job(self) -> Optional[Dict[str, Any]]:
        """Polled loop fetch: locks next job using SELECT FOR UPDATE SKIP LOCKED."""
        if self.active_tasks_count >= self.concurrency_limit:
            # We are saturated. Pause fetching.
            await asyncio.sleep(0.5)
            return None

        async with AsyncSessionFactory() as session:
            # Resolve queue name to queue ID
            stmt = select(Queue.id).where(Queue.name == self.queue_name, Queue.deleted_at == None)
            res = await session.execute(stmt)
            queue_id = res.scalar_one_or_none()
            if not queue_id:
                logger.warning(f"Queue '{self.queue_name}' not found in database. Retrying in 5s...")
                await asyncio.sleep(5)
                return None

            job_service = JobService(session)
            # Claim next job under a database transaction
            job = await job_service.claim_next_job(
                worker_id=self.db_worker_id,
                allowed_queue_ids=[queue_id]
            )
            
            if job:
                # Commit changes (status set to claimed, JobExecution created)
                await session.commit()
                # Return standard dict format for the loop processor
                return {
                    "id": job.id,
                    "name": job.name,
                    "payload": job.payload
                }
            return None

    async def _process_job(self, job: Dict[str, Any]) -> None:
        """Spawn background task execution inside the semaphore count."""
        # We trigger this concurrently. We don't block the polling loop.
        asyncio.create_task(self._execute_task_bounded(job))

    async def _execute_task_bounded(self, job: Dict[str, Any]) -> None:
        """Executes task inside the Semaphore rate limiter, updating DB state on exit."""
        async with self.semaphore:
            self.active_tasks_count += 1
            start_time = time.perf_counter()
            job_id = job["id"]
            
            logger.info(f"Worker executing job {job_id} ({job['name']})...")
            
            status = "success"
            result = None
            error_message = None
            
            try:
                # 1. Update status to 'running'
                async with AsyncSessionFactory() as session:
                    async with session.begin():
                        job_service = JobService(session)
                        db_job = await job_service.get_job(job_id)
                        await job_service.job_repo.update(db_job, {"status": "running"})
                
                # 2. Dynamic execution of task logic
                result = await self._execute_task_logic(job["name"], job["payload"])
                
            except Exception as e:
                status = "failed"
                error_message = f"{type(e).__name__}: {str(e)}"
                logger.error(f"Job {job_id} failed: {error_message}")
                
                # Log execution error trace to JobLogs
                await self._log_to_db(job_id, "error", f"Task execution threw exception:\n{traceback.format_exc()}")
                
            finally:
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                self.active_tasks_count -= 1
                
                # 3. Transition Job state to completed / retry / DLQ
                async with AsyncSessionFactory() as session:
                    async with session.begin():
                        job_service = JobService(session)
                        await job_service.finish_job(
                            job_id=job_id,
                            worker_id=self.db_worker_id,
                            status=status,
                            result=result,
                            error_message=error_message,
                            duration_ms=duration_ms
                        )

    async def _execute_task_logic(self, task_name: str, payload: Dict[str, Any]) -> Any:
        """Dynamically load and execute the target task function based on name mappings."""
        task_path = REGISTERED_TASKS.get(task_name)
        if not task_path:
            # Fallback mock task runner if task is not dynamically registered
            # (Allows testing scheduler flows without hard dependencies)
            logger.info(f"Task path for '{task_name}' not registered. Simulating execution...")
            await asyncio.sleep(2.0)
            return {"status": "mock_completed", "input_received": payload}

        # Dynamic import
        path_parts = task_path.split(".")
        module_name = ".".join(path_parts[:-1])
        func_name = path_parts[-1]
        
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)
        
        if asyncio.iscoroutinefunction(func):
            return await func(payload)
        else:
            return func(payload)

    async def _log_to_db(self, job_id: uuid.UUID, level: str, message: str) -> None:
        """Create a JobLog database record linked to the active JobExecution."""
        try:
            async with AsyncSessionFactory() as session:
                async with session.begin():
                    # Find active execution
                    from app.models.core import JobExecution
                    stmt = (
                        select(JobExecution.id)
                        .where(JobExecution.job_id == job_id, JobExecution.completed_at == None)
                        .order_by(JobExecution.started_at.desc())
                        .limit(1)
                    )
                    res = await session.execute(stmt)
                    exec_id = res.scalar_one_or_none()
                    
                    if exec_id:
                        log_record = JobLog(
                            job_execution_id=exec_id,
                            job_id=job_id,
                            level=level,
                            message=message,
                            timestamp=datetime.now(timezone.utc)
                        )
                        session.add(log_record)
        except Exception as e:
            logger.error(f"Failed to log task output to database: {str(e)}")

if __name__ == "__main__":
    setup_logger = logging.getLogger()
    setup_logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    setup_logger.addHandler(ch)

    worker_name = os.getenv("WORKER_NAME", f"worker-node-{uuid.uuid4().hex[:6]}")
    queue_name = os.getenv("QUEUE_NAME", "default-task-queue")
    concurrency = int(os.getenv("WORKER_CONCURRENCY", "5"))
    
    runner = WorkerRunner(
        worker_name=worker_name,
        queue_name=queue_name,
        concurrency_limit=concurrency
    )
    
    logger.info(f"Starting WorkerRunner: name={worker_name}, queue={queue_name}, concurrency={concurrency}")
    try:
        asyncio.run(runner.start())
    except KeyboardInterrupt:
        logger.info("WorkerRunner shutdown complete.")
