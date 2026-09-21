from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.middleware.auth import get_current_user
from app.models.core import User
from app.repositories.core import UserRepository
from typing import List
from app.schemas.dto import UserResponse, UserUpdate, OrgResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Fetch profile data of the currently logged-in user."""
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Modify profile parameters for the active user."""
    user_repo = UserRepository(db)
    # Filter non-None values to apply partial update
    update_data = user_update.model_dump(exclude_unset=True)
    updated_user = await user_repo.update(current_user, update_data)
    return updated_user

@router.get("/me/organizations", response_model=List[OrgResponse])
async def get_my_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve list of organizations the active user is a member of."""
    from app.models.core import Membership
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    query = select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.deleted_at == None
    ).options(selectinload(Membership.organization))
    
    result = await db.execute(query)
    memberships = result.scalars().all()
    return [m.organization for m in memberships if m.organization is not None]
