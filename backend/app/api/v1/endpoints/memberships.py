import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.middleware.auth import get_current_user, RequirePermission
from app.models.core import User, Membership
from app.schemas.dto import MembershipCreate, MembershipResponse, MembershipUpdate
from app.services.org import OrgService

router = APIRouter()

@router.post("/{org_id}/members", response_model=MembershipResponse, dependencies=[Depends(RequirePermission("user_management"))])
async def add_member(
    org_id: uuid.UUID,
    invite_in: MembershipCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Invite and add a user to the organization with a designated role."""
    org_service = OrgService(db)
    membership = await org_service.add_membership(
        org_id=org_id,
        creator_id=current_user.id,
        target_email=invite_in.email,
        role=invite_in.role
    )
    
    # Load user relationship details before returning response
    query = select(Membership).where(Membership.id == membership.id).options(selectinload(Membership.user))
    result = await db.execute(query)
    return result.scalar_one()


@router.get("/{org_id}/members", response_model=List[MembershipResponse], dependencies=[Depends(RequirePermission("metrics_access"))])
async def list_members(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """List all members and their roles inside an organization."""
    query = select(Membership).where(
        Membership.organization_id == org_id,
        Membership.deleted_at == None
    ).options(selectinload(Membership.user))
    
    result = await db.execute(query)
    memberships = result.scalars().all()
    return list(memberships)


@router.patch("/{org_id}/members/{membership_id}", response_model=MembershipResponse, dependencies=[Depends(RequirePermission("user_management"))])
async def update_member_role(
    org_id: uuid.UUID,
    membership_id: uuid.UUID,
    role_update: MembershipUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Change organization role for a specific membership."""
    org_service = OrgService(db)
    membership = await org_service.update_membership(
        membership_id=membership_id,
        updater_id=current_user.id,
        role=role_update.role
    )
    
    # Reload details
    query = select(Membership).where(Membership.id == membership.id).options(selectinload(Membership.user))
    result = await db.execute(query)
    return result.scalar_one()


@router.delete("/{org_id}/members/{membership_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RequirePermission("user_management"))])
async def remove_member(
    org_id: uuid.UUID,
    membership_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Kick and remove a member from the organization."""
    org_service = OrgService(db)
    await org_service.remove_membership(membership_id)
