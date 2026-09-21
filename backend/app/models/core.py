import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

class User(BaseModel):
    """Users table mapping user profiles and security/lockout settings."""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    profile_picture: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    
    # Brute-force protection
    login_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    memberships: Mapped[List["Membership"]] = relationship("Membership", back_populates="user", cascade="all, delete-orphan", foreign_keys="[Membership.user_id]")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan", foreign_keys="[RefreshToken.user_id]")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user", foreign_keys="[AuditLog.user_id]")


class Organization(BaseModel):
    """Organizations table separating projects and memberships."""
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    logo: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    plan: Mapped[str] = mapped_column(String(50), default="Free", server_default="Free", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Active", server_default="Active", nullable=False)

    # Relationships
    memberships: Mapped[List["Membership"]] = relationship("Membership", back_populates="organization", cascade="all, delete-orphan")
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="organization", cascade="all, delete-orphan")


class Membership(BaseModel):
    """Memberships table resolving Users <-> Organizations M2M with RBAC roles."""
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_user_organization"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False) # Roles: Super Admin, Organization Admin, Developer, Viewer

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="memberships", foreign_keys=[user_id])
    organization: Mapped["Organization"] = relationship("Organization", back_populates="memberships")


class Project(BaseModel):
    """Projects table grouping execution queues."""
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_project_slug"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    environment: Mapped[str] = mapped_column(String(50), default="development", server_default="development", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", server_default="active", nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="projects")
    queues: Mapped[List["Queue"]] = relationship("Queue", back_populates="project", cascade="all, delete-orphan")
    scheduled_jobs: Mapped[List["ScheduledJob"]] = relationship("ScheduledJob", back_populates="project", cascade="all, delete-orphan")
    workflows: Mapped[List["Workflow"]] = relationship("Workflow", back_populates="project", cascade="all, delete-orphan")


class Queue(BaseModel):
    """Queues table defining individual processing streams."""
    __tablename__ = "queues"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_queue_name"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    concurrency_limit: Mapped[int] = mapped_column(Integer, default=10, server_default="10", nullable=False)
    rate_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="queues")
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="queue", cascade="all, delete-orphan")
    retry_policies: Mapped[List["RetryPolicy"]] = relationship("RetryPolicy", back_populates="queue", cascade="all, delete-orphan")
    scheduled_jobs: Mapped[List["ScheduledJob"]] = relationship("ScheduledJob", back_populates="target_queue", cascade="all, delete-orphan")


class Job(BaseModel):
    """Jobs table storing concrete background task arguments, status, and payload details."""
    __tablename__ = "jobs"

    queue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("queues.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued", server_default="queued", index=True, nullable=False) # queued, running, success, failed, cancelled
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), index=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, server_default="3", nullable=False)
    retries_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    timeout: Mapped[int] = mapped_column("execution_timeout", Integer, default=3600, server_default="3600", nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), index=True, nullable=True)
    workflow_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), index=True, nullable=True)

    # Relationships
    queue: Mapped["Queue"] = relationship("Queue", back_populates="jobs")
    parent: Mapped[Optional["Job"]] = relationship("Job", remote_side="[Job.id]", back_populates="children")
    children: Mapped[List["Job"]] = relationship("Job", back_populates="parent")
    workflow: Mapped[Optional["Workflow"]] = relationship("Workflow", back_populates="jobs")
    executions: Mapped[List["JobExecution"]] = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")
    dead_letter_record: Mapped[Optional["DeadLetterQueue"]] = relationship("DeadLetterQueue", back_populates="job", cascade="all, delete-orphan")
    retry_policies: Mapped[List["RetryPolicy"]] = relationship("RetryPolicy", back_populates="job", cascade="all, delete-orphan")


class Workflow(BaseModel):
    """Workflows logically grouping multiple Jobs into a DAG execution graph."""
    __tablename__ = "workflows"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False) # running, success, failed, cancelled
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="workflows")
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="workflow", cascade="all, delete-orphan")


