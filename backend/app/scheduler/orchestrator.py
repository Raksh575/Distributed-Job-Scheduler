import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Set
from sqlalchemy import select, update
from app.db.database import AsyncSessionFactory
from app.models.core import ScheduledJob, Job, Worker
from app.services.job_service import JobService
from app.scheduler.manager import scheduler_manager

logger = logging.getLogger("app.scheduler.orchestrator")

class SchedulerOrchestrator:
    """
    SchedulerOrchestrator syncs scheduled jobs in the database to active APScheduler triggers.
    Runs worker heartbeats recovery sweep tasks.
    """

    def __init__(self):
        # Keep track of active registered job IDs in memory to detect edits/removals
        self.active_trigger_ids: Set[str] = set()

    async def sync_database_triggers(self) -> None:
        """Poll the ScheduledJob table and sync active triggers with APScheduler."""
        logger.info("Synchronizing scheduled database jobs with APScheduler...")
        
        async with AsyncSessionFactory() as session:
            async with session.begin():
                # Fetch all active scheduled jobs
                stmt = select(ScheduledJob).where(ScheduledJob.is_active == True, ScheduledJob.deleted_at == None)
                result = await session.execute(stmt)
                db_schedules = result.scalars().all()

                db_schedule_ids = {str(s.id) for s in db_schedules}

                # 1. Remove jobs in APScheduler that are no longer active in DB
                for active_id in list(self.active_trigger_ids):
                    if active_id not in db_schedule_ids:
                        scheduler_manager.remove_scheduled_job(active_id)
                        self.active_trigger_ids.remove(active_id)

                # 2. Add or update active schedules
                for schedule in db_schedules:
                    sched_id_str = str(schedule.id)
                    
                    # Compute trigger settings
                    trigger_args = {}
                    if schedule.trigger_type == "cron":
                        trigger_args = {"expression": schedule.cron_expression} # e.g. "*/10 * * * *"
                        # APScheduler cron parameter mapping
                        # Standard cron expression: 'min hour day month day_of_week'
                        # For simplicity, parse basic string and pass as cron parameters,
                        # or parse standard 5-part cron strings.
                        # Standard cron parser:
                        parts = schedule.cron_expression.split()
                        if len(parts) == 5:
                            trigger_args = {
                                "minute": parts[0],
                                "hour": parts[1],
                                "day": parts[2],
                                "month": parts[3],
                                "day_of_week": parts[4]
                            }
                    elif schedule.trigger_type == "interval":
                        trigger_args = {"seconds": schedule.interval_seconds}
                    else:
                        logger.error(f"Unknown trigger type: {schedule.trigger_type} for schedule {schedule.id}")
                        continue

                    # Define callback
                    def make_callback(sid: uuid.UUID):
                        return lambda: asyncio.create_task(self.trigger_scheduled_job(sid))

                    # Register with manager
                    # Using trigger names cron or interval
                    trigger_type = "cron" if schedule.trigger_type == "cron" else "interval"
                    
                    try:
                        scheduler_manager.add_scheduled_job(
                            func=make_callback(schedule.id),
                            trigger=trigger_type,
                            job_id=sched_id_str,
                            trigger_args=trigger_args,
                            replace_existing=True
                        )
                        self.active_trigger_ids.add(sched_id_str)
                        
                        # Update next execution time in DB
                        apsched_job = scheduler_manager.scheduler.get_job(sched_id_str)
                        if apsched_job and apsched_job.next_run_time:
                            schedule.next_run_time = apsched_job.next_run_time.astimezone(timezone.utc)
                            
                    except Exception as e:
                        logger.error(f"Failed to register database schedule {schedule.id}: {str(e)}")

    async def trigger_scheduled_job(self, schedule_id: uuid.UUID) -> None:
        """Fired callback by APScheduler: spawns a concrete Job record in the target queue."""
        logger.info(f"Triggering scheduled job: {schedule_id}")
        async with AsyncSessionFactory() as session:
            async with session.begin():
                # Load scheduled configuration
                stmt = select(ScheduledJob).where(ScheduledJob.id == schedule_id, ScheduledJob.is_active == True, ScheduledJob.deleted_at == None)
                res = await session.execute(stmt)
                schedule = res.scalar_one_or_none()
                
                if not schedule:
                    logger.warning(f"Fired schedule {schedule_id} was not found or is inactive.")
                    return

                # Submit the new job
                job_service = JobService(session)
                job = await job_service.submit_job(
                    queue_id=schedule.target_queue_id,
                    name=schedule.job_name,
                    payload=schedule.job_payload,
                    creator_id=schedule.created_by
                )
                
                # Fetch next run time from APScheduler to keep DB accurate
                sched_id_str = str(schedule_id)
                apsched_job = scheduler_manager.scheduler.get_job(sched_id_str)
                if apsched_job and apsched_job.next_run_time:
                    schedule.next_run_time = apsched_job.next_run_time.astimezone(timezone.utc)
                
                logger.info(f"Scheduled job {schedule_id} successfully created concrete job instance {job.id}")

    async def recover_crashed_workers(self) -> None:
        """Find offline/dead worker instances and recover any running jobs they claimed."""
        logger.info("Running crashed worker recovery sweep...")
        now = datetime.now(timezone.utc)
        heartbeat_timeout = now - timedelta(seconds=30)
        
        async with AsyncSessionFactory() as session:
            async with session.begin():
                # 1. Fetch active workers whose heartbeat is older than timeout limits
                stmt = select(Worker).where(
                    Worker.status != "offline",
                    Worker.last_heartbeat < heartbeat_timeout,
                    Worker.deleted_at == None
                )
                res = await session.execute(stmt)
                dead_workers = res.scalars().all()
                
                if not dead_workers:
                    return

                dead_worker_ids = [w.id for w in dead_workers]
                logger.warning(f"Found {len(dead_workers)} workers missing heartbeats. Flagging as offline: {dead_worker_ids}")

                # 2. Flag them as offline in DB
                for worker in dead_workers:
                    worker.status = "offline"

                # 3. Find any jobs in status 'claimed' or 'running' owned by these dead workers
                # Reset them back to 'queued' state for re-execution
                job_stmt = select(Job).where(
                    Job.status.in_(["claimed", "running"]),
                    Job.deleted_at == None
                )
                job_res = await session.execute(job_stmt)
                jobs = job_res.scalars().all()

                recovered_count = 0
                for job in jobs:
                    # Check if the job's last execution was owned by one of the dead workers
                    from app.models.core import JobExecution
                    exec_stmt = (
                        select(JobExecution.worker_id)
                        .where(JobExecution.job_id == job.id)
                        .order_by(JobExecution.started_at.desc())
                        .limit(1)
                    )
                    exec_res = await session.execute(exec_stmt)
                    worker_id = exec_res.scalar_one_or_none()
                    
                    if worker_id in dead_worker_ids:
                        logger.info(f"Recovering job {job.id} owned by crashed worker {worker_id}. Re-queuing...")
                        job.status = "queued"
                        job.error_message = f"Recovered from offline worker node {worker_id}."
                        recovered_count += 1
                        
                logger.info(f"Crashed worker recovery complete. Recovered {recovered_count} jobs.")

# Global singleton orchestrator
scheduler_orchestrator = SchedulerOrchestrator()
