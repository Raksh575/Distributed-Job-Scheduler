import asyncio
import os
import sys

# Ensure app can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import select
from app.db.database import AsyncSessionFactory
from app.models.core import User, Organization, Membership, Project, Queue, Job, RetryPolicy, Worker, JobExecution, ScheduledJob

async def audit_models():
    models = [
        User, Organization, Membership, Project, Queue, Job, 
        RetryPolicy, Worker, JobExecution, ScheduledJob
    ]
    
    print("Starting Model Audit...")
    for model in models:
        try:
            async with AsyncSessionFactory() as session:
                # Try to select the first record to ensure schema matches
                stmt = select(model).limit(1)
                await session.execute(stmt)
                print(f"[OK] {model.__name__} maps correctly to {model.__tablename__}")
        except Exception as e:
            print(f"[FAIL] {model.__name__} mismatch with {model.__tablename__}:")
            print(str(e).split('\n')[0])
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(audit_models())
