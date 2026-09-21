import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.middleware.auth import RequirePermission
from app.services.metrics_service import MetricsService

router = APIRouter()

@router.get("/{org_id}/dashboard-metrics", dependencies=[Depends(RequirePermission("metrics_access"))])
async def get_dashboard_metrics(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve aggregate cluster stats, worker allocations, and throughput rates."""
    metrics_service = MetricsService(db)
    return await metrics_service.get_dashboard_metrics()


@router.get("/{org_id}/queues-telemetry", dependencies=[Depends(RequirePermission("metrics_access"))])
async def get_queues_telemetry(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve queue-specific job lengths and active running counts."""
    metrics_service = MetricsService(db)
    return await metrics_service.get_queue_telemetries()
