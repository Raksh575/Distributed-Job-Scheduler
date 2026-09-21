import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.middleware.auth import get_current_user, RequirePermission
from app.models.core import User, ScheduledJob
from app.schemas.dto import ScheduledJobCreate, ScheduledJobResponse
from app.scheduler.orchestrator import scheduler_orchestrator
from app.repositories.core import ScheduledJobRepository

router = APIRouter()

@router.post("/{org_id}/projects/{project_id}/schedules", response_model=ScheduledJobResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RequirePermission("queue_management"))])
async def create_schedule(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    schedule_in: ScheduledJobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new cron/interval scheduled trigger policy."""
    sched_repo = ScheduledJobRepository(db)
    
    new_schedule = ScheduledJob(
        project_id=project_id,
        name=schedule_in.name,
        trigger_type=schedule_in.trigger_type,
        cron_expression=schedule_in.cron_expression,
        interval_seconds=schedule_in.interval_seconds,
        target_queue_id=schedule_in.target_queue_id,
        job_name=schedule_in.job_name,
        job_payload=schedule_in.job_payload,
        is_active=True,
        created_by=current_user.id
    )
    schedule = await sched_repo.create(new_schedule)
    await db.commit()
    
    # Sync with running APScheduler instance
    await scheduler_orchestrator.sync_database_triggers()
    return schedule


@router.get("/{org_id}/projects/{project_id}/schedules", response_model=List[ScheduledJobResponse], dependencies=[Depends(RequirePermission("metrics_access"))])
async def list_schedules(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """List scheduled jobs registered under a project."""
    stmt = select(ScheduledJob).where(ScheduledJob.project_id == project_id, ScheduledJob.deleted_at == None)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post("/{org_id}/schedules/{schedule_id}/pause", response_model=ScheduledJobResponse, dependencies=[Depends(RequirePermission("queue_management"))])
async def pause_schedule(
    org_id: uuid.UUID,
    schedule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Pause a schedule trigger."""
    sched_repo = ScheduledJobRepository(db)
    schedule = await sched_repo.get_by_id(schedule_id)
    if not schedule:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Schedule not found.")
        
    updated = await sched_repo.update(schedule, {"is_active": False, "updated_by": current_user.id})
    await db.commit()
    
    # Sync triggers
    await scheduler_orchestrator.sync_database_triggers()
    return updated


@router.post("/{org_id}/schedules/{schedule_id}/resume", response_model=ScheduledJobResponse, dependencies=[Depends(RequirePermission("queue_management"))])
async def resume_schedule(
    org_id: uuid.UUID,
    schedule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Resume a paused schedule trigger."""
    sched_repo = ScheduledJobRepository(db)
    schedule = await sched_repo.get_by_id(schedule_id)
    if not schedule:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Schedule not found.")
        
    updated = await sched_repo.update(schedule, {"is_active": True, "updated_by": current_user.id})
    await db.commit()
    
    # Sync triggers
    await scheduler_orchestrator.sync_database_triggers()
    return updated


@router.delete("/{org_id}/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RequirePermission("queue_management"))])
async def delete_schedule(
    org_id: uuid.UUID,
    schedule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a scheduled cron task."""
    sched_repo = ScheduledJobRepository(db)
    schedule = await sched_repo.get_by_id(schedule_id)
    if not schedule:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Schedule not found.")
        
    await sched_repo.delete(schedule, soft=True)
    await db.commit()
    
    # Sync triggers
    await scheduler_orchestrator.sync_database_triggers()
