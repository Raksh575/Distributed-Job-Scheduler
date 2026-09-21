import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, update
from app.repositories.base import BaseRepository
from app.models.core import (
    User,
    Organization,
    Membership,
    Project,
    Queue,
    Job,
    ScheduledJob,
    RefreshToken,
    AuditLog,
    JobExecution,
    DeadLetterQueue
)

class UserRepository(BaseRepository[User]):
    def __init__(self, db_session):
        super().__init__(User, db_session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user record by email, excluding soft-deleted items."""
        query = select(User).where(User.email == email, User.deleted_at == None)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, db_session):
        super().__init__(Organization, db_session)

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        """Resolve organization by slug."""
        query = select(Organization).where(Organization.slug == slug, Organization.deleted_at == None)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


class MembershipRepository(BaseRepository[Membership]):
    def __init__(self, db_session):
        super().__init__(Membership, db_session)

    async def get_membership(self, user_id: uuid.UUID, organization_id: uuid.UUID) -> Optional[Membership]:
        """Find a membership link by user and org ids."""
        query = select(Membership).where(
            Membership.user_id == user_id,
            Membership.organization_id == organization_id,
            Membership.deleted_at == None
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_memberships(self, user_id: uuid.UUID) -> List[Membership]:
        """Get all membership organizations for a user."""
        query = select(Membership).where(
            Membership.user_id == user_id,
            Membership.deleted_at == None
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db_session):
        super().__init__(Project, db_session)

    async def get_by_slug(self, organization_id: uuid.UUID, slug: str) -> Optional[Project]:
        """Resolve project by organization and project slugs."""
        query = select(Project).where(
            Project.organization_id == organization_id,
            Project.slug == slug,
            Project.deleted_at == None
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_org(self, organization_id: uuid.UUID) -> List[Project]:
        """List all active projects in an organization."""
        query = select(Project).where(
            Project.organization_id == organization_id,
            Project.deleted_at == None
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())


class QueueRepository(BaseRepository[Queue]):
    def __init__(self, db_session):
        super().__init__(Queue, db_session)


class JobRepository(BaseRepository[Job]):
    def __init__(self, db_session):
        super().__init__(Job, db_session)


class ScheduledJobRepository(BaseRepository[ScheduledJob]):
    def __init__(self, db_session):
        super().__init__(ScheduledJob, db_session)


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db_session):
        super().__init__(RefreshToken, db_session)

    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        """Find token record."""
        query = select(RefreshToken).where(RefreshToken.token == token, RefreshToken.deleted_at == None)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def revoke_family(self, token_family: uuid.UUID) -> None:
        """Revoke all tokens associated with a specific family ID."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.token_family == token_family)
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db_session):
        super().__init__(AuditLog, db_session)


class JobExecutionRepository(BaseRepository[JobExecution]):
    def __init__(self, db_session):
        super().__init__(JobExecution, db_session)


class DeadLetterQueueRepository(BaseRepository[DeadLetterQueue]):
    def __init__(self, db_session):
        super().__init__(DeadLetterQueue, db_session)

