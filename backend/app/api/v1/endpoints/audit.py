import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.middleware.auth import RequirePermission
from app.models.core import AuditLog
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    action: str
    entity_type: str
    entity_id: Optional[uuid.UUID]
    changes: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/{org_id}/audit-logs", response_model=List[AuditLogResponse], dependencies=[Depends(RequirePermission("metrics_access"))])
async def list_audit_logs(
    org_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve audit trail logs of project configuration changes."""
    stmt = (
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())
