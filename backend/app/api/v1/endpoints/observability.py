import psutil
import uuid
import time
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.middleware.auth import RequirePermission
from app.models.core import Worker, Queue, Job, JobExecution, WorkerHeartbeat
from app.services.log_reader import LogReaderService

router = APIRouter()

# Record startup time to calculate uptime
STARTUP_TIME = time.time()

@router.get("/{org_id}/observability/metrics", dependencies=[Depends(RequirePermission("metrics_access"))])
async def get_observability_metrics(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve complete real-time cluster metrics, queue analytics, and worker diagnostics."""
    from app.services.metrics_service import MetricsService
    metrics_service = MetricsService(db)
    return await metrics_service.get_observability_metrics(org_id)


@router.get("/{org_id}/observability/logs", dependencies=[Depends(RequirePermission("metrics_access"))])
async def search_observability_logs(
    org_id: uuid.UUID,
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    search_query: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    """Query, search, and paginate JSON-structured system logs."""
    reader = LogReaderService()
    logs, total = reader.read_logs(
        category=category,
        level=level,
        search_query=search_query,
        skip=skip,
        limit=limit
    )
    return {
        "logs": logs,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{org_id}/observability/logs/download", dependencies=[Depends(RequirePermission("metrics_access"))])
async def download_observability_logs(
    org_id: uuid.UUID,
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    search_query: Optional[str] = Query(None)
):
    """Stream formatted application logs as a downloadable file attachment."""
    reader = LogReaderService()
    stream = reader.generate_download_stream(
        category=category,
        level=level,
        search_query=search_query
    )
    headers = {
        "Content-Disposition": f"attachment; filename=djs_observability_logs_{int(time.time())}.log"
    }
    return StreamingResponse(stream, media_type="text/plain", headers=headers)
