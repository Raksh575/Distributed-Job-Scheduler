-- ========================================================
-- DISTRIBUTED JOB SCHEDULER CONSTRAINTS & FOREIGN KEYS
-- ========================================================

-- 1. FOREIGN KEYS

-- Audit self-references on Users
ALTER TABLE users ADD CONSTRAINT fk_users_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE users ADD CONSTRAINT fk_users_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- Organizations References
ALTER TABLE organizations ADD CONSTRAINT fk_organizations_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE organizations ADD CONSTRAINT fk_organizations_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE organizations ADD CONSTRAINT fk_organizations_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- Memberships References
ALTER TABLE memberships ADD CONSTRAINT fk_memberships_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE memberships ADD CONSTRAINT fk_memberships_org FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;
ALTER TABLE memberships ADD CONSTRAINT fk_memberships_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE memberships ADD CONSTRAINT fk_memberships_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- Projects References
ALTER TABLE projects ADD CONSTRAINT fk_projects_org FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;
ALTER TABLE projects ADD CONSTRAINT fk_projects_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE projects ADD CONSTRAINT fk_projects_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- Retry Policies References
ALTER TABLE retry_policies ADD CONSTRAINT fk_retry_policies_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE retry_policies ADD CONSTRAINT fk_retry_policies_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- Queues References
ALTER TABLE queues ADD CONSTRAINT fk_queues_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
ALTER TABLE queues ADD CONSTRAINT fk_queues_retry_policy FOREIGN KEY (retry_policy_id) REFERENCES retry_policies(id) ON DELETE SET NULL;
ALTER TABLE queues ADD CONSTRAINT fk_queues_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE queues ADD CONSTRAINT fk_queues_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- Workers References
ALTER TABLE workers ADD CONSTRAINT fk_workers_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE workers ADD CONSTRAINT fk_workers_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- Jobs References
ALTER TABLE jobs ADD CONSTRAINT fk_jobs_queue FOREIGN KEY (queue_id) REFERENCES queues(id) ON DELETE CASCADE;
ALTER TABLE jobs ADD CONSTRAINT fk_jobs_worker FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE SET NULL;
ALTER TABLE jobs ADD CONSTRAINT fk_jobs_parent FOREIGN KEY (parent_id) REFERENCES jobs(id) ON DELETE SET NULL;
ALTER TABLE jobs ADD CONSTRAINT fk_jobs_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE jobs ADD CONSTRAINT fk_jobs_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- Scheduled Jobs References
ALTER TABLE scheduled_jobs ADD CONSTRAINT fk_scheduled_jobs_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
ALTER TABLE scheduled_jobs ADD CONSTRAINT fk_scheduled_jobs_queue FOREIGN KEY (target_queue_id) REFERENCES queues(id) ON DELETE CASCADE;
ALTER TABLE scheduled_jobs ADD CONSTRAINT fk_scheduled_jobs_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE scheduled_jobs ADD CONSTRAINT fk_scheduled_jobs_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- Job Executions References
ALTER TABLE job_executions ADD CONSTRAINT fk_job_executions_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;
ALTER TABLE job_executions ADD CONSTRAINT fk_job_executions_worker FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE SET NULL;
ALTER TABLE job_executions ADD CONSTRAINT fk_job_executions_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE job_executions ADD CONSTRAINT fk_job_executions_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- Worker Heartbeats References
ALTER TABLE worker_heartbeats ADD CONSTRAINT fk_worker_heartbeats_worker FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE;
ALTER TABLE worker_heartbeats ADD CONSTRAINT fk_worker_heartbeats_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE worker_heartbeats ADD CONSTRAINT fk_worker_heartbeats_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- Job Logs References
ALTER TABLE job_logs ADD CONSTRAINT fk_job_logs_execution FOREIGN KEY (job_execution_id) REFERENCES job_executions(id) ON DELETE CASCADE;
ALTER TABLE job_logs ADD CONSTRAINT fk_job_logs_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;
ALTER TABLE job_logs ADD CONSTRAINT fk_job_logs_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE job_logs ADD CONSTRAINT fk_job_logs_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- Dead Letter Queue References
ALTER TABLE dead_letter_queues ADD CONSTRAINT fk_dead_letter_queues_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;
ALTER TABLE dead_letter_queues ADD CONSTRAINT fk_dead_letter_queues_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE dead_letter_queues ADD CONSTRAINT fk_dead_letter_queues_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- Notifications References
ALTER TABLE notifications ADD CONSTRAINT fk_notifications_org FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;
ALTER TABLE notifications ADD CONSTRAINT fk_notifications_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE notifications ADD CONSTRAINT fk_notifications_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- Audit Logs References
ALTER TABLE audit_logs ADD CONSTRAINT fk_audit_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE audit_logs ADD CONSTRAINT fk_audit_logs_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE audit_logs ADD CONSTRAINT fk_audit_logs_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;

-- Refresh Tokens References
ALTER TABLE refresh_tokens ADD CONSTRAINT fk_refresh_tokens_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE refresh_tokens ADD CONSTRAINT fk_refresh_tokens_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE refresh_tokens ADD CONSTRAINT fk_refresh_tokens_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;


