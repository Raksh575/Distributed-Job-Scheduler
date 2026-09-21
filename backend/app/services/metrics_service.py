import uuid
import time
import psutil
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.core import Job, Worker, Queue, JobExecution, WorkerHeartbeat

STARTUP_TIME = time.time()

class MetricsService:
    """
    MetricsService aggregates database records to expose dashboard metrics,
    throughput levels, and cluster performance statistics.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Aggregate high-level overview metrics of the active scheduler cluster."""
        now = datetime.now(timezone.utc)
        past_24h = now - timedelta(hours=24)

        # 1. Total active queues count
        queues_stmt = select(func.count(Queue.id)).where(Queue.deleted_at == None)
        queues_res = await self.db.execute(queues_stmt)
        total_queues = queues_res.scalar() or 0

        # 2. Total active workers count
        workers_stmt = select(func.count(Worker.id)).where(Worker.status != "offline", Worker.deleted_at == None)
        workers_res = await self.db.execute(workers_stmt)
        total_workers = workers_res.scalar() or 0

        # 3. Overall Job status counts (total)
        status_stmt = (
            select(Job.status, func.count(Job.id))
            .where(Job.deleted_at == None)
            .group_by(Job.status)
        )
        status_res = await self.db.execute(status_stmt)
        job_counts = {"queued": 0, "running": 0, "success": 0, "failed": 0, "cancelled": 0}
        for status_val, count in status_res.all():
            if status_val in job_counts:
                job_counts[status_val] = count

        # 4. Average execution duration (24h)
        duration_stmt = (
            select(func.avg(JobExecution.duration_ms))
            .where(
                JobExecution.status == "success",
                JobExecution.completed_at >= past_24h,
                JobExecution.deleted_at == None
            )
        )
        duration_res = await self.db.execute(duration_stmt)
        avg_duration = float(duration_res.scalar() or 0.0)

        # 5. Success / Failure Rates (24h)
        rates_stmt = (
            select(JobExecution.status, func.count(JobExecution.id))
            .where(JobExecution.completed_at >= past_24h, JobExecution.deleted_at == None)
            .group_by(JobExecution.status)
        )
        rates_res = await self.db.execute(rates_stmt)
        rates = {"success": 0, "failed": 0}
        for status_val, count in rates_res.all():
            if status_val in rates:
                rates[status_val] = count

        total_completed = rates["success"] + rates["failed"]
        success_rate = (rates["success"] / total_completed * 100) if total_completed > 0 else 100.0

        return {
            "queues_count": total_queues,
            "workers_count": total_workers,
            "jobs": job_counts,
            "throughput_24h": total_completed,
            "success_rate_24h": round(success_rate, 2),
            "avg_execution_ms": round(avg_duration, 2)
        }

    async def get_queue_telemetries(self) -> List[Dict[str, Any]]:
        """Fetch length and details of active queues."""
        stmt = (
            select(
                Queue.id,
                Queue.name,
                Queue.is_active,
                func.count(Job.id).filter(Job.status == "queued").label("queued_count"),
                func.count(Job.id).filter(Job.status == "running").label("running_count")
            )
            .outerjoin(Job, and_(Job.queue_id == Queue.id, Job.deleted_at == None))
            .where(Queue.deleted_at == None)
            .group_by(Queue.id, Queue.name, Queue.is_active)
        )
        result = await self.db.execute(stmt)
        
        telemetries = []
        for row in result.all():
            telemetries.append({
                "queue_id": str(row.id),
                "name": row.name,
                "is_active": row.is_active,
                "queued_jobs": row.queued_count,
                "running_jobs": row.running_count
            })
        return telemetries

    async def get_observability_metrics(self, org_id: uuid.UUID) -> Dict[str, Any]:
        """Retrieve complete real-time cluster metrics, queue analytics, and worker diagnostics."""
        # 1. Host hardware metrics
        cpu_percent = psutil.cpu_percent()
        ram_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage("/").percent

        # 2. Database connection pool count
        try:
            res = await self.db.execute(text("SELECT count(*) FROM pg_stat_activity"))
            db_connections = res.scalar() or 1
        except Exception:
            db_connections = 1

        # 3. Active clusters summary
        workers_res = await self.db.execute(select(func.count(Worker.id)).where(Worker.status != "offline", Worker.deleted_at == None))
        active_workers = workers_res.scalar() or 0

        queues_res = await self.db.execute(select(func.count(Queue.id)).where(Queue.is_active == True, Queue.deleted_at == None))
        active_queues = queues_res.scalar() or 0

        jobs_res = await self.db.execute(select(Job.status, func.count(Job.id)).where(Job.deleted_at == None).group_by(Job.status))
        status_counts = dict(jobs_res.all())

        running_jobs = status_counts.get("running", 0)
        waiting_jobs = status_counts.get("queued", 0)
        failed_jobs = status_counts.get("failed", 0)
        success_jobs = status_counts.get("success", 0)

        # 4. Queue Analytics
        queue_analytics = []
        queues_stmt = select(Queue).where(Queue.deleted_at == None)
        queues_list = (await self.db.execute(queues_stmt)).scalars().all()

        for q in queues_list:
            q_jobs_res = await self.db.execute(select(func.count(Job.id)).where(Job.queue_id == q.id, Job.deleted_at == None))
            q_size = q_jobs_res.scalar() or 0

            wait_stmt = select(func.avg(func.extract('epoch', Job.run_at - Job.created_at))).where(Job.queue_id == q.id, Job.deleted_at == None)
            avg_wait = (await self.db.execute(wait_stmt)).scalar() or 0.0

            exec_stmt = select(func.avg(JobExecution.duration_ms)).join(Job).where(Job.queue_id == q.id)
            avg_exec = (await self.db.execute(exec_stmt)).scalar() or 0.0

            queue_analytics.append({
                "queue_id": str(q.id),
                "queue_name": q.name,
                "queue_size": q_size,
                "avg_wait_seconds": round(avg_wait, 2),
                "avg_execution_ms": round(avg_exec, 2),
                "is_active": q.is_active
            })

        # 5. Worker Analytics
        worker_analytics = []
        workers_stmt = select(Worker).where(Worker.deleted_at == None)
        workers_list = (await self.db.execute(workers_stmt)).scalars().all()

        for w in workers_list:
            hb_stmt = select(WorkerHeartbeat).where(WorkerHeartbeat.worker_id == w.id).order_by(WorkerHeartbeat.created_at.desc()).limit(1)
            latest_hb = (await self.db.execute(hb_stmt)).scalar_one_or_none()

            worker_analytics.append({
                "worker_id": str(w.id),
                "name": w.name,
                "status": w.status,
                "cpu_usage": latest_hb.cpu_usage if latest_hb else 0.0,
                "memory_usage": latest_hb.memory_usage if latest_hb else 0.0,
                "active_jobs": latest_hb.active_jobs_count if latest_hb else 0,
                "last_heartbeat": w.last_heartbeat.isoformat()
            })

        system_uptime = int(time.time() - STARTUP_TIME)

        return {
            "system_metrics": {
                "cpu_usage": cpu_percent,
                "memory_usage": ram_percent,
                "disk_usage": disk_percent,
                "database_connections": db_connections,
                "active_workers": active_workers,
                "active_queues": active_queues,
                "running_jobs": running_jobs,
                "waiting_jobs": waiting_jobs,
                "failed_jobs": failed_jobs,
                "success_jobs": success_jobs,
                "uptime_seconds": system_uptime
            },
            "queue_analytics": queue_analytics,
            "worker_analytics": worker_analytics
        }

