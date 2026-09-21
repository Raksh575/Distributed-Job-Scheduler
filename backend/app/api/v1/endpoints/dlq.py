import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.middleware.auth import get_current_user, RequirePermission
from app.schemas.dto import DLQRecordResponse, JobResponse
from app.services.dlq_service import DLQService

router = APIRouter()

@router.get("/{org_id}/dlq", response_model=List[DLQRecordResponse], dependencies=[Depends(RequirePermission("metrics_access"))])
async def list_dead_letter_jobs(
    org_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve all jobs parked inside the Dead Letter Queue."""
    dlq_service = DLQService(db)
    return await dlq_service.list_dlq_records(skip=skip, limit=limit)


@router.post("/{org_id}/dlq/{job_id}/replay", response_model=JobResponse, dependencies=[Depends(RequirePermission("job_management"))])
async def replay_dead_letter_job(
    org_id: uuid.UUID,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Force replay and re-enqueue a failed job, clearing previous error status."""
    dlq_service = DLQService(db)
    job = await dlq_service.replay_job(job_id)
    await db.commit()
    return job


@router.delete("/{org_id}/dlq/{job_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RequirePermission("job_management"))])
async def delete_dead_letter_job(
    org_id: uuid.UUID,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Purge and soft-delete a job record from the Dead Letter Queue logs."""
    dlq_service = DLQService(db)
    await dlq_service.delete_job(job_id)
    await db.commit()