class ScheduledJob(BaseModel):
    """ScheduledJobs table storing cron/repeating triggers generating background jobs."""
    __tablename__ = "scheduled_jobs"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_scheduled_job_name"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False) # cron, interval
    cron_expression: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    interval_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_queue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("queues.id", ondelete="CASCADE"), index=True, nullable=False)
    job_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    next_run_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="scheduled_jobs")
    target_queue: Mapped["Queue"] = relationship("Queue", back_populates="scheduled_jobs")


class RetryPolicy(BaseModel):
    """RetryPolicies configuring retry parameters on execution failure."""
    __tablename__ = "retry_policies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="Fixed Delay", server_default="Fixed Delay", nullable=False)
    delay: Mapped[int] = mapped_column(Integer, default=5, server_default="5", nullable=False) # seconds
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, server_default="3", nullable=False)
    backoff_factor: Mapped[float] = mapped_column(Float, default=2.0, server_default="2.0", nullable=False)
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=True)
    queue_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("queues.id", ondelete="CASCADE"), index=True, nullable=True)

    # Relationships
    job: Mapped[Optional["Job"]] = relationship("Job", back_populates="retry_policies")
    queue: Mapped[Optional["Queue"]] = relationship("Queue", back_populates="retry_policies")


class JobExecution(BaseModel):
    """JobExecutions logging runtime attempts, durations, and output logs."""
    __tablename__ = "job_executions"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    worker_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("workers.id", ondelete="SET NULL"), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False) # success, failed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ai_analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="executions")
    worker: Mapped[Optional["Worker"]] = relationship("Worker", back_populates="executions")
    logs: Mapped[List["JobLog"]] = relationship("JobLog", back_populates="execution", cascade="all, delete-orphan")


class Worker(BaseModel):
    """Workers table defining nodes currently online in execution pools."""
    __tablename__ = "workers"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="idle", server_default="idle", index=True, nullable=False) # active, idle, offline
    last_heartbeat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)
    system_info: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Relationships
    executions: Mapped[List["JobExecution"]] = relationship("JobExecution", back_populates="worker")
    heartbeats: Mapped[List["WorkerHeartbeat"]] = relationship("WorkerHeartbeat", back_populates="worker", cascade="all, delete-orphan")


class WorkerHeartbeat(BaseModel):
    """WorkerHeartbeats logging diagnostic CPU, RAM, and load metrics of online instances."""
    __tablename__ = "worker_heartbeats"

    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workers.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    cpu_usage: Mapped[float] = mapped_column("cpu", Float, nullable=False)
    memory_usage: Mapped[float] = mapped_column("memory", Float, nullable=False)
    disk: Mapped[float] = mapped_column(Float, default=10.0, server_default="10.0", nullable=False)
    active_jobs_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    # Relationships
    worker: Mapped["Worker"] = relationship("Worker", back_populates="heartbeats")


class JobLog(BaseModel):
    """JobLogs tracking stdout/stderr logging generated by job runs."""
    __tablename__ = "job_logs"

    job_execution_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_executions.id", ondelete="CASCADE"), index=True, nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False) # info, error, warn
    message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)

    # Relationships
    execution: Mapped["JobExecution"] = relationship("JobExecution", back_populates="logs")


class DeadLetterQueue(BaseModel):
    """DeadLetterQueue holding failed jobs exceeding retry limitations."""
    __tablename__ = "dead_letter_queues"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    failed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="dead_letter_record")


class Notification(BaseModel):
    """Notifications logging alerts dispatched to external target APIs or emails."""
    __tablename__ = "notifications"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False) # email, webhook
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", server_default="pending", nullable=False) # pending, sent, failed
    is_read: Mapped[bool] = mapped_column("read_status", Boolean, default=False, server_default="false", nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="notifications")


class AuditLog(BaseModel):
    """AuditLogs tracking administrator endpoints changes for compliance auditing."""
    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    changes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])


class RefreshToken(BaseModel):
    """RefreshTokens representing security user login sessions."""
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    token: Mapped[str] = mapped_column(String(512), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    device_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    token_family: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, index=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens", foreign_keys=[user_id])
