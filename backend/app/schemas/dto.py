import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# ========================================================
# AUTHENTICATION SCHEMAS
# ========================================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Strong password, min 8 characters")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., min_length=1, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


# ========================================================
# USER SCHEMAS
# ========================================================

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    username: str
    phone: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    profile_picture: Optional[str] = None
    is_verified: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    username: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=100)
    profile_picture: Optional[str] = Field(None, max_length=512)
    is_active: Optional[bool] = None


# ========================================================
# ORGANIZATION SCHEMAS
# ========================================================

class OrgCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    description: Optional[str] = None


class OrgResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    logo: Optional[str] = None
    plan: str
    status: str
    created_at: datetime
    version: int

    class Config:
        from_attributes = True


class OrgUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    logo: Optional[str] = None


# ========================================================
# PROJECT SCHEMAS
# ========================================================

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    description: Optional[str] = None
    environment: Optional[str] = Field("development", max_length=50)


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    environment: str
    status: str
    organization_id: uuid.UUID
    created_at: datetime
    version: int

    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    environment: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=50)


# ========================================================
# MEMBERSHIP SCHEMAS
# ========================================================

class MembershipCreate(BaseModel):
    email: EmailStr
    role: str = Field(..., pattern="^(Super Admin|Organization Admin|Developer|Viewer)$")


class MembershipUpdate(BaseModel):
    role: str = Field(..., pattern="^(Super Admin|Organization Admin|Developer|Viewer)$")


class MembershipResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: str
    user: Optional[UserResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========================================================
# QUEUE SCHEMAS
# ========================================================

class QueueCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, pattern="^[a-zA-Z0-9_-]+$")
    priority: int = Field(default=0, ge=0, le=1000)
    concurrency_limit: int = Field(default=10, ge=1, le=1000)
    rate_limit: Optional[int] = Field(default=None, ge=1)


class QueueResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    is_active: bool
    is_paused: bool
    priority: int
    concurrency_limit: int
    rate_limit: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========================================================
# JOB SCHEMAS
# ========================================================

class JobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    payload: dict = Field(default_factory=dict)
    parent_id: Optional[uuid.UUID] = None
    delay_seconds: Optional[int] = Field(default=None, ge=0)
    priority: int = Field(default=0, ge=0, description="Higher number means higher priority")
    max_retries: int = Field(default=3, ge=0)
    timeout: Optional[int] = Field(default=None, ge=0, description="Timeout in seconds, 0 or None means no timeout")


class JobResponse(BaseModel):
    id: uuid.UUID
    queue_id: uuid.UUID
    name: str
    status: str
    payload: dict
    result: Optional[dict] = None
    progress: int
    error_message: Optional[str] = None
    run_at: datetime
    priority: int
    max_retries: int
    retries_count: int
    timeout: Optional[int] = None
    parent_id: Optional[uuid.UUID] = None
    workflow_id: Optional[uuid.UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ========================================================
# WORKFLOW SCHEMAS
# ========================================================

class WorkflowNodeCreate(BaseModel):
    temp_id: str
    name: str = Field(..., min_length=1, max_length=100)
    queue_id: uuid.UUID
    payload: dict = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    priority: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3, ge=0)

class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    nodes: List[WorkflowNodeCreate] = Field(..., min_length=1)

class WorkflowResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    status: str
    created_at: datetime
    jobs: Optional[List[JobResponse]] = None

    class Config:
        from_attributes = True


# ========================================================
# SCHEDULED JOB SCHEMAS
# ========================================================

class ScheduledJobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    trigger_type: str = Field(..., pattern="^(cron|interval)$")
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = Field(None, ge=1)
    target_queue_id: uuid.UUID
    job_name: str = Field(..., min_length=1, max_length=100)
    job_payload: dict


class ScheduledJobResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    trigger_type: str
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    target_queue_id: uuid.UUID
    job_name: str
    job_payload: dict
    is_active: bool
    next_run_time: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========================================================
# DEAD LETTER QUEUE SCHEMAS
# ========================================================

class DLQRecordResponse(BaseModel):
    job_id: uuid.UUID
    failed_at: datetime
    reason: str
    job: Optional[JobResponse] = None


    class Config:
        from_attributes = True


# ========================================================
# WORKER SCHEMAS
# ========================================================

class WorkerResponse(BaseModel):
    id: uuid.UUID
    name: str
    ip_address: Optional[str] = None
    status: str
    last_heartbeat: datetime
    system_info: dict

    class Config:
        from_attributes = True


# ========================================================
# NOTIFICATION SCHEMAS
# ========================================================

class NotificationResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    message: str
    type: str
    sent_at: Optional[datetime] = None
    status: str
    is_read: bool

    class Config:
        from_attributes = True
