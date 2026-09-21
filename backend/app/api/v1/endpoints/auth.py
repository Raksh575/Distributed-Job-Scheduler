from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.middleware.auth import get_current_user
from app.models.core import User
from app.schemas.dto import (
    UserRegister,
    UserResponse,
    TokenResponse,
    TokenRefreshRequest,
    PasswordChange,
    PasswordResetRequest
)
from app.services.auth import AuthService

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserRegister,
    db: AsyncSession = Depends(get_db_session)
):
    """Register a new user account."""
    import re
    from app.core.exceptions import BadRequestException

    password = user_in.password
    if len(password) < 8:
        raise BadRequestException(message="Password must be at least 8 characters long.", code="PASSWORD_TOO_SHORT")
    if not re.search(r"[A-Z]", password):
        raise BadRequestException(message="Password must contain at least one uppercase letter.", code="PASSWORD_NO_UPPERCASE")
    if not re.search(r"[a-z]", password):
        raise BadRequestException(message="Password must contain at least one lowercase letter.", code="PASSWORD_NO_LOWERCASE")
    if not re.search(r"[0-9]", password):
        raise BadRequestException(message="Password must contain at least one digit.", code="PASSWORD_NO_DIGIT")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise BadRequestException(message="Password must contain at least one special character.", code="PASSWORD_NO_SPECIAL")

    auth_service = AuthService(db)
    user = await auth_service.register(payload=user_in)
    return user

@router.post("/token", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session)
):
    """Authenticate credentials and generate active session JWT tokens."""
    auth_service = AuthService(db)
    user = await auth_service.authenticate(
        email=form_data.username,
        password=form_data.password
    )
    
    device_info = request.headers.get("user-agent", "Unknown Device")
    access_token, refresh_token = await auth_service.create_tokens_for_user(
        user=user,
        device_info=device_info
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    refresh_in: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Validate and rotate refresh tokens, generating fresh session pairs."""
    auth_service = AuthService(db)
    device_info = request.headers.get("user-agent", "Unknown Device")
    access_token, refresh_token = await auth_service.refresh_session(
        refresh_token_str=refresh_in.refresh_token,
        device_info=device_info
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_in: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Revoke user refresh token and sign out."""
    auth_service = AuthService(db)
    await auth_service.logout(refresh_token_str=refresh_in.refresh_token)

@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    change_in: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update password, validating old credentials first."""
    auth_service = AuthService(db)
    await auth_service.change_password(
        user=current_user,
        current_password=change_in.old_password,
        new_password=change_in.new_password
    )

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(reset_in: PasswordResetRequest):
    """Initiate password recovery sequence (stub)."""
    return {"message": "If this email is registered, a password recovery link has been dispatched."}
