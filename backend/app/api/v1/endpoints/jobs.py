import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.middleware.auth import get_current_user, RequirePermission
from app.models.core import User, Job
from app.schemas.dto import JobCreate, JobResponse
from app.services.job_service import JobService

router = APIRouter()

@router.post("/{org_id}/queues/{queue_id}/jobs", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(RequirePermission("job_management"))])
async def submit_job(
    org_id: uuid.UUID,
    queue_id: uuid.UUID,
    job_in: JobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Submit a new background job to a specific queue."""
    job_service = JobService(db)
    return await job_service.submit_job(
        queue_id=queue_id,
        name=job_in.name,
        payload=job_in.payload,
        parent_id=job_in.parent_id,
        delay_seconds=job_in.delay_seconds,
        priority=job_in.priority,
        max_retries=job_in.max_retries,
        timeout=job_in.timeout,
        creator_id=current_user.id
    )


@router.get("/{org_id}/jobs/{job_id}", response_model=JobResponse, dependencies=[Depends(RequirePermission("metrics_access"))])
async def get_job_details(
    org_id: uuid.UUID,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve detailed state and progress metrics of a job."""
    job_service = JobService(db)
    return await job_service.get_job(job_id)


@router.post("/{org_id}/jobs/{job_id}/cancel", response_model=JobResponse, dependencies=[Depends(RequirePermission("job_management"))])
async def cancel_job(
    org_id: uuid.UUID,
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Cancel a queued or scheduled job execution."""
    job_service = JobService(db)
    return await job_service.cancel_job(job_id, current_user.id)


@router.get("/{org_id}/queues/{queue_id}/jobs", response_model=List[JobResponse], dependencies=[Depends(RequirePermission("metrics_access"))])
async def list_jobs_in_queue(
    org_id: uuid.UUID,
    queue_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """List jobs submitted to a queue with pagination filters."""
    stmt = (
        select(Job)
        .where(Job.queue_id == queue_id, Job.deleted_at == None)
        .order_by(Job.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/{org_id}/jobs/{job_id}/logs", dependencies=[Depends(RequirePermission("metrics_access"))])
async def get_job_logs(
    org_id: uuid.UUID,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Fetch all execution attempts and logs associated with a job."""
    from sqlalchemy.orm import selectinload
    from app.models.core import JobExecution
    
    stmt = (
        select(JobExecution)
        .where(JobExecution.job_id == job_id, JobExecution.deleted_at == None)
        .options(selectinload(JobExecution.logs))
        .order_by(JobExecution.started_at.desc())
    )
    res = await db.execute(stmt)
    executions = res.scalars().all()
    
    return [
        {
            "execution_id": str(e.id),
            "worker_id": str(e.worker_id) if e.worker_id else None,
            "status": e.status,
            "started_at": e.started_at.isoformat(),
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            "error_message": e.error_message,
            "duration_ms": e.duration_ms,
            "ai_analysis": e.ai_analysis,
            "logs": [
                {
                    "level": l.level,
                    "message": l.message,
                    "timestamp": l.timestamp.isoformat()
                }
                for l in e.logs
            ]
        }
        for e in executions
    ]
