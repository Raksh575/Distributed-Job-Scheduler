import asyncio
import uuid
import random
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session, AsyncSessionFactory
from app.middleware.auth import RequirePermission
from app.models.core import Queue, Job, Worker, WorkerHeartbeat
from app.services.job_service import JobService
from app.websocket.manager import ws_connection_manager

router = APIRouter()

# Global dictionary to track active simulation runs and their worker handles
ACTIVE_SIMULATIONS = {}

async def run_autoscaler_loop(org_id: uuid.UUID, queue_id: uuid.UUID):
    """Background loop that scales simulated workers based on queue length."""
    sim_workers = []
    
    while ACTIVE_SIMULATIONS.get(queue_id):
        await asyncio.sleep(1.0)
        
        async with AsyncSessionFactory() as session:
            async with session.begin():
                # 1. Count pending queued jobs
                q_jobs_res = await session.execute(
                    select(func.count(Job.id))
                    .where(Job.queue_id == queue_id, Job.status == "queued", Job.deleted_at == None)
                )
                queued_count = q_jobs_res.scalar() or 0
                
                # 2. Scaling rules
                # Target: 1 worker per 50 jobs (min 1, max 10 workers)
                target_workers_count = min(max(1, queued_count // 50), 10)
                current_active = len(sim_workers)
                
                # Scale up
                if current_active < target_workers_count:
                    diff = target_workers_count - current_active
                    for i in range(diff):
                        w_name = f"simulated-scaler-node-{uuid.uuid4().hex[:6]}"
                        new_worker = Worker(
                            name=w_name,
                            status="active",
                            system_info={"cpu_count": 2, "total_memory_gb": 4.0, "os": "linux"}
                        )
                        session.add(new_worker)
                        await session.flush()
                        
                        hb = WorkerHeartbeat(
                            worker_id=new_worker.id,
                            status="active",
                            cpu_usage=random.uniform(20.0, 60.0),
                            memory_usage=random.uniform(30.0, 50.0),
                            active_jobs_count=5
                        )
                        session.add(hb)
                        sim_workers.append(new_worker.id)
                        
                        # Notify sockets of scale up
                        await ws_connection_manager.broadcast_to_topic("notifications", {
                            "id": str(uuid.uuid4()),
                            "title": "Scale Out Event",
                            "message": f"Auto-scaler spawned simulated node: {w_name} (Queue depth: {queued_count} jobs)",
                            "type": "scale_out",
                            "created_at": datetime.now(timezone.utc).isoformat() if 'datetime' in globals() else ""
                        })
                        
                # Scale down
                elif current_active > target_workers_count and current_active > 0:
                    diff = current_active - target_workers_count
                    for i in range(diff):
                        w_id = sim_workers.pop()
                        # Update worker to offline
                        w_stmt = select(Worker).where(Worker.id == w_id)
                        res = await session.execute(w_stmt)
                        w = res.scalar_one_or_none()
                        if w:
                            w.status = "offline"
                            
                            # Notify sockets of scale in
                            await ws_connection_manager.broadcast_to_topic("notifications", {
                                "id": str(uuid.uuid4()),
                                "title": "Scale In Event",
                                "message": f"Auto-scaler removed node: {w.name} due to decreased load (Queue depth: {queued_count} jobs)",
                                "type": "scale_in",
                                "created_at": datetime.now(timezone.utc).isoformat() if 'datetime' in globals() else ""
                            })

                # If queue is completely empty, stop simulation
                if queued_count == 0:
                    # Clean up all spawned sim workers
                    for w_id in sim_workers:
                        await session.execute(delete(WorkerHeartbeat).where(WorkerHeartbeat.worker_id == w_id))
                        await session.execute(delete(Worker).where(Worker.id == w_id))
                    sim_workers.clear()
                    ACTIVE_SIMULATIONS[queue_id] = False
                    break


@router.post("/{org_id}/simulator/trigger", dependencies=[Depends(RequirePermission("queue_management"))])
async def trigger_queue_simulation(
    org_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    queue_id: Optional[uuid.UUID] = Query(None),
    job_count: int = Query(100, ge=10, le=10000),
    db: AsyncSession = Depends(get_db_session)
):
    """Enqueue N simulated jobs and fire the Horizontal Pod Auto-scaling loop."""
    # Resolve default queue if none provided
    if not queue_id:
        stmt = select(Queue.id).where(Queue.deleted_at == None).limit(1)
        res = await db.execute(stmt)
        queue_id = res.scalar_one_or_none()
        if not queue_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="No active queues found in workspace database. Create a queue first.")

    # Submit simulation jobs inside transaction
    job_service = JobService(db)
    
    mock_tasks = ["system_cleanup", "send_email", "generate_reports"]
    
    # Batch create to avoid overhead
    for i in range(job_count):
        task_name = random.choice(mock_tasks)
        payload = {
            "simulation_id": str(uuid.uuid4()),
            "job_index": i,
            "recipient": f"simulated_user_{i}@corp.com",
            "execute_on": "success"
        }
        await job_service.submit_job(
            queue_id=queue_id,
            name=task_name,
            payload=payload,
            priority=random.randint(0, 5),
            max_retries=1
        )
        
    await db.commit()

    # Launch auto scaling loop
    ACTIVE_SIMULATIONS[queue_id] = True
    background_tasks.add_task(run_autoscaler_loop, org_id, queue_id)

    return {
        "status": "simulation_started",
        "queue_id": str(queue_id),
        "jobs_created": job_count,
        "auto_scaling": True
    }


@router.post("/{org_id}/simulator/stop", dependencies=[Depends(RequirePermission("queue_management"))])
async def stop_queue_simulation(
    org_id: uuid.UUID,
    queue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Force terminate active scaling simulations and purge simulation jobs."""
    ACTIVE_SIMULATIONS[queue_id] = False
    
    # Purge simulated jobs that are still queued
    stmt = delete(Job).where(Job.queue_id == queue_id, Job.status == "queued")
    await db.execute(stmt)
    await db.commit()
    
    return {"status": "simulation_stopped"}