-- 2. UNIQUE CONSTRAINTS
ALTER TABLE memberships ADD CONSTRAINT uq_user_organization UNIQUE (user_id, organization_id);
ALTER TABLE projects ADD CONSTRAINT uq_project_name UNIQUE (organization_id, name);
ALTER TABLE queues ADD CONSTRAINT uq_queue_name UNIQUE (project_id, name);
ALTER TABLE scheduled_jobs ADD CONSTRAINT uq_scheduled_job_name UNIQUE (project_id, name);


-- 3. CHECK CONSTRAINTS

-- Email and phone regex format checks
ALTER TABLE users ADD CONSTRAINT check_user_email_format CHECK (email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$');

-- Plan constraints
ALTER TABLE organizations ADD CONSTRAINT check_organization_plan CHECK (plan IN ('Free', 'Pro', 'Enterprise'));
ALTER TABLE organizations ADD CONSTRAINT check_organization_status CHECK (status IN ('Active', 'Suspended'));

-- Project environment and status checks
ALTER TABLE projects ADD CONSTRAINT check_projects_environment CHECK (environment IN ('Production', 'Staging', 'Development'));
ALTER TABLE projects ADD CONSTRAINT check_projects_status CHECK (status IN ('Active', 'Inactive'));

-- Membership Roles check
ALTER TABLE memberships ADD CONSTRAINT check_memberships_role CHECK (role IN ('Owner', 'Admin', 'Developer', 'Viewer'));

-- Queues bounds
ALTER TABLE queues ADD CONSTRAINT check_queues_priority CHECK (priority >= 0);
ALTER TABLE queues ADD CONSTRAINT check_queues_concurrency CHECK (concurrency_limit >= 1);
ALTER TABLE queues ADD CONSTRAINT check_queues_rate_limit CHECK (rate_limit >= 1);

-- Workers status and usage bounds
ALTER TABLE workers ADD CONSTRAINT check_workers_status CHECK (status IN ('active', 'idle', 'offline'));
ALTER TABLE workers ADD CONSTRAINT check_workers_cpu CHECK (cpu_usage BETWEEN 0.00 AND 100.00);
ALTER TABLE workers ADD CONSTRAINT check_workers_mem CHECK (memory_usage BETWEEN 0.00 AND 100.00);
ALTER TABLE workers ADD CONSTRAINT check_workers_active_jobs CHECK (active_jobs >= 0);

-- Jobs status and priorities bounds
ALTER TABLE jobs ADD CONSTRAINT check_jobs_status CHECK (status IN ('queued', 'running', 'success', 'failed', 'cancelled'));
ALTER TABLE jobs ADD CONSTRAINT check_jobs_priority CHECK (priority >= 0);
ALTER TABLE jobs ADD CONSTRAINT check_jobs_attempts CHECK (attempts >= 0 AND attempts <= max_attempts);
ALTER TABLE jobs ADD CONSTRAINT check_jobs_max_attempts CHECK (max_attempts >= 1);
ALTER TABLE jobs ADD CONSTRAINT check_jobs_timeout CHECK (execution_timeout >= 1);

-- Scheduled jobs trigger types check
ALTER TABLE scheduled_jobs ADD CONSTRAINT check_scheduled_jobs_trigger CHECK (trigger_type IN ('cron', 'interval', 'date'));
ALTER TABLE scheduled_jobs ADD CONSTRAINT check_scheduled_interval CHECK (interval_seconds IS NULL OR interval_seconds >= 1);

-- Job executions status and CPU/memory bounds
ALTER TABLE job_executions ADD CONSTRAINT check_job_executions_status CHECK (status IN ('success', 'failed', 'running'));
ALTER TABLE job_executions ADD CONSTRAINT check_job_executions_cpu CHECK (cpu_usage BETWEEN 0.00 AND 100.00);
ALTER TABLE job_executions ADD CONSTRAINT check_job_executions_mem CHECK (memory_usage BETWEEN 0.00 AND 100.00);
ALTER TABLE job_executions ADD CONSTRAINT check_job_executions_time CHECK (execution_time IS NULL OR execution_time >= 0);

-- Worker heartbeats CPU/memory/disk bounds
ALTER TABLE worker_heartbeats ADD CONSTRAINT check_worker_heartbeats_cpu CHECK (cpu BETWEEN 0.00 AND 100.00);
ALTER TABLE worker_heartbeats ADD CONSTRAINT check_worker_heartbeats_mem CHECK (memory BETWEEN 0.00 AND 100.00);
ALTER TABLE worker_heartbeats ADD CONSTRAINT check_worker_heartbeats_disk CHECK (disk BETWEEN 0.00 AND 100.00);

-- Retry Policies types check
ALTER TABLE retry_policies ADD CONSTRAINT check_retry_policies_type CHECK (type IN ('Fixed Delay', 'Linear Backoff', 'Exponential Backoff'));
ALTER TABLE retry_policies ADD CONSTRAINT check_retry_policies_delay CHECK (delay >= 1);
ALTER TABLE retry_policies ADD CONSTRAINT check_retry_policies_max CHECK (max_attempts >= 1);
ALTER TABLE retry_policies ADD CONSTRAINT check_retry_policies_backoff CHECK (backoff_factor >= 1.00);

-- Job logs log levels check
ALTER TABLE job_logs ADD CONSTRAINT check_job_logs_level CHECK (log_level IN ('INFO', 'WARN', 'ERROR', 'DEBUG'));

-- Notifications types check
ALTER TABLE notifications ADD CONSTRAINT check_notifications_type CHECK (type IN ('System', 'Alert', 'Slack', 'Email'));
