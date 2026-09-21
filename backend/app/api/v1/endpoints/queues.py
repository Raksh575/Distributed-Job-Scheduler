import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.middleware.auth import get_current_user, RequirePermission
from app.models.core import User, Queue
from app.schemas.dto import QueueCreate, QueueResponse
from app.services.queue_service import QueueService

router = APIRouter()

@router.post("/{org_id}/projects/{project_id}/queues", response_model=QueueResponse, dependencies=[Depends(RequirePermission("queue_management"))])
async def create_queue(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    queue_in: QueueCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new job processing queue under a project."""
    queue_service = QueueService(db)
    return await queue_service.create_queue(
        project_id=project_id,
        creator_id=current_user.id,
        queue_in=queue_in
    )


@router.get("/{org_id}/projects/{project_id}/queues", response_model=List[QueueResponse], dependencies=[Depends(RequirePermission("metrics_access"))])
async def list_queues(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """List all active queues under a project."""
    stmt = select(Queue).where(Queue.project_id == project_id, Queue.deleted_at == None)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/{org_id}/queues/{queue_id}/stats", dependencies=[Depends(RequirePermission("metrics_access"))])
async def get_queue_stats(
    org_id: uuid.UUID,
    queue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Get active, queued, succeeded, and failed count for a queue."""
    queue_service = QueueService(db)
    return await queue_service.get_queue_statistics(queue_id)


@router.post("/{org_id}/queues/{queue_id}/pause", response_model=QueueResponse, dependencies=[Depends(RequirePermission("queue_management"))])
async def pause_queue(
    org_id: uuid.UUID,
    queue_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Pause job consumption on a queue."""
    queue_service = QueueService(db)
    return await queue_service.pause_queue(queue_id, current_user.id)


@router.post("/{org_id}/queues/{queue_id}/resume", response_model=QueueResponse, dependencies=[Depends(RequirePermission("queue_management"))])
async def resume_queue(
    org_id: uuid.UUID,
    queue_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Resume job consumption on a queue."""
    queue_service = QueueService(db)
    return await queue_service.resume_queue(queue_id, current_user.id)


@router.delete("/{org_id}/queues/{queue_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RequirePermission("queue_management"))])
async def delete_queue(
    org_id: uuid.UUID,
    queue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Soft delete a queue."""
    queue_service = QueueService(db)
    await queue_service.delete_queue(queue_id)
