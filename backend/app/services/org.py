import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.core import Organization, Project, Membership, User
from app.repositories.core import (
    OrganizationRepository,
    ProjectRepository,
    MembershipRepository,
    UserRepository
)

class OrgService:
    """
    OrgService coordinates business transactions relating to Organizations,
    Projects, and User Memberships.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.org_repo = OrganizationRepository(db_session)
        self.project_repo = ProjectRepository(db_session)
        self.member_repo = MembershipRepository(db_session)
        self.user_repo = UserRepository(db_session)

    # ========================================================
    # ORGANIZATION METHODS
    # ========================================================

    async def create_org(self, creator_id: uuid.UUID, org_in) -> Organization:
        """Create an organization and automatically assign the creator as 'Organization Admin'."""
        existing_org = await self.org_repo.get_by_slug(org_in.slug)
        if existing_org:
            raise BadRequestException(
                message=f"Organization slug '{org_in.slug}' is already taken.",
                code="SLUG_TAKEN"
            )

        new_org = Organization(name=org_in.name, slug=org_in.slug, description=org_in.description, created_by=creator_id, owner_id=creator_id)
        created_org = await self.org_repo.create(new_org)

        # Assign creator as Owner
        membership = Membership(
            user_id=creator_id,
            organization_id=created_org.id,
            role="Owner",
            created_by=creator_id
        )
        await self.member_repo.create(membership)

        # Auto-create a default project so the org is immediately usable
        default_project = Project(
            name="Default",
            slug="default",
            description="Default project workspace",
            environment="production",
            organization_id=created_org.id,
            created_by=creator_id
        )
        await self.project_repo.create(default_project)
        
        return created_org

    async def get_org_by_id(self, org_id: uuid.UUID) -> Organization:
        """Fetch organization, raising error if not found."""
        org = await self.org_repo.get_by_id(org_id)
        if not org:
            raise NotFoundException(message="Organization not found.", code="ORGANIZATION_NOT_FOUND")
        return org

    async def update_org(self, org_id: uuid.UUID, updater_id: uuid.UUID, org_update) -> Organization:
        """Update organization details."""
        org = await self.get_org_by_id(org_id)
        update_data = org_update.model_dump(exclude_unset=True)
        update_data["updated_by"] = updater_id
        return await self.org_repo.update(org, update_data)

    async def delete_org(self, org_id: uuid.UUID) -> None:
        """Soft delete organization."""
        org = await self.get_org_by_id(org_id)
        await self.org_repo.delete(org, soft=True)

    # ========================================================
    # PROJECT METHODS
    # ========================================================

    async def create_project(self, org_id: uuid.UUID, creator_id: uuid.UUID, project_in) -> Project:
        """Create a new project workspace under an organization."""
        # Ensure organization exists
        await self.get_org_by_id(org_id)

        # Check slug uniqueness within organization
        existing_project = await self.project_repo.get_by_slug(org_id, project_in.slug)
        if existing_project:
            raise BadRequestException(
                message=f"Project slug '{project_in.slug}' already exists in this organization.",
                code="PROJECT_SLUG_EXISTS"
            )

        new_project = Project(
            name=project_in.name,
            slug=project_in.slug,
            description=project_in.description,
            environment=project_in.environment,
            organization_id=org_id,
            created_by=creator_id
        )
        return await self.project_repo.create(new_project)

    async def get_project_by_id(self, project_id: uuid.UUID) -> Project:
        """Fetch project details, raising error if not found."""
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise NotFoundException(message="Project not found.", code="PROJECT_NOT_FOUND")
        return project

    async def update_project(self, project_id: uuid.UUID, updater_id: uuid.UUID, project_update) -> Project:
        """Update project details."""
        project = await self.get_project_by_id(project_id)
        update_data = project_update.model_dump(exclude_unset=True)
        update_data["updated_by"] = updater_id
        return await self.project_repo.update(project, update_data)

    async def delete_project(self, project_id: uuid.UUID) -> None:
        """Soft delete project."""
        project = await self.get_project_by_id(project_id)
        await self.project_repo.delete(project, soft=True)

    # ========================================================
    # MEMBERSHIP METHODS
    # ========================================================

    async def add_membership(self, org_id: uuid.UUID, creator_id: uuid.UUID, target_email: str, role: str) -> Membership:
        """Add a user to an organization with a specific role."""
        # Ensure organization exists
        await self.get_org_by_id(org_id)

        # Resolve user email
        user = await self.user_repo.get_by_email(target_email)
        if not user:
            raise NotFoundException(
                message="User account with this email address was not found.",
                code="USER_NOT_FOUND"
            )

        # Check existing membership
        existing_member = await self.member_repo.get_membership(user.id, org_id)
        if existing_member:
            raise BadRequestException(
                message="This user is already a member of this organization.",
                code="MEMBERSHIP_EXISTS"
            )

        new_member = Membership(
            user_id=user.id,
            organization_id=org_id,
            role=role,
            created_by=creator_id
        )
        return await self.member_repo.create(new_member)

    async def update_membership(self, membership_id: uuid.UUID, updater_id: uuid.UUID, role: str) -> Membership:
        """Promote or demote member's role."""
        membership = await self.member_repo.get_by_id(membership_id)
        if not membership:
            raise NotFoundException(message="Membership record not found.", code="MEMBERSHIP_NOT_FOUND")
        
        return await self.member_repo.update(membership, {"role": role, "updated_by": updater_id})

    async def remove_membership(self, membership_id: uuid.UUID) -> None:
        """Remove a member from the organization."""
        membership = await self.member_repo.get_by_id(membership_id)
        if not membership:
            raise NotFoundException(message="Membership record not found.", code="MEMBERSHIP_NOT_FOUND")
        
        await self.member_repo.delete(membership, soft=True)
