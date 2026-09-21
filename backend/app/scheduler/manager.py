import logging
from typing import Any, Callable, Dict, List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.core.config import settings

logger = logging.getLogger("app.scheduler")

class SchedulerManager:
    """
    Manages the lifecycle and job scheduling of the APScheduler.
    Uses SQLAlchemy connection backend to persist schedule details.
    """

    def __init__(self):
        # Configure job stores to persist schedulers if database_url is provided
        # For simplicity in testing/dev, use in-memory store if needed, or fallback.
        # Here we configure SQLAlchemyJobStore using database sync url equivalent or in-memory
        # Because we're using asyncpg, SQLAlchemyJobStore (which uses traditional DBAPIs)
        # requires a sync driver (psycopg2) or we can default to memory for local dev.
        # Let's use memory jobstore by default for simplicity, allow expansion.
        jobstores = {
            "default": SQLAlchemyJobStore(url=settings.DATABASE_URL.replace("+asyncpg", ""))
        } if not settings.DATABASE_URL.startswith("sqlite") and "+asyncpg" in settings.DATABASE_URL else {}

        self.scheduler = AsyncIOScheduler(jobstores=jobstores)

    async def start(self) -> None:
        """Initialize and start scheduler engine."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler manager started successfully.")

    async def shutdown(self) -> None:
        """Stop scheduler engine and wait for running tasks."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler manager shut down successfully.")

    def add_scheduled_job(
        self,
        func: Callable[..., Any],
        trigger: str,
        job_id: str,
        trigger_args: Dict[str, Any],
        replace_existing: bool = True
    ) -> None:
        """
        Add a job to the scheduler.
        trigger: 'cron', 'interval', or 'date'
        """
        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            replace_existing=replace_existing,
            **trigger_args
        )
        logger.info(f"Scheduled job added: ID={job_id}, trigger={trigger}")

    def remove_scheduled_job(self, job_id: str) -> None:
        """Cancel a scheduled job by its unique ID."""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Scheduled job removed: ID={job_id}")
        except Exception as e:
            logger.error(f"Failed to remove scheduled job {job_id}: {str(e)}")

    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Retrieve list of currently registered jobs."""
        jobs = self.scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                "pending": job.pending
            }
            for job in jobs
        ]

# Global singleton instance
scheduler_manager = SchedulerManager()
