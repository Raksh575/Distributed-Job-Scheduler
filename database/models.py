import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    String,
    Text,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# ========================================================
# DECLARATIVE BASE & BASE MODEL
# ========================================================

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass

class BaseModel(Base):
    """
    Abstract Base Model exposing audit controls, versioning,
    and soft-delete columns across all tables.
    """
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid()
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
        nullable=False
    )

# ========================================================
# MODELS DEFINITIONS
# ========================================================

class User(BaseModel):
    """Users table mapping user credentials, roles, and profiles."""
    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str] = mapped_column(String(100), default="UTC", server_default="UTC", nullable=False)
    profile_picture: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    owned_organizations: Mapped[List["Organization"]] = relationship("Organization", back_populates="owner", foreign_keys="[Organization.owner_id]")
    memberships: Mapped[List["Membership"]] = relationship("Membership", back_populates="user", foreign_keys="[Membership.user_id]")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user", foreign_keys="[AuditLog.user_id]")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="user", foreign_keys="[RefreshToken.user_id]")


class Organization(BaseModel):
    """Organizations table separating multiple workspace billing plans and teams."""
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    logo: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    plan: Mapped[str] = mapped_column(String(50), default="Free", server_default="Free", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Active", server_default="Active", nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="owned_organizations", foreign_keys=[owner_id])
    memberships: Mapped[List["Membership"]] = relationship("Membership", back_populates="organization", cascade="all, delete-orphan")
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="organization", cascade="all, delete-orphan")


class Membership(BaseModel):
    """Memberships table mapping many-to-many user membership in organizations."""
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_user_organization"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="memberships", foreign_keys=[user_id])
    organization: Mapped["Organization"] = relationship("Organization", back_populates="memberships")


class Project(BaseModel):
    """Projects table isolating workflows, queues, and resources."""
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_project_name"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    environment: Mapped[str] = mapped_column(String(50), default="Development", server_default="Development", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Active", server_default="Active", nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="projects")
    queues: Mapped[List["Queue"]] = relationship("Queue", back_populates="project", cascade="all, delete-orphan")
    scheduled_jobs: Mapped[List["ScheduledJob"]] = relationship("ScheduledJob", back_populates="project", cascade="all, delete-orphan")


class RetryPolicy(BaseModel):
    """RetryPolicies configuration detailing backoff triggers and counts."""
    __tablename__ = "retry_policies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="Fixed Delay", server_default="Fixed Delay", nullable=False)
    delay: Mapped[int] = mapped_column(Integer, default=5, server_default="5", nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, server_default="3", nullable=False)
    backoff_factor: Mapped[float] = mapped_column(Numeric(4, 2), default=2.00, server_default="2.00", nullable=False)

    # Relationships
    queues: Mapped[List["Queue"]] = relationship("Queue", back_populates="retry_policy")


class Queue(BaseModel):
    """Queues mapping parallel task processing limits and priorities."""
    __tablename__ = "queues"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_queue_name"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    concurrency_limit: Mapped[int] = mapped_column(Integer, default=10, server_default="10", nullable=False)
    retry_policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("retry_policies.id", ondelete="SET NULL"), nullable=True)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    rate_limit: Mapped[int] = mapped_column(Integer, default=100, server_default="100", nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="queues")
    retry_policy: Mapped[Optional["RetryPolicy"]] = relationship("RetryPolicy", back_populates="queues")
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="queue", cascade="all, delete-orphan")
    scheduled_jobs: Mapped[List["ScheduledJob"]] = relationship("ScheduledJob", back_populates="target_queue", cascade="all, delete-orphan")


class Worker(BaseModel):
    """Workers table defining compute instances subscribed to queues."""
    __tablename__ = "workers"

    hostname: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="idle", server_default="idle", nullable=False)
    cpu_usage: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, server_default="0.00", nullable=False)
    memory_usage: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, server_default="0.00", nullable=False)
    active_jobs: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    last_heartbeat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)

    # Relationships
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="worker")
    job_executions: Mapped[List["JobExecution"]] = relationship("JobExecution", back_populates="worker")
    heartbeats: Mapped[List["WorkerHeartbeat"]] = relationship("WorkerHeartbeat", back_populates="worker", cascade="all, delete-orphan")


class Job(BaseModel):
    """Jobs database entry holding serialized payloads, parameters, and metadata."""
    __tablename__ = "jobs"

    queue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("queues.id", ondelete="CASCADE"), nullable=False)
    worker_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("workers.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued", server_default="queued", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, server_default="3", nullable=False)
    execution_timeout: Mapped[int] = mapped_column(Integer, default=3600, server_default="3600", nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    queue: Mapped["Queue"] = relationship("Queue", back_populates="jobs")
    worker: Mapped[Optional["Worker"]] = relationship("Worker", back_populates="jobs")
    parent: Mapped[Optional["Job"]] = relationship("Job", remote_side="[Job.id]", back_populates="children")
    children: Mapped[List["Job"]] = relationship("Job", back_populates="parent")
    executions: Mapped[List["JobExecution"]] = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")
    dead_letter_records: Mapped[List["DeadLetterQueue"]] = relationship("DeadLetterQueue", back_populates="job", cascade="all, delete-orphan")
    logs: Mapped[List["JobLog"]] = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")


class ScheduledJob(BaseModel):
    """ScheduledJobs mapping repeating events generating task jobs."""
    __tablename__ = "scheduled_jobs"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_scheduled_job_name"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    cron_expression: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    interval_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_queue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("queues.id", ondelete="CASCADE"), nullable=False)
    job_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    next_run_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="scheduled_jobs")
    target_queue: Mapped["Queue"] = relationship("Queue", back_populates="scheduled_jobs")


class JobExecution(BaseModel):
    """JobExecutions details of a single execution attempt of a job."""
    __tablename__ = "job_executions"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    worker_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("workers.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cpu_usage: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, server_default="0.00", nullable=False)
    memory_usage: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, server_default="0.00", nullable=False)
    response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="executions")
    worker: Mapped[Optional["Worker"]] = relationship("Worker", back_populates="job_executions")
    logs: Mapped[List["JobLog"]] = relationship("JobLog", back_populates="execution", cascade="all, delete-orphan")


class WorkerHeartbeat(BaseModel):
    """WorkerHeartbeats logging diagnostic health reports of workers."""
    __tablename__ = "worker_heartbeats"

    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    heartbeat_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)
    cpu: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    memory: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    disk: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    # Relationships
    worker: Mapped["Worker"] = relationship("Worker", back_populates="heartbeats")


class JobLog(BaseModel):
    """JobLogs tracking detailed runtime task console output."""
    __tablename__ = "job_logs"

    job_execution_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("job_executions.id", ondelete="CASCADE"), nullable=True)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    log_level: Mapped[str] = mapped_column(String(20), default="INFO", server_default="INFO", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="logs")
    execution: Mapped[Optional["JobExecution"]] = relationship("JobExecution", back_populates="logs")


class DeadLetterQueue(BaseModel):
    """DeadLetterQueue table holding permanently failed job records."""
    __tablename__ = "dead_letter_queues"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    failed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="dead_letter_records")


class Notification(BaseModel):
    """Notifications alert dispatch ledger logs."""
    __tablename__ = "notifications"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    read_status: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="notifications")


class AuditLog(BaseModel):
    """AuditLogs for compliance monitoring and change auditing."""
    __tablename__ = "audit_logs"

    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    changes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])


class RefreshToken(BaseModel):
    """RefreshTokens table representing user login sessions."""
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(512), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    device_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens", foreign_keys=[user_id])
