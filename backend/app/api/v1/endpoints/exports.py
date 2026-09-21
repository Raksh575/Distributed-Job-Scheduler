import csv
import io
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.middleware.auth import RequirePermission
from app.models.core import Queue, Worker, Job, JobExecution

router = APIRouter()

@router.get("/{org_id}/exports/queues", dependencies=[Depends(RequirePermission("metrics_access"))])
async def export_queues_report(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Generate a downloadable CSV report summarizing queue sizes, latency, and status."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["Queue ID", "Queue Name", "Active Status", "Pending Jobs Count", "Created At"])
    
    # Query all queues in project
    stmt = select(Queue).where(Queue.deleted_at == None)
    res = await db.execute(stmt)
    queues = res.scalars().all()
    
    for q in queues:
        # Count jobs
        job_count_res = await db.execute(
            select(func.count(Job.id)).where(Job.queue_id == q.id, Job.deleted_at == None)
        )
        job_count = job_count_res.scalar() or 0
        
        writer.writerow([
            str(q.id),
            q.name,
            "Active" if q.is_active else "Paused",
            job_count,
            q.created_at.isoformat()
        ])
        
    output.seek(0)
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=djs_queues_telemetry.csv"
    return response


@router.get("/{org_id}/exports/workers", dependencies=[Depends(RequirePermission("metrics_access"))])
async def export_workers_report(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Generate a downloadable CSV report summarizing worker health and assignment allocations."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["Worker ID", "Name", "Status", "Last Heartbeat", "Created At"])
    
    stmt = select(Worker).where(Worker.deleted_at == None)
    res = await db.execute(stmt)
    workers = res.scalars().all()
    
    for w in workers:
        writer.writerow([
            str(w.id),
            w.name,
            w.status,
            w.last_heartbeat.isoformat(),
            w.created_at.isoformat()
        ])
        
    output.seek(0)
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=djs_workers_telemetry.csv"
    return response


@router.get("/{org_id}/exports/executions", dependencies=[Depends(RequirePermission("metrics_access"))])
async def export_executions_report(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Generate a downloadable CSV report outlining historic job execution runtimes."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["Execution ID", "Job ID", "Job Name", "Worker ID", "Status", "Duration (ms)", "Started At", "Completed At"])
    
    stmt = select(JobExecution).join(Job).where(JobExecution.deleted_at == None).order_by(JobExecution.started_at.desc()).limit(1000)
    res = await db.execute(stmt)
    executions = res.scalars().all()
    
    for e in executions:
        # Fetch job name
        job_stmt = select(Job.name).where(Job.id == e.job_id)
        job_res = await db.execute(job_stmt)
        job_name = job_res.scalar() or "Unknown"
        
        writer.writerow([
            str(e.id),
            str(e.job_id),
            job_name,
            str(e.worker_id) if e.worker_id else "None",
            e.status,
            e.duration_ms or 0,
            e.started_at.isoformat(),
            e.completed_at.isoformat() if e.completed_at else "In Progress"
        ])
        
    output.seek(0)
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=djs_executions_telemetry.csv"
    return response
