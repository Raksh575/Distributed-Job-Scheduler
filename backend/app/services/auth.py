import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BadRequestException, UnauthorizedException, ForbiddenException
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token
)
from app.models.core import User, RefreshToken
from app.repositories.core import UserRepository, RefreshTokenRepository, MembershipRepository

class AuthService:
    """
    AuthService coordinates security policies, password checking via Argon2,
    brute-force lockout timers, and JWT Refresh Token Rotation family protections.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.user_repo = UserRepository(db_session)
        self.token_repo = RefreshTokenRepository(db_session)
        self.membership_repo = MembershipRepository(db_session)

    async def register(self, payload) -> User:
        """Register a new user account."""
        existing_user = await self.user_repo.get_by_email(payload.email)
        if existing_user:
            raise BadRequestException(
                message="A user with this email address already exists.",
                code="EMAIL_EXISTS"
            )

        hashed_pass = get_password_hash(payload.password)
        new_user = User(
            email=payload.email,
            hashed_password=hashed_pass,
            first_name=payload.first_name,
            last_name=payload.last_name,
            username=payload.username,
            is_active=True,
            is_verified=False
        )
        return await self.user_repo.create(new_user)

    async def authenticate(self, email: str, password: str) -> User:
        """Authenticate user credentials, managing brute-force failure counts and lockouts."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UnauthorizedException(
                message="Invalid email credentials or password.",
                code="INVALID_CREDENTIALS"
            )

        # Check account lockout status
        now = datetime.now(timezone.utc)
        if user.locked_until and user.locked_until > now:
            minutes_remaining = int((user.locked_until - now).total_seconds() / 60) + 1
            raise UnauthorizedException(
                message=f"Account is temporarily locked. Retry in {minutes_remaining} minutes.",
                code="ACCOUNT_LOCKED",
                details={"locked_until": user.locked_until.isoformat()}
            )

        if not user.is_active:
            raise UnauthorizedException(
                message="User account is deactivated.",
                code="USER_DEACTIVATED"
            )

        # Verify password
        if not verify_password(password, user.hashed_password):
            # Increment failed attempts
            attempts = user.login_attempts + 1
            updates = {"login_attempts": attempts}
            
            if attempts >= 5:
                # Lockout for 15 minutes
                updates["locked_until"] = now + timedelta(minutes=15)
                updates["login_attempts"] = 0
                
            await self.user_repo.update(user, updates)
            
            raise UnauthorizedException(
                message="Invalid email credentials or password.",
                code="INVALID_CREDENTIALS"
            )

        # Reset login attempts on success
        if user.login_attempts > 0 or user.locked_until is not None:
            await self.user_repo.update(user, {"login_attempts": 0, "locked_until": None})

        return user

    async def create_tokens_for_user(self, user: User, device_info: Optional[str] = None) -> Tuple[str, str]:
        """Generate Access Token (with RBAC roles) and Refresh Token session."""
        # 1. Fetch memberships to build role claims
        memberships = await self.membership_repo.get_user_memberships(user.id)
        role_claims = {str(m.organization_id): m.role for m in memberships}

        # 2. Generate token strings
        access_token = create_access_token(subject=user.id, organization_role_claims=role_claims)
        refresh_token_val = create_refresh_token(subject=user.id)

        # 3. Create RefreshToken session record
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        db_token = RefreshToken(
            user_id=user.id,
            token=refresh_token_val,
            expires_at=expires_at,
            device_info=device_info,
            token_family=uuid.uuid4()
        )
        await self.token_repo.create(db_token)
        
        return access_token, refresh_token_val

    async def refresh_session(self, refresh_token_str: str, device_info: Optional[str] = None) -> Tuple[str, str]:
        """
        Validate and rotate refresh token.
        Detects reuse attacks: if a revoked refresh token is re-submitted,
        we revoke the entire token family.
        """
        # Validate signature
        try:
            payload = decode_access_token(refresh_token_str)
            if payload.get("type") != "refresh":
                raise UnauthorizedException(message="Invalid token type.", code="INVALID_TOKEN")
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise UnauthorizedException(message="Missing subject claim.", code="INVALID_TOKEN")
            user_uuid = uuid.UUID(user_id_str)
        except Exception as e:
            raise UnauthorizedException(message="Could not validate refresh token.", code="INVALID_TOKEN", details={"error": str(e)})

        # Query database session record
        db_token = await self.token_repo.get_by_token(refresh_token_str)
        if not db_token:
            raise UnauthorizedException(message="Session token not found.", code="INVALID_TOKEN")

        # Reuse Detection: Check if token has already been revoked
        if db_token.revoked_at is not None:
            # Compromised token family! Revoke all tokens in family.
            await self.token_repo.revoke_family(db_token.token_family)
            raise ForbiddenException(
                message="Compromised session detected. All sessions in this family are revoked.",
                code="SESSION_COMPROMISED"
            )

        now = datetime.now(timezone.utc)
        if db_token.expires_at < now:
            raise UnauthorizedException(message="Session has expired. Please re-login.", code="SESSION_EXPIRED")

        # Fetch User object
        user = await self.user_repo.get_by_id(user_uuid)
        if not user or not user.is_active:
            raise UnauthorizedException(message="User is inactive or deleted.", code="USER_INACTIVE")

        # Rotate tokens:
        # 1. Mark current token as revoked
        await self.token_repo.update(db_token, {"revoked_at": now})

        # 2. Gather role claims and generate new tokens
        memberships = await self.membership_repo.get_user_memberships(user.id)
        role_claims = {str(m.organization_id): m.role for m in memberships}

        new_access = create_access_token(subject=user.id, organization_role_claims=role_claims)
        new_refresh = create_refresh_token(subject=user.id)

        # 3. Save new refresh token under the SAME family
        expires_at = now + timedelta(days=7)
        new_db_token = RefreshToken(
            user_id=user.id,
            token=new_refresh,
            expires_at=expires_at,
            device_info=device_info or db_token.device_info,
            token_family=db_token.token_family
        )
        await self.token_repo.create(new_db_token)

        return new_access, new_refresh

    async def logout(self, refresh_token_str: str) -> None:
        """Revoke user refresh token session on signout."""
        db_token = await self.token_repo.get_by_token(refresh_token_str)
        if db_token and db_token.revoked_at is None:
            await self.token_repo.update(db_token, {"revoked_at": datetime.now(timezone.utc)})

    async def change_password(self, user: User, current_password: str, new_password: str) -> None:
        """Change user password, verifying current credentials first."""
        if not verify_password(current_password, user.hashed_password):
            raise BadRequestException(message="Incorrect password entered.", code="INCORRECT_PASSWORD")

        new_hash = get_password_hash(new_password)
        await self.user_repo.update(user, {"hashed_password": new_hash})
