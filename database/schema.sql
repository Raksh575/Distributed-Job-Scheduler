-- ========================================================
-- DISTRIBUTED JOB SCHEDULER DATABASE SCHEMA
-- PostgreSQL 16 Production-Ready Relational Schema (3NF)
-- ========================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- DROP existing tables to ensure clean rebuild
DROP TABLE IF EXISTS refresh_tokens CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS dead_letter_queues CASCADE;
DROP TABLE IF EXISTS job_logs CASCADE;
DROP TABLE IF EXISTS worker_heartbeats CASCADE;
DROP TABLE IF EXISTS job_executions CASCADE;
DROP TABLE IF EXISTS scheduled_jobs CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;
DROP TABLE IF EXISTS workers CASCADE;
DROP TABLE IF EXISTS queues CASCADE;
DROP TABLE IF EXISTS retry_policies CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS memberships CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1. USERS
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    username VARCHAR(100) UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    phone VARCHAR(30),
    country VARCHAR(100),
    timezone VARCHAR(100) DEFAULT 'UTC' NOT NULL,
    profile_picture VARCHAR(512),
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    login_attempts INTEGER DEFAULT 0 NOT NULL,
    locked_until TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);

-- 2. ORGANIZATIONS
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    owner_id UUID NOT NULL,
    logo VARCHAR(512),
    plan VARCHAR(50) DEFAULT 'Free' NOT NULL,
    status VARCHAR(50) DEFAULT 'Active' NOT NULL,
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);

-- 3. MEMBERSHIPS
CREATE TABLE memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    role VARCHAR(50) NOT NULL,
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);

-- 4. PROJECTS
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    description TEXT,
    environment VARCHAR(50) DEFAULT 'Development' NOT NULL,
    status VARCHAR(50) DEFAULT 'Active' NOT NULL,
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);

-- 5. RETRY POLICIES
CREATE TABLE retry_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) DEFAULT 'Fixed Delay' NOT NULL,
    delay INTEGER DEFAULT 5 NOT NULL, -- in seconds
    max_attempts INTEGER DEFAULT 3 NOT NULL,
    backoff_factor NUMERIC(4,2) DEFAULT 2.00 NOT NULL,
    job_id UUID,
    queue_id UUID,
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);

-- 6. QUEUES
CREATE TABLE queues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    priority INTEGER DEFAULT 1 NOT NULL,
    concurrency_limit INTEGER DEFAULT 10 NOT NULL,
    retry_policy_id UUID,
    is_paused BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    rate_limit INTEGER DEFAULT 100 NOT NULL, -- requests per second
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);

-- 7. WORKERS
CREATE TABLE workers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE,
    hostname VARCHAR(255) NOT NULL UNIQUE,
    ip_address VARCHAR(45) NOT NULL,
    status VARCHAR(50) DEFAULT 'idle' NOT NULL,
    cpu_usage NUMERIC(5,2) DEFAULT 0.00 NOT NULL,
    memory_usage NUMERIC(5,2) DEFAULT 0.00 NOT NULL,
    active_jobs INTEGER DEFAULT 0 NOT NULL,
    system_info JSONB,
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);

-- 8. JOBS
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_id UUID NOT NULL,
    worker_id UUID,
    name VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    result JSONB,
    progress INTEGER DEFAULT 0 NOT NULL,
    error_message TEXT,
    status VARCHAR(50) DEFAULT 'queued' NOT NULL,
    priority INTEGER DEFAULT 0 NOT NULL,
    run_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    attempts INTEGER DEFAULT 0 NOT NULL,
    max_attempts INTEGER DEFAULT 3 NOT NULL,
    retries_count INTEGER DEFAULT 0 NOT NULL,
    max_retries INTEGER DEFAULT 3 NOT NULL,
    execution_timeout INTEGER DEFAULT 3600 NOT NULL, -- in seconds
    parent_id UUID,
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);

-- 9. SCHEDULED JOBS
CREATE TABLE scheduled_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(50) NOT NULL, -- 'cron', 'interval', 'date'
    cron_expression VARCHAR(255),
    interval_seconds INTEGER,
    target_queue_id UUID NOT NULL,
    job_name VARCHAR(255) NOT NULL,
    job_payload JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    next_run_time TIMESTAMP WITH TIME ZONE,
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);

-- 10. JOB EXECUTIONS
CREATE TABLE job_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    worker_id UUID,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    finished_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    execution_time INTEGER, -- in milliseconds
    duration_ms INTEGER, -- in milliseconds
    cpu_usage NUMERIC(5,2) DEFAULT 0.00 NOT NULL,
    memory_usage NUMERIC(5,2) DEFAULT 0.00 NOT NULL,
    response JSONB,
    error_message TEXT,
    stack_trace TEXT,
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);

-- 11. WORKER HEARTBEATS
CREATE TABLE worker_heartbeats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id UUID NOT NULL,
    heartbeat_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    status VARCHAR(50),
    cpu NUMERIC(5,2) NOT NULL,
    memory NUMERIC(5,2) NOT NULL,
    disk NUMERIC(5,2) NOT NULL,
    active_jobs_count INTEGER DEFAULT 0 NOT NULL,
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);

-- 12. JOB LOGS
CREATE TABLE job_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_execution_id UUID,
    job_id UUID NOT NULL,
    log_level VARCHAR(20) DEFAULT 'INFO' NOT NULL,
    level VARCHAR(20) DEFAULT 'info' NOT NULL,
    message TEXT NOT NULL,
    stack_trace TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);

-- 13. DEAD LETTER QUEUE
CREATE TABLE dead_letter_queues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    failed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    reason TEXT NOT NULL,
    payload JSONB NOT NULL,
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);

-- 14. NOTIFICATIONS
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    read_status BOOLEAN DEFAULT FALSE NOT NULL,
    organization_id UUID,
    sent_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);

-- 15. AUDIT LOGS
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID,
    user_id UUID,
    changes JSONB,
    ip_address VARCHAR(45),
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);

-- 16. REFRESH TOKENS
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    token VARCHAR(512) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    device_info VARCHAR(255),
    token_family UUID,
    
    -- Common Columns
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID,
    version INTEGER DEFAULT 1 NOT NULL
);
