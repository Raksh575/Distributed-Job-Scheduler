"""Create complete PostgreSQL database schema for Distributed Job Scheduler.

Revision ID: complete_schema_001
Revises: None
Create Date: 2026-07-03 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'complete_schema_001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # 2. Create Tables
    # users
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('timezone', sa.String(length=100), server_default='UTC', nullable=False),
        sa.Column('profile_picture', sa.String(length=512), nullable=True),
        sa.Column('email_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
        sa.CheckConstraint("email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,4}$'", name='check_user_email_format')
    )

    # organizations
    op.create_table(
        'organizations',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('logo', sa.String(length=512), nullable=True),
        sa.Column('plan', sa.String(length=50), server_default='Free', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='Active', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint("plan IN ('Free', 'Pro', 'Enterprise')", name='check_organization_plan'),
        sa.CheckConstraint("status IN ('Active', 'Suspended')", name='check_organization_status')
    )

    # memberships
    op.create_table(
        'memberships',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'organization_id', name='uq_user_organization'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.CheckConstraint("role IN ('Owner', 'Admin', 'Developer', 'Viewer')", name='check_memberships_role')
    )

    # projects
    op.create_table(
        'projects',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('environment', sa.String(length=50), server_default='Development', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='Active', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'name', name='uq_project_name'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.CheckConstraint("environment IN ('Production', 'Staging', 'Development')", name='check_projects_environment'),
        sa.CheckConstraint("status IN ('Active', 'Inactive')", name='check_projects_status')
    )

    # retry_policies
    op.create_table(
        'retry_policies',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), server_default='Fixed Delay', nullable=False),
        sa.Column('delay', sa.Integer(), server_default='5', nullable=False),
        sa.Column('max_attempts', sa.Integer(), server_default='3', nullable=False),
        sa.Column('backoff_factor', sa.Numeric(precision=4, scale=2), server_default='2.00', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("type IN ('Fixed Delay', 'Linear Backoff', 'Exponential Backoff')", name='check_retry_policies_type'),
        sa.CheckConstraint('delay >= 1', name='check_retry_policies_delay'),
        sa.CheckConstraint('max_attempts >= 1', name='check_retry_policies_max'),
        sa.CheckConstraint('backoff_factor >= 1.00', name='check_retry_policies_backoff')
    )

    # queues
    op.create_table(
        'queues',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('priority', sa.Integer(), server_default='1', nullable=False),
        sa.Column('concurrency_limit', sa.Integer(), server_default='10', nullable=False),
        sa.Column('retry_policy_id', sa.UUID(), nullable=True),
        sa.Column('is_paused', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('rate_limit', sa.Integer(), server_default='100', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'name', name='uq_queue_name'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['retry_policy_id'], ['retry_policies.id'], ondelete='SET NULL'),
        sa.CheckConstraint('priority >= 0', name='check_queues_priority'),
        sa.CheckConstraint('concurrency_limit >= 1', name='check_queues_concurrency'),
        sa.CheckConstraint('rate_limit >= 1', name='check_queues_rate_limit')
    )

    # workers
    op.create_table(
        'workers',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('hostname', sa.String(length=255), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='idle', nullable=False),
        sa.Column('cpu_usage', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('memory_usage', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('active_jobs', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hostname'),
        sa.CheckConstraint("status IN ('active', 'idle', 'offline')", name='check_workers_status'),
        sa.CheckConstraint('cpu_usage BETWEEN 0.00 AND 100.00', name='check_workers_cpu'),
        sa.CheckConstraint('memory_usage BETWEEN 0.00 AND 100.00', name='check_workers_mem'),
        sa.CheckConstraint('active_jobs >= 0', name='check_workers_active_jobs')
    )

    # jobs
    op.create_table(
        'jobs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('queue_id', sa.UUID(), nullable=False),
        sa.Column('worker_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='queued', nullable=False),
        sa.Column('priority', sa.Integer(), server_default='0', nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('max_attempts', sa.Integer(), server_default='3', nullable=False),
        sa.Column('execution_timeout', sa.Integer(), server_default='3600', nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['queue_id'], ['queues.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.CheckConstraint("status IN ('queued', 'running', 'success', 'failed', 'cancelled')", name='check_jobs_status'),
        sa.CheckConstraint('priority >= 0', name='check_jobs_priority'),
        sa.CheckConstraint('attempts >= 0 AND attempts <= max_attempts', name='check_jobs_attempts'),
        sa.CheckConstraint('max_attempts >= 1', name='check_jobs_max_attempts'),
        sa.CheckConstraint('execution_timeout >= 1', name='check_jobs_timeout')
    )

    # scheduled_jobs
    op.create_table(
        'scheduled_jobs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('trigger_type', sa.String(length=50), nullable=False),
        sa.Column('cron_expression', sa.String(length=255), nullable=True),
        sa.Column('interval_seconds', sa.Integer(), nullable=True),
        sa.Column('target_queue_id', sa.UUID(), nullable=False),
        sa.Column('job_name', sa.String(length=255), nullable=False),
        sa.Column('job_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('next_run_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'name', name='uq_scheduled_job_name'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_queue_id'], ['queues.id'], ondelete='CASCADE'),
        sa.CheckConstraint("trigger_type IN ('cron', 'interval', 'date')", name='check_scheduled_jobs_trigger'),
        sa.CheckConstraint('interval_seconds IS NULL OR interval_seconds >= 1', name='check_scheduled_interval')
    )

    # job_executions
    op.create_table(
        'job_executions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('worker_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_time', sa.Integer(), nullable=True),
        sa.Column('cpu_usage', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('memory_usage', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ondelete='SET NULL'),
        sa.CheckConstraint("status IN ('success', 'failed', 'running')", name='check_job_executions_status'),
        sa.CheckConstraint('cpu_usage BETWEEN 0.00 AND 100.00', name='check_job_executions_cpu'),
        sa.CheckConstraint('memory_usage BETWEEN 0.00 AND 100.00', name='check_job_executions_mem'),
        sa.CheckConstraint('execution_time IS NULL OR execution_time >= 0', name='check_job_executions_time')
    )

    # worker_heartbeats
    op.create_table(
        'worker_heartbeats',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('worker_id', sa.UUID(), nullable=False),
        sa.Column('heartbeat_time', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('cpu', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('memory', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('disk', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ondelete='CASCADE'),
        sa.CheckConstraint('cpu BETWEEN 0.00 AND 100.00', name='check_worker_heartbeats_cpu'),
        sa.CheckConstraint('memory BETWEEN 0.00 AND 100.00', name='check_worker_heartbeats_mem'),
        sa.CheckConstraint('disk BETWEEN 0.00 AND 100.00', name='check_worker_heartbeats_disk')
    )

    # job_logs
    op.create_table(
        'job_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('job_execution_id', sa.UUID(), nullable=True),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('log_level', sa.String(length=20), server_default='INFO', nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_execution_id'], ['job_executions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.CheckConstraint("log_level IN ('INFO', 'WARN', 'ERROR', 'DEBUG')", name='check_job_logs_level')
    )

    # dead_letter_queues
    op.create_table(
        'dead_letter_queues',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('failed_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE')
    )

    # notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('read_status', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.CheckConstraint("type IN ('System', 'Alert', 'Slack', 'Email')", name='check_notifications_type')
    )

    # audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )

    # refresh_tokens
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token', sa.String(length=512), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('device_info', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )

    # 3. Add audit foreign keys on users, organizations and others to resolve circularity
    op.create_foreign_key('fk_users_created_by', 'users', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_users_updated_by', 'users', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_organizations_created_by', 'organizations', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_organizations_updated_by', 'organizations', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_memberships_created_by', 'memberships', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_memberships_updated_by', 'memberships', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_projects_created_by', 'projects', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_projects_updated_by', 'projects', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_retry_policies_created_by', 'retry_policies', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_retry_policies_updated_by', 'retry_policies', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_queues_created_by', 'queues', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_queues_updated_by', 'queues', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_workers_created_by', 'workers', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_workers_updated_by', 'workers', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_jobs_created_by', 'jobs', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_jobs_updated_by', 'jobs', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_scheduled_jobs_created_by', 'scheduled_jobs', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_scheduled_jobs_updated_by', 'scheduled_jobs', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_job_executions_created_by', 'job_executions', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_job_executions_updated_by', 'job_executions', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_worker_heartbeats_created_by', 'worker_heartbeats', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_worker_heartbeats_updated_by', 'worker_heartbeats', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_job_logs_created_by', 'job_logs', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_job_logs_updated_by', 'job_logs', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_dead_letter_queues_created_by', 'dead_letter_queues', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_dead_letter_queues_updated_by', 'dead_letter_queues', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_notifications_created_by', 'notifications', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_notifications_updated_by', 'notifications', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_audit_logs_created_by', 'audit_logs', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_audit_logs_updated_by', 'audit_logs', 'users', ['updated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_refresh_tokens_created_by', 'refresh_tokens', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_refresh_tokens_updated_by', 'refresh_tokens', 'users', ['updated_by'], ['id'], ondelete='SET NULL')

    # 4. Create Indexes
    # standard indices
    op.create_index('idx_users_created_by', 'users', ['created_by'])
    op.create_index('idx_users_updated_by', 'users', ['updated_by'])
    op.create_index('idx_organizations_owner', 'organizations', ['owner_id'])
    op.create_index('idx_memberships_user', 'memberships', ['user_id'])
    op.create_index('idx_memberships_org', 'memberships', ['organization_id'])
    op.create_index('idx_projects_org', 'projects', ['organization_id'])
    op.create_index('idx_queues_project', 'queues', ['project_id'])
    op.create_index('idx_queues_retry_policy', 'queues', ['retry_policy_id'])
    op.create_index('idx_jobs_queue', 'jobs', ['queue_id'])
    op.create_index('idx_jobs_worker', 'jobs', ['worker_id'])
    op.create_index('idx_jobs_parent', 'jobs', ['parent_id'])
    op.create_index('idx_scheduled_jobs_project', 'scheduled_jobs', ['project_id'])
    op.create_index('idx_scheduled_jobs_queue', 'scheduled_jobs', ['target_queue_id'])
    op.create_index('idx_job_executions_job', 'job_executions', ['job_id'])
    op.create_index('idx_job_executions_worker', 'job_executions', ['worker_id'])
    op.create_index('idx_worker_heartbeats_worker', 'worker_heartbeats', ['worker_id'])
    op.create_index('idx_job_logs_execution', 'job_logs', ['job_execution_id'])
    op.create_index('idx_job_logs_job', 'job_logs', ['job_id'])
    op.create_index('idx_dead_letter_queues_job', 'dead_letter_queues', ['job_id'])
    op.create_index('idx_notifications_org', 'notifications', ['organization_id'])
    op.create_index('idx_audit_logs_user', 'audit_logs', ['user_id'])
    op.create_index('idx_refresh_tokens_user', 'refresh_tokens', ['user_id'])

    # composite optimizer indices
    op.execute(
        "CREATE INDEX idx_jobs_claim_optimizer ON jobs(status, scheduled_at, priority DESC) "
        "WHERE status = 'queued' AND deleted_at IS NULL"
    )
    op.execute(
        "CREATE INDEX idx_workers_heartbeat_status ON workers(status, last_heartbeat DESC) "
        "WHERE deleted_at IS NULL"
    )
    op.execute(
        "CREATE INDEX idx_scheduled_jobs_trigger_opt ON scheduled_jobs(is_active, next_run_time ASC) "
        "WHERE is_active = TRUE AND deleted_at IS NULL"
    )
    op.execute(
        "CREATE INDEX idx_job_logs_search ON job_logs(job_id, log_level, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX idx_audit_logs_tracking ON audit_logs(entity_type, entity_id, created_at DESC)"
    )

    # 5. Create PL/pgSQL Triggers & Functions
    # generic timestamp updater function
    op.execute("""
    CREATE OR REPLACE FUNCTION trigger_set_timestamp()
    RETURNS TRIGGER AS $$
    BEGIN
      NEW.updated_at = NOW();
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Apply updated_at trigger to all tables
    for table in [
        'users', 'organizations', 'memberships', 'projects', 'retry_policies',
        'queues', 'workers', 'jobs', 'scheduled_jobs', 'job_executions',
        'worker_heartbeats', 'job_logs', 'dead_letter_queues', 'notifications',
        'audit_logs', 'refresh_tokens'
    ]:
        op.execute(f"""
        CREATE TRIGGER set_timestamp_{table}
        BEFORE UPDATE ON {table}
        FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();
        """)

    # audit logger trigger
    op.execute("""
    CREATE OR REPLACE FUNCTION trigger_audit_log_actions()
    RETURNS TRIGGER AS $$
    DECLARE
      v_user_id UUID;
      v_changes JSONB;
    END;
    $$ LANGUAGE plpgsql;
    """)
    # Wait, let's execute the complete definition of the trigger_audit_log_actions
    op.execute("""
    CREATE OR REPLACE FUNCTION trigger_audit_log_actions()
    RETURNS TRIGGER AS $$
    DECLARE
      v_user_id UUID;
      v_changes JSONB;
    BEGIN
      IF (TG_OP = 'UPDATE') THEN
        v_changes = jsonb_build_object('old', to_jsonb(OLD), 'new', to_jsonb(NEW));
        v_user_id = NEW.updated_by;
      ELSIF (TG_OP = 'INSERT') THEN
        v_changes = to_jsonb(NEW);
        v_user_id = NEW.created_by;
      ELSIF (TG_OP = 'DELETE') THEN
        v_changes = to_jsonb(OLD);
        v_user_id = OLD.updated_by;
      END IF;

      INSERT INTO audit_logs (
        action,
        entity_type,
        entity_id,
        user_id,
        changes,
        created_at,
        updated_at
      ) VALUES (
        TG_OP || ' ' || TG_TABLE_NAME,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        v_user_id,
        v_changes,
        NOW(),
        NOW()
      );

      RETURN COALESCE(NEW, OLD);
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Bind audit trigger
    op.execute("""
    CREATE TRIGGER audit_log_queues
    AFTER INSERT OR UPDATE OR DELETE ON queues
    FOR EACH ROW EXECUTE FUNCTION trigger_audit_log_actions();
    """)
    op.execute("""
    CREATE TRIGGER audit_log_scheduled_jobs
    AFTER INSERT OR UPDATE OR DELETE ON scheduled_jobs
    FOR EACH ROW EXECUTE FUNCTION trigger_audit_log_actions();
    """)

    # 6. Create Database Functions
    op.execute("""
    CREATE OR REPLACE FUNCTION enqueue_job(
        p_queue_id UUID,
        p_name VARCHAR,
        p_payload JSONB,
        p_priority INT DEFAULT 0,
        p_max_attempts INT DEFAULT 3,
        p_delay_seconds INT DEFAULT 0
    ) RETURNS UUID AS $$
    DECLARE
        v_job_id UUID;
    BEGIN
        INSERT INTO jobs (
            queue_id,
            name,
            payload,
            status,
            priority,
            scheduled_at,
            max_attempts,
            attempts,
            created_at,
            updated_at
        ) VALUES (
            p_queue_id,
            p_name,
            p_payload,
            'queued',
            p_priority,
            NOW() + (p_delay_seconds || ' seconds')::INTERVAL,
            p_max_attempts,
            0,
            NOW(),
            NOW()
        ) RETURNING id INTO v_job_id;

        RETURN v_job_id;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE OR REPLACE FUNCTION claim_job(
        p_worker_id UUID,
        p_queue_ids UUID[]
    ) RETURNS TABLE(
        job_id UUID,
        job_name VARCHAR,
        job_payload JSONB
    ) AS $$
    DECLARE
        v_claimed_id UUID;
    BEGIN
        UPDATE jobs
        SET 
            status = 'running',
            worker_id = p_worker_id,
            started_at = NOW(),
            attempts = attempts + 1,
            updated_at = NOW()
        WHERE id = (
            SELECT id 
            FROM jobs
            WHERE status = 'queued'
              AND queue_id = ANY(p_queue_ids)
              AND scheduled_at <= NOW()
              AND deleted_at IS NULL
            ORDER BY priority DESC, scheduled_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        RETURNING id INTO v_claimed_id;

        IF v_claimed_id IS NOT NULL THEN
            RETURN QUERY 
            SELECT id, name, payload 
            FROM jobs 
            WHERE id = v_claimed_id;
        END IF;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE OR REPLACE FUNCTION replay_dlq_job(
        p_job_id UUID
    ) RETURNS BOOLEAN AS $$
    DECLARE
        v_deleted_count INT;
    BEGIN
        DELETE FROM dead_letter_queues
        WHERE job_id = p_job_id;
        
        GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

        IF v_deleted_count > 0 THEN
            UPDATE jobs
            SET 
                status = 'queued',
                attempts = 0,
                worker_id = NULL,
                started_at = NULL,
                completed_at = NULL,
                scheduled_at = NOW(),
                updated_at = NOW()
            WHERE id = p_job_id;
            
            RETURN TRUE;
        ELSE
            RETURN FALSE;
        END IF;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # 7. Create Views
    op.execute("""
    CREATE OR REPLACE VIEW view_active_jobs_summary AS
    SELECT 
        q.id AS queue_id,
        q.name AS queue_name,
        COUNT(CASE WHEN j.status = 'queued' THEN 1 END) AS queued_count,
        COUNT(CASE WHEN j.status = 'running' THEN 1 END) AS running_count,
        COUNT(CASE WHEN j.status = 'failed' THEN 1 END) AS failed_count,
        COUNT(CASE WHEN j.status = 'success' THEN 1 END) AS success_count
    FROM queues q
    LEFT JOIN jobs j ON q.id = j.queue_id AND j.deleted_at IS NULL
    WHERE q.deleted_at IS NULL
    GROUP BY q.id, q.name;
    """)

    op.execute("""
    CREATE OR REPLACE VIEW view_queue_performance_metrics AS
    SELECT 
        q.id AS queue_id,
        q.name AS queue_name,
        COUNT(je.id) AS total_executions,
        ROUND(AVG(je.execution_time), 2) AS avg_execution_time_ms,
        ROUND(MAX(je.execution_time), 2) AS max_execution_time_ms,
        COUNT(CASE WHEN je.status = 'success' THEN 1 END) AS success_count,
        COUNT(CASE WHEN je.status = 'failed' THEN 1 END) AS failure_count,
        ROUND(
            (COUNT(CASE WHEN je.status = 'success' THEN 1 END)::NUMERIC / 
             NULLIF(COUNT(je.id), 0) * 100), 2
        ) AS success_rate_percent
    FROM queues q
    LEFT JOIN jobs j ON q.id = j.queue_id AND j.deleted_at IS NULL
    LEFT JOIN job_executions je ON j.id = je.job_id
    WHERE q.deleted_at IS NULL
    GROUP BY q.id, q.name;
    """)

    op.execute("""
    CREATE OR REPLACE VIEW view_worker_load_telemetry AS
    SELECT 
        w.id AS worker_id,
        w.hostname,
        w.ip_address,
        w.status AS worker_status,
        w.active_jobs,
        w.cpu_usage AS current_cpu,
        w.memory_usage AS current_memory,
        w.last_heartbeat,
        (w.last_heartbeat >= NOW() - INTERVAL '30 seconds') AS is_healthy
    FROM workers w
    WHERE w.deleted_at IS NULL;
    """)


def downgrade() -> None:
    # Drop Views
    op.execute("DROP VIEW IF EXISTS view_worker_load_telemetry CASCADE")
    op.execute("DROP VIEW IF EXISTS view_queue_performance_metrics CASCADE")
    op.execute("DROP VIEW IF EXISTS view_active_jobs_summary CASCADE")

    # Drop Functions
    op.execute("DROP FUNCTION IF EXISTS replay_dlq_job(UUID) CASCADE")
    op.execute("DROP FUNCTION IF EXISTS claim_job(UUID, UUID[]) CASCADE")
    op.execute("DROP FUNCTION IF EXISTS enqueue_job(UUID, VARCHAR, JSONB, INT, INT, INT) CASCADE")
    op.execute("DROP FUNCTION IF EXISTS trigger_audit_log_actions() CASCADE")
    op.execute("DROP FUNCTION IF EXISTS trigger_set_timestamp() CASCADE")

    # Drop Tables
    op.drop_table('refresh_tokens')
    op.drop_table('audit_logs')
    op.drop_table('notifications')
    op.drop_table('dead_letter_queues')
    op.drop_table('job_logs')
    op.drop_table('worker_heartbeats')
    op.drop_table('job_executions')
    op.drop_table('scheduled_jobs')
    op.drop_table('jobs')
    op.drop_table('workers')
    op.drop_table('queues')
    op.drop_table('retry_policies')
    op.drop_table('projects')
    op.drop_table('memberships')
    op.drop_table('organizations')
    op.drop_table('users')
