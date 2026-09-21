import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import NotFoundException
from app.models.core import DeadLetterQueue, Job
from app.repositories.core import DeadLetterQueueRepository, JobRepository

class DLQService:
    """
    DLQService manages recovery, analysis, replay, and deletion of failed jobs
    that have exhausted all configured retry policies.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.dlq_repo = DeadLetterQueueRepository(db_session)
        self.job_repo = JobRepository(db_session)

    async def list_dlq_records(self, skip: int = 0, limit: int = 100) -> List[DeadLetterQueue]:
        """Fetch all dead-lettered jobs, including underlying Job payload details."""
        stmt = (
            select(DeadLetterQueue)
            .offset(skip)
            .limit(limit)
            .options(selectinload(DeadLetterQueue.job))
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_dlq_record(self, job_id: uuid.UUID) -> DeadLetterQueue:
        """Fetch a specific DLQ record by Job ID."""
        stmt = (
            select(DeadLetterQueue)
            .where(DeadLetterQueue.job_id == job_id)
            .options(selectinload(DeadLetterQueue.job))
        )
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            raise NotFoundException(message="Dead letter record not found.", code="DLQ_RECORD_NOT_FOUND")
        return record

    async def replay_job(self, job_id: uuid.UUID) -> Job:
        """Replay (re-enqueue) a dead-lettered job, resetting retry counters."""
        record = await self.get_dlq_record(job_id)
        job = record.job

        # Reset job state back to queued
        updated_job = await self.job_repo.update(
            job,
            {
                "status": "queued",
                "retries_count": 0,
                "run_at": datetime.now(timezone.utc),
                "error_message": None
            }
        )

        # Remove record from dead letter queue
        await self.dlq_repo.delete(record, soft=False) # Hard delete trace in DLQ
        return updated_job

    async def delete_job(self, job_id: uuid.UUID) -> None:
        """Completely remove a dead-lettered job from system queues."""
        record = await self.get_dlq_record(job_id)
        job = record.job

        # Remove DLQ trace and soft-delete job
        await self.dlq_repo.delete(record, soft=False)
        await self.job_repo.delete(job, soft=True)
