import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.middleware.auth import get_current_user, RequirePermission
from app.models.core import User
from app.schemas.dto import (
    OrgCreate,
    OrgResponse,
    OrgUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate
)
from app.services.org import OrgService

router = APIRouter()

# ========================================================
# ORGANIZATION ENDPOINTS
# ========================================================

@router.post("", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_in: OrgCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new organization workspace. Creator becomes owner."""
    org_service = OrgService(db)
    org = await org_service.create_org(
        creator_id=current_user.id,
        org_in=org_in
    )
    return org


@router.get("/{org_id}", response_model=OrgResponse, dependencies=[Depends(RequirePermission("metrics_access"))])
async def get_organization(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve organization details."""
    org_service = OrgService(db)
    return await org_service.get_org_by_id(org_id)


@router.patch("/{org_id}", response_model=OrgResponse, dependencies=[Depends(RequirePermission("org_management"))])
async def update_organization(
    org_id: uuid.UUID,
    org_update: OrgUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Modify organization name details."""
    org_service = OrgService(db)
    return await org_service.update_org(
        org_id=org_id,
        updater_id=current_user.id,
        org_update=org_update
    )


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RequirePermission("org_management"))])
async def delete_organization(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Soft delete organization workspace."""
    org_service = OrgService(db)
    await org_service.delete_org(org_id)


# ========================================================
# PROJECT ENDPOINTS
# ========================================================

@router.post("/{org_id}/projects", response_model=ProjectResponse, dependencies=[Depends(RequirePermission("org_management"))])
async def create_project(
    org_id: uuid.UUID,
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new project workspace under an organization."""
    org_service = OrgService(db)
    return await org_service.create_project(
        org_id=org_id,
        creator_id=current_user.id,
        project_in=project_in
    )


@router.get("/{org_id}/projects", response_model=List[ProjectResponse], dependencies=[Depends(RequirePermission("metrics_access"))])
async def list_projects(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """List all projects under an organization. Auto-creates a default project if none exist."""
    org_service = OrgService(db)
    projects = await org_service.project_repo.get_by_org(org_id)
    if not projects:
        # Retroactively create a default project for orgs that predate auto-project creation
        from app.models.core import Project
        default_project = Project(
            name="Default",
            slug="default",
            description="Default project workspace",
            environment="production",
            organization_id=org_id,
            created_by=current_user.id
        )
        from app.repositories.core import ProjectRepository
        project_repo = ProjectRepository(db)
        created = await project_repo.create(default_project)
        projects = [created]
    return projects


@router.get("/{org_id}/projects/{project_id}", response_model=ProjectResponse, dependencies=[Depends(RequirePermission("metrics_access"))])
async def get_project(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve detailed project settings."""
    org_service = OrgService(db)
    project = await org_service.get_project_by_id(project_id)
    return project


@router.patch("/{org_id}/projects/{project_id}", response_model=ProjectResponse, dependencies=[Depends(RequirePermission("org_management"))])
async def update_project(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update project details."""
    org_service = OrgService(db)
    return await org_service.update_project(
        project_id=project_id,
        updater_id=current_user.id,
        project_update=project_update
    )


@router.delete("/{org_id}/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RequirePermission("org_management"))])
async def delete_project(
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Soft delete project workspace."""
    org_service = OrgService(db)
    await org_service.delete_project(project_id)
