import asyncio
import logging
import sys
import random
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, delete, text

# Add parent directory to path to support app imports
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.core import (
    User, Organization, Membership, Project, Queue, Job, 
    JobExecution, JobLog, DeadLetterQueue, Worker, 
    WorkerHeartbeat, Notification, AuditLog, RetryPolicy
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scripts.seed_demo")

async def seed_demo():
    logger.info("Connecting to Database...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with async_session() as session:
        async with session.begin():
            # 1. Database Migrations (ensure workflows table and workflow_id exist)
            logger.info("Ensuring workflows table and columns exist in DB...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    status VARCHAR(50) DEFAULT 'running' NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    deleted_at TIMESTAMP WITH TIME ZONE,
                    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
                    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
                    version INTEGER DEFAULT 1 NOT NULL
                );
            """))
            await session.execute(text("""
                ALTER TABLE jobs ADD COLUMN IF NOT EXISTS workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE;
            """))
            await session.execute(text("""
                ALTER TABLE job_executions ADD COLUMN IF NOT EXISTS ai_analysis JSONB;
            """))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_jobs_workflow_id ON jobs(workflow_id);"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_workflows_project_id ON workflows(project_id);"))

            # 2. Clean up existing demo data to allow safe re-running
            logger.info("Cleaning up existing demo data...")
            
            # Delete catalyst org (cascades to projects, queues, jobs, etc.)
            await session.execute(delete(Organization).where(Organization.slug == "catalyst"))
            
            # Delete demo workers
            worker_names = [f"worker-prod-0{i}" for i in range(1, 5)]
            await session.execute(delete(Worker).where(Worker.name.in_(worker_names)))
            
            # Delete demo users
            emails = [
                "nithin200511@gmail.com", "admin@djs.com",
                "sarah.jenkins@catalyst.io", "david.chen@catalyst.io",
                "elena.rodriguez@catalyst.io", "marcus.vance@catalyst.io",
                "alicia.keys@catalyst.io", "tom.hanks@catalyst.io",
                "robert.downey@catalyst.io"
            ]
            await session.execute(delete(User).where(User.email.in_(emails)))
            
            # 2. Seed Users
            logger.info("Seeding Users...")
            users_to_create = [
                {"email": "nithin200511@gmail.com", "pwd": "Pymapass@111", "fname": "Nithin", "lname": "Kumar", "username": "nithinkumar", "role": "Owner"},
                {"email": "admin@djs.com", "pwd": "admin123", "fname": "Global", "lname": "Admin", "username": "globaladmin", "role": "Owner"},
                {"email": "sarah.jenkins@catalyst.io", "pwd": "Password123!", "fname": "Sarah", "lname": "Jenkins", "username": "sjenkins", "role": "Admin"},
                {"email": "david.chen@catalyst.io", "pwd": "Password123!", "fname": "David", "lname": "Chen", "username": "dchen", "role": "Developer"},
                {"email": "robert.downey@catalyst.io", "pwd": "Password123!", "fname": "Robert", "lname": "Downey", "username": "rdowney", "role": "Developer"},
                {"email": "elena.rodriguez@catalyst.io", "pwd": "Password123!", "fname": "Elena", "lname": "Rodriguez", "username": "erodriguez", "role": "Developer"},
                {"email": "marcus.vance@catalyst.io", "pwd": "Password123!", "fname": "Marcus", "lname": "Vance", "username": "mvance", "role": "Developer"},
                {"email": "alicia.keys@catalyst.io", "pwd": "Password123!", "fname": "Alicia", "lname": "Keys", "username": "akeys", "role": "Viewer"},
                {"email": "tom.hanks@catalyst.io", "pwd": "Password123!", "fname": "Tom", "lname": "Hanks", "username": "thanks", "role": "Viewer"}
            ]
            
            created_users = {}
            for u in users_to_create:
                db_user = User(
                    email=u["email"],
                    hashed_password=get_password_hash(u["pwd"]),
                    first_name=u["fname"],
                    last_name=u["lname"],
                    full_name=f"{u['fname']} {u['lname']}",
                    username=u["username"],
                    phone="+14155552671" if u["email"] == "nithin200511@gmail.com" else None,
                    country="United States",
                    timezone="America/New_York",
                    is_verified=True,
                    is_active=True
                )
                session.add(db_user)
                created_users[u["email"]] = db_user
            
            await session.flush()
            
            # 3. Seed Organization
            logger.info("Seeding Organization 'Catalyst'...")
            owner = created_users["nithin200511@gmail.com"]
            org = Organization(
                name="Catalyst",
                slug="catalyst",
                description="Enterprise AI and Cloud Engineering Organization specializing in distributed systems, workflow automation, intelligent scheduling, backend platforms, cloud-native applications, and AI-powered enterprise solutions.",
                owner_id=owner.id,
                plan="Enterprise",
                status="Active"
            )
            session.add(org)
            await session.flush()
            
            # 4. Seed Memberships
            logger.info("Seeding Memberships...")
            for email, db_user in created_users.items():
                role = next(u["role"] for u in users_to_create if u["email"] == email)
                membership = Membership(
                    user_id=db_user.id,
                    organization_id=org.id,
                    role=role
                )
                session.add(membership)
            
            # 5. Seed Projects
            logger.info("Seeding Projects...")
            p1 = Project(
                name="Customer Communication Platform",
                slug="customer-communication",
                description="Distributed job scheduling platform responsible for processing customer notifications, transactional emails, SMS delivery, push notifications, and marketing campaigns at enterprise scale.",
                environment="Production",
                status="Active",
                organization_id=org.id,
                created_by=owner.id
            )
            p2 = Project(
                name="AI Document Processing Platform",
                slug="ai-document-processing",
                description="Enterprise AI workflow responsible for document ingestion, OCR processing, document classification, invoice extraction, report generation, and AI-powered analytics.",
                environment="Production",
                status="Active",
                organization_id=org.id,
                created_by=owner.id
            )
            session.add(p1)
            session.add(p2)
            await session.flush()

            # 6. Seed Retry Policies
            logger.info("Seeding Retry Policies...")
            rp1 = RetryPolicy(
                name="Exponential Backoff Policy",
                type="Exponential Backoff",
                delay=5,
                max_attempts=5,
                backoff_factor=2.0
            )
            rp2 = RetryPolicy(
                name="Linear Backoff Policy",
                type="Linear Backoff",
                delay=10,
                max_attempts=3,
                backoff_factor=1.0
            )
            session.add(rp1)
            session.add(rp2)
            await session.flush()

            # 7. Seed Queues
            logger.info("Seeding Queues...")
            q_p1_names = ["Email Queue", "SMS Queue", "Push Notification Queue"]
            q_p2_names = ["OCR Queue", "AI Processing Queue", "Report Generation Queue"]
            
            queues = {}
            for name in q_p1_names:
                q = Queue(
                    project_id=p1.id,
                    name=name,
                    is_active=True,
                    is_paused=False,
                    priority=2 if "SMS" in name else 0,
                    concurrency_limit=25 if "Email" in name else 10,
                    rate_limit=100 if "Email" in name else 20,
                    created_by=owner.id
                )
                session.add(q)
                queues[name] = q
                
            for name in q_p2_names:
                q = Queue(
                    project_id=p2.id,
                    name=name,
                    is_active=True,
                    is_paused=False,
                    priority=1 if "AI" in name else 0,
                    concurrency_limit=5 if "AI" in name else 15,
                    rate_limit=50,
                    created_by=owner.id
                )
                session.add(q)
                queues[name] = q
            
            await session.flush()

            # 8. Seed Workers
            logger.info("Seeding Workers & Telemetry...")
            workers = []
            for i, name in enumerate(worker_names):
                w = Worker(
                    name=name,
                    hostname=name,
                    ip_address=f"10.0.1.{10 + i}",
                    status="active" if i < 3 else "idle",
                    last_heartbeat=datetime.now(timezone.utc),
                    system_info={
                        "cpu_count": 8 if i % 2 == 0 else 16,
                        "total_memory_gb": 32 if i % 2 == 0 else 64,
                        "os": "linux",
                        "kernel": "5.15.0-generic",
                        "architecture": "x86_64"
                    }
                )
                session.add(w)
                workers.append(w)
            await session.flush()

            # Seed heartbeats going back 2 hours
            now = datetime.now(timezone.utc)
            for w in workers:
                for mins in range(0, 120, 10):
                    hb = WorkerHeartbeat(
                        worker_id=w.id,
                        status="active" if w.status == "active" else "idle",
                        cpu_usage=random.uniform(25.0, 75.0) if w.status == "active" else random.uniform(2.0, 8.0),
                        memory_usage=random.uniform(40.0, 60.0),
                        active_jobs_count=random.randint(1, 8) if w.status == "active" else 0,
                        created_at=now - timedelta(minutes=mins)
                    )
                    session.add(hb)

            # 9. Seed Jobs (Completed, Failed, Queued, Running, DLQ)
            logger.info("Seeding Jobs & Logs...")
            
            job_types = {
                "Email Queue": [
                    {"name": "send_transactional_receipt", "payload": {"recipient": "user@example.com", "template": "receipt_v2", "amount": 128.50}},
                    {"name": "dispatch_marketing_newsletter", "payload": {"segment": "premium_customers", "campaign_id": "summer_sale_2026"}}
                ],
                "SMS Queue": [
                    {"name": "send_otp_verification", "payload": {"phone": "+15550192834", "code": "837482"}},
                    {"name": "dispatch_critical_alert", "payload": {"phone": "+15550293847", "alert": "High CPU load on DB server"}}
                ],
                "Push Notification Queue": [
                    {"name": "push_order_shipped", "payload": {"user_id": "usr_928347", "tracking_no": "1Z99AA999999999999"}},
                    {"name": "push_payment_failed", "payload": {"user_id": "usr_102834", "invoice_id": "inv_82734"}}
                ],
                "OCR Queue": [
                    {"name": "extract_invoice_pdf", "payload": {"s3_uri": "s3://catalyst-invoices/2026/07/inv_8273.pdf", "engine": "tesseract"}},
                    {"name": "ocr_passport_image", "payload": {"s3_uri": "s3://catalyst-verification/docs/pass_9283.jpg", "resolution_dpi": 300}}
                ],
                "AI Processing Queue": [
                    {"name": "classify_document_intent", "payload": {"text_length": 4500, "model": "llama-3-70b-instruct"}},
                    {"name": "extract_entities_named", "payload": {"schema_fields": ["vendor_name", "invoice_total", "tax_id"], "model": "gemini-1.5-pro"}}
                ],
                "Report Generation Queue": [
                    {"name": "generate_monthly_financials", "payload": {"quarter": "Q2", "format": "xlsx", "recipient_email": "finance@catalyst.io"}},
                    {"name": "compile_compliance_audit", "payload": {"year": 2026, "framework": "SOC2_Type_II"}}
                ]
            }

            # Generate historical job data spanning past 24 hours
            for q_name, q in queues.items():
                types = job_types[q_name]
                
                # 50 completed jobs per queue spread out
                for i in range(50):
                    job_def = random.choice(types)
                    created_time = now - timedelta(hours=random.uniform(0.1, 24))
                    started_time = created_time + timedelta(seconds=random.uniform(0.5, 3))
                    completed_time = started_time + timedelta(seconds=random.uniform(0.2, 5))
                    
                    job = Job(
                        queue_id=q.id,
                        name=job_def["name"],
                        status="success",
                        payload=job_def["payload"],
                        result={"status": "delivered", "execution_node": random.choice(worker_names), "duration_seconds": (completed_time - started_time).total_seconds()},
                        progress=100,
                        run_at=created_time,
                        created_at=created_time,
                        updated_at=completed_time
                    )
                    session.add(job)
                    await session.flush()
                    
                    # Log execution
                    exec_w = random.choice(workers)
                    dur = int((completed_time - started_time).total_seconds() * 1000)
                    execution = JobExecution(
                        job_id=job.id,
                        worker_id=exec_w.id,
                        status="success",
                        started_at=started_time,
                        completed_at=completed_time,
                        duration_ms=dur
                    )
                    session.add(execution)
                    await session.flush()
                    
                    # Log lines
                    log_1 = JobLog(job_execution_id=execution.id, job_id=job.id, level="info", message=f"Task initiated on node {exec_w.name}.", timestamp=started_time)
                    log_2 = JobLog(job_execution_id=execution.id, job_id=job.id, level="info", message=f"Fetched task dependencies and validated input payload successfully.", timestamp=started_time + timedelta(milliseconds=100))
                    log_3 = JobLog(job_execution_id=execution.id, job_id=job.id, level="info", message=f"Execution completed. Captured result output. Payload successfully processed.", timestamp=completed_time)
                    session.add_all([log_1, log_2, log_3])

                # 2 currently running jobs
                for i in range(2):
                    job_def = random.choice(types)
                    created_time = now - timedelta(seconds=random.randint(5, 60))
                    job = Job(
                        queue_id=q.id,
                        name=job_def["name"],
                        status="running",
                        payload=job_def["payload"],
                        progress=random.randint(10, 80),
                        run_at=created_time,
                        created_at=created_time,
                        updated_at=now
                    )
                    session.add(job)
                    await session.flush()
                    
                    exec_w = random.choice(workers)
                    execution = JobExecution(
                        job_id=job.id,
                        worker_id=exec_w.id,
                        status="running",
                        started_at=created_time
                    )
                    session.add(execution)
                    await session.flush()
                    
                    log_1 = JobLog(job_execution_id=execution.id, job_id=job.id, level="info", message=f"Job claim succeeded on node {exec_w.name}.", timestamp=created_time)
                    log_2 = JobLog(job_execution_id=execution.id, job_id=job.id, level="info", message="Processing input schema...", timestamp=created_time + timedelta(seconds=1))
                    session.add_all([log_1, log_2])

                # 3 currently queued jobs
                for i in range(3):
                    job_def = random.choice(types)
                    created_time = now + timedelta(seconds=random.randint(10, 300))
                    job = Job(
                        queue_id=q.id,
                        name=job_def["name"],
                        status="queued",
                        payload=job_def["payload"],
                        progress=0,
                        run_at=created_time,
                        created_at=now
                    )
                    session.add(job)

                # 2 failed jobs
                for i in range(2):
                    job_def = random.choice(types)
                    created_time = now - timedelta(hours=random.uniform(1, 8))
                    started_time = created_time + timedelta(seconds=2)
                    failed_time = started_time + timedelta(seconds=1.5)
                    
                    errors = [
                        "HTTP Request Timeout Exception: Connection lost to microservice node.",
                        "ValueError: Input argument 'recipient' must be a valid email string.",
                        "psycopg2.errors.DeadlockDetected: deadlocked concurrent database transactions."
                    ]
                    err_msg = random.choice(errors)
                    
                    # Build AI failure summary
                    from app.services.failure_analyzer import failure_analyzer
                    analysis = failure_analyzer.analyze_failure(err_msg, job_def["payload"])
                    import json
                    serialized_error = json.dumps({"message": err_msg, "analysis": analysis})
                    
                    job = Job(
                        queue_id=q.id,
                        name=job_def["name"],
                        status="failed",
                        payload=job_def["payload"],
                        progress=0,
                        error_message=serialized_error,
                        run_at=created_time,
                        created_at=created_time,
                        updated_at=failed_time,
                        max_retries=3,
                        retries_count=3
                    )
                    session.add(job)
                    await session.flush()
                    
                    exec_w = random.choice(workers)
                    execution = JobExecution(
                        job_id=job.id,
                        worker_id=exec_w.id,
                        status="failed",
                        started_at=started_time,
                        completed_at=failed_time,
                        error_message=err_msg,
                        duration_ms=1500,
                        ai_analysis=analysis
                    )
                    session.add(execution)
                    await session.flush()
                    
                    log_1 = JobLog(job_execution_id=execution.id, job_id=job.id, level="info", message=f"Task claimed by node {exec_w.name}.", timestamp=started_time)
                    log_2 = JobLog(job_execution_id=execution.id, job_id=job.id, level="error", message=f"Execution halted: {err_msg}", timestamp=failed_time)
                    session.add_all([log_1, log_2])
                    
                    # DLQ Record
                    dlq_rec = DeadLetterQueue(
                        job_id=job.id,
                        failed_at=failed_time,
                        reason=err_msg,
                        payload=job_def["payload"]
                    )
                    session.add(dlq_rec)

            # 10. Seed Notifications
            logger.info("Seeding Notifications...")
            notifs = [
                {"title": "Worker worker-prod-04 Disconnected", "msg": "Node worker-prod-04 missed 3 consecutive heartbeat cycles. Status updated to offline.", "type": "Alert"},
                {"title": "High CPU utilization", "msg": "Node worker-prod-01 CPU usage exceeded threshold 90%. System auto-regulating queue concurrency limits.", "type": "Alert"},
                {"title": "Job retry successful", "msg": "Job generate_monthly_financials succeeded on retry attempt 2.", "type": "System"},
                {"title": "Billing queue paused", "msg": "Queue 'Report Generation Queue' was paused by administrator action.", "type": "System"}
            ]
            for n in notifs:
                notif = Notification(
                    organization_id=org.id,
                    title=n["title"],
                    message=n["msg"],
                    type=n["type"],
                    status="sent",
                    sent_at=now - timedelta(minutes=random.randint(10, 120))
                )
                session.add(notif)

            # 11. Seed Audit Logs
            logger.info("Seeding Audit Logs...")
            audit_events = [
                {"action": "User Login", "type": "User", "changes": None},
                {"action": "Queue Created", "type": "Queue", "changes": {"name": "AI Processing Queue", "concurrency_limit": 5}},
                {"action": "Queue Paused", "type": "Queue", "changes": {"name": "Report Generation Queue", "is_paused": True}},
                {"action": "Worker Started", "type": "Worker", "changes": {"name": "worker-prod-01", "ip_address": "10.0.1.10"}},
                {"action": "Settings Updated", "type": "Organization", "changes": {"plan": "Enterprise"}}
            ]
            for e in audit_events:
                al = AuditLog(
                    user_id=owner.id,
                    action=e["action"],
                    entity_type=e["type"],
                    entity_id=uuid.uuid4(),
                    changes=e["changes"],
                    ip_address="192.168.1.52",
                    created_at=now - timedelta(hours=random.uniform(0.5, 4))
                )
                session.add(al)

    logger.info("Demo database seeding completed successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_demo())
