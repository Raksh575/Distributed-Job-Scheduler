import jwt
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.core.config import settings
from app.core.exceptions import UnauthorizedException

# Initialize Argon2 Password Hasher with strong default parameters
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password matches the Argon2 hash."""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Hash password string using Argon2id."""
    return ph.hash(password)

def create_access_token(subject: str | Any, organization_role_claims: Optional[Dict[str, str]] = None, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate a signed JWT Access Token containing subject identifier
    and authorization RBAC claims matching memberships.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "roles": organization_role_claims or {}  # organization_id (string) -> role (string)
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a JWT Refresh Token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7) # 7 days refresh duration
        
    to_encode = {
        "exp": int(expire.timestamp()),
        "sub": str(subject),
        "type": "refresh",
        "jti": str(uuid.uuid4())
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        raise UnauthorizedException(
            message="Could not validate credentials",
            code="INVALID_CREDENTIALS",
            details={"error": str(e)}
        )
