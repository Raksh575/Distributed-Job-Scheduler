import uuid
from typing import Dict, List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.core import Queue, Job
from app.repositories.core import QueueRepository, ProjectRepository

class QueueService:
    """
    QueueService coordinates configurations and runtime metadata for individual queues.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.queue_repo = QueueRepository(db_session)
        self.project_repo = ProjectRepository(db_session)

    async def create_queue(self, project_id: uuid.UUID, creator_id: uuid.UUID, queue_in) -> Queue:
        """Create a new job queue inside a project workspace."""
        # Ensure project exists
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise NotFoundException(message="Project not found.", code="PROJECT_NOT_FOUND")

        # Check name uniqueness
        stmt = select(Queue).where(Queue.project_id == project_id, Queue.name == queue_in.name, Queue.deleted_at == None)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise BadRequestException(
                message=f"Queue '{queue_in.name}' already exists in this project.",
                code="QUEUE_NAME_EXISTS"
            )

        new_queue = Queue(
            project_id=project_id,
            name=queue_in.name,
            priority=queue_in.priority if queue_in.priority is not None else 0,
            concurrency_limit=queue_in.concurrency_limit if queue_in.concurrency_limit is not None else 10,
            rate_limit=queue_in.rate_limit,
            is_active=True,
            created_by=creator_id
        )
        return await self.queue_repo.create(new_queue)

    async def get_queue_by_id(self, queue_id: uuid.UUID) -> Queue:
        """Fetch queue, raising error if not found."""
        queue = await self.queue_repo.get_by_id(queue_id)
        if not queue:
            raise NotFoundException(message="Queue not found.", code="QUEUE_NOT_FOUND")
        return queue

    async def update_queue(self, queue_id: uuid.UUID, updater_id: uuid.UUID, name: str) -> Queue:
        """Update queue parameters."""
        queue = await self.get_queue_by_id(queue_id)
        return await self.queue_repo.update(queue, {"name": name, "updated_by": updater_id})

    async def pause_queue(self, queue_id: uuid.UUID, updater_id: uuid.UUID) -> Queue:
        """Pause job consumption on a queue."""
        queue = await self.get_queue_by_id(queue_id)
        return await self.queue_repo.update(queue, {"is_active": False, "updated_by": updater_id})

    async def resume_queue(self, queue_id: uuid.UUID, updater_id: uuid.UUID) -> Queue:
        """Resume job consumption on a queue."""
        queue = await self.get_queue_by_id(queue_id)
        return await self.queue_repo.update(queue, {"is_active": True, "updated_by": updater_id})

    async def delete_queue(self, queue_id: uuid.UUID) -> None:
        """Soft delete queue."""
        queue = await self.get_queue_by_id(queue_id)
        await self.queue_repo.delete(queue, soft=True)

    async def get_queue_statistics(self, queue_id: uuid.UUID) -> Dict[str, int]:
        """Aggregate real-time job counts in this queue by status."""
        # Ensure queue exists
        await self.get_queue_by_id(queue_id)

        stmt = (
            select(Job.status, func.count(Job.id))
            .where(Job.queue_id == queue_id, Job.deleted_at == None)
            .group_by(Job.status)
        )
        result = await self.db.execute(stmt)
        
        stats = {
            "queued": 0,
            "running": 0,
            "success": 0,
            "failed": 0,
            "cancelled": 0
        }
        for status_val, count in result.all():
            if status_val in stats:
                stats[status_val] = count
                
        return stats
