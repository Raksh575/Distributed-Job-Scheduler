import uuid
from typing import Dict, List, Set, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.core.security import decode_access_token
from app.db.database import get_db_session
from app.models.core import User
from app.repositories.core import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "Super Admin": {
        "user_management",
        "org_management",
        "queue_management",
        "worker_management",
        "job_management",
        "metrics_access"
    },
    "Owner": {
        "user_management",
        "org_management",
        "queue_management",
        "worker_management",
        "job_management",
        "metrics_access"
    },
    "Admin": {
        "user_management",
        "org_management",
        "queue_management",
        "worker_management",
        "job_management",
        "metrics_access"
    },
    "Developer": {
        "queue_management",
        "worker_management",
        "job_management",
        "metrics_access"
    },
    "Viewer": {
        "metrics_access"
    }
}

async def get_token_payload(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI Dependency: Decode access token and return token claims payload."""
    return decode_access_token(token)

async def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """FastAPI Dependency: Fetch current authenticated user from token subject."""
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException(message="Token missing subject identifier.", code="INVALID_TOKEN")
    
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException(message="Invalid subject UUID format.", code="INVALID_TOKEN")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_uuid)
    if not user:
        raise UnauthorizedException(message="User not found in system records.", code="USER_NOT_FOUND")
    if not user.is_active:
        raise UnauthorizedException(message="User account is deactivated.", code="USER_DEACTIVATED")

    return user

class RequirePermission:
    """
    FastAPI Dependency Guard enforcing Role-Based Access Control (RBAC).
    Checks that the user has the required permission in the specified organization.
    """

    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(
        self,
        request: Request,
        payload: dict = Depends(get_token_payload),
        current_user: User = Depends(get_current_user)
    ) -> None:
        # Extract organization_id from path parameters
        org_id_str = request.path_params.get("org_id")
        if not org_id_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization scope identifier (org_id) is missing in path."
            )

        # Check organization role claims inside access token
        roles_claims: Dict[str, str] = payload.get("roles", {})
        user_role = roles_claims.get(org_id_str)

        # If user has no membership role in this org, check if they are Super Admin globally
        # By standard design, if they have 'Super Admin' role in any org claim, we can grant global access,
        # or we verify if they have the specific role in the target org.
        if not user_role:
            # Check if user has global 'Super Admin' role in any organization
            is_global_admin = any(role == "Super Admin" for role in roles_claims.values())
            if is_global_admin:
                user_role = "Super Admin"
            else:
                raise ForbiddenException(
                    message="You are not a member of this organization workspace.",
                    code="FORBIDDEN_ORG_ACCESS"
                )

        # Validate that the role has the required permission
        allowed_permissions = ROLE_PERMISSIONS.get(user_role, set())
        if self.required_permission not in allowed_permissions:
            raise ForbiddenException(
                message=f"Insufficient permissions. Required: {self.required_permission}",
                code="INSUFFICIENT_PERMISSIONS",
                details={"required_permission": self.required_permission, "user_role": user_role}
            )
