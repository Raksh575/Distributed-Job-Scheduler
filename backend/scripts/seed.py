import asyncio
import logging
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

# Add parent directory to path to support app imports
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.core import User, Organization, Membership, Project, Queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scripts.seed")

async def seed_database():
    logger.info("Connecting to Supabase PostgreSQL database...")
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with async_session() as session:
        async with session.begin():
            # 1. Seed Super Admin User
            admin_email = "admin@djs.com"
            result = await session.execute(select(User).where(User.email == admin_email))
            admin_user = result.scalar_one_or_none()

            if not admin_user:
                logger.info(f"Seeding super administrator '{admin_email}'...")
                admin_user = User(
                    email=admin_email,
                    hashed_password=get_password_hash("admin123"),
                    full_name="Global Administrator",
                    is_verified=True,
                    is_active=True
                )
                session.add(admin_user)
                await session.flush()  # Populates admin_user.id
            else:
                logger.info(f"Super admin '{admin_email}' already exists.")

            # 2. Seed Acme Corp Organization
            org_slug = "acme"
            result = await session.execute(select(Organization).where(Organization.slug == org_slug))
            org = result.scalar_one_or_none()

            if not org:
                logger.info(f"Seeding organization '{org_slug}'...")
                org = Organization(
                    name="Acme Corp",
                    slug=org_slug,
                    created_by=admin_user.id
                )
                session.add(org)
                await session.flush()  # Populates org.id
            else:
                logger.info(f"Organization '{org_slug}' already exists.")

            # 3. Seed Membership linking admin to organization
            result = await session.execute(
                select(Membership).where(
                    Membership.user_id == admin_user.id,
                    Membership.organization_id == org.id
                )
            )
            membership = result.scalar_one_or_none()

            if not membership:
                logger.info("Seeding membership link...")
                membership = Membership(
                    user_id=admin_user.id,
                    organization_id=org.id,
                    role="Super Admin",
                    created_by=admin_user.id
                )
                session.add(membership)
            else:
                logger.info("Membership link already exists.")

            # 4. Seed default Project
            project_slug = "production-scheduler"
            result = await session.execute(
                select(Project).where(
                    Project.organization_id == org.id,
                    Project.slug == project_slug
                )
            )
            project = result.scalar_one_or_none()

            if not project:
                logger.info(f"Seeding project '{project_slug}'...")
                project = Project(
                    name="Production Scheduler",
                    slug=project_slug,
                    organization_id=org.id,
                    created_by=admin_user.id
                )
                session.add(project)
                await session.flush()
            else:
                logger.info(f"Project '{project_slug}' already exists.")

            # 5. Seed default Queue
            queue_name = "default-task-queue"
            result = await session.execute(
                select(Queue).where(
                    Queue.project_id == project.id,
                    Queue.name == queue_name
                )
            )
            queue = result.scalar_one_or_none()

            if not queue:
                logger.info(f"Seeding queue '{queue_name}'...")
                queue = Queue(
                    project_id=project.id,
                    name=queue_name,
                    is_active=True,
                    created_by=admin_user.id
                )
                session.add(queue)
            else:
                logger.info(f"Queue '{queue_name}' already exists.")

    logger.info("Database seeding successfully completed!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_database())
