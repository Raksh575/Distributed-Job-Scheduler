from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base
from app.core.exceptions import AppException

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """
    Generic async Repository pattern class for database operations.
    Handles soft deletes and optimistic lock validation out-of-the-box.
    """

    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        self.model = model
        self.db = db_session

    async def get_by_id(self, id: Any, include_deleted: bool = False) -> Optional[ModelType]:
        """Fetch a single record by primary key id, filtering soft deletes unless specified."""
        entity = await self.db.get(self.model, id)
        if entity and not include_deleted and hasattr(entity, "deleted_at") and entity.deleted_at is not None:
            return None
        return entity

    async def get_all(self, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> List[ModelType]:
        """Fetch paginated lists of records, filtering soft deletes unless specified."""
        query = select(self.model)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at == None)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, entity: ModelType) -> ModelType:
        """Persist a new entity instance."""
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def update(self, entity: ModelType, update_data: Dict[str, Any]) -> ModelType:
        """
        Update fields of an existing entity instance.
        Validates optimistic locking version checks to prevent overwrite conflicts.
        """
        # Validate version mismatch if table implements optimistic locking
        if hasattr(entity, "version") and hasattr(entity, "id") and entity.id is not None:
            current_version = getattr(entity, "version")
            
            # Fetch active version from database context
            db_version_query = select(self.model.version).where(self.model.id == entity.id)
            result = await self.db.execute(db_version_query)
            db_version = result.scalar_one_or_none()
            
            if db_version is not None and db_version != current_version:
                raise AppException(
                    message="Optimistic locking conflict: The resource was modified by another transaction.",
                    code="CONFLICT",
                    status_code=409
                )
            
            # Increment version safely
            setattr(entity, "version", current_version + 1)

        # Apply updates
        for field, value in update_data.items():
            if hasattr(entity, field):
                setattr(entity, field, value)
                
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def delete(self, entity: ModelType, soft: bool = True) -> None:
        """Remove a record from database context (triggers soft-delete if supported)."""
        if soft and hasattr(entity, "deleted_at"):
            setattr(entity, "deleted_at", datetime.now(timezone.utc))
            self.db.add(entity)
        else:
            await self.db.delete(entity)
        await self.db.flush()
