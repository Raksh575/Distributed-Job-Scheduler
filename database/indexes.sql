-- ========================================================
-- DISTRIBUTED JOB SCHEDULER PERFORMANCE INDEXES
-- ========================================================

-- 1. FOREIGN KEY INDEXES (To accelerate JOIN performance)

CREATE INDEX idx_users_created_by ON users(created_by);
CREATE INDEX idx_users_updated_by ON users(updated_by);

CREATE INDEX idx_organizations_owner ON organizations(owner_id);
CREATE INDEX idx_organizations_created_by ON organizations(created_by);
CREATE INDEX idx_organizations_updated_by ON organizations(updated_by);

CREATE INDEX idx_memberships_user ON memberships(user_id);
CREATE INDEX idx_memberships_org ON memberships(organization_id);
CREATE INDEX idx_memberships_created_by ON memberships(created_by);
CREATE INDEX idx_memberships_updated_by ON memberships(updated_by);

CREATE INDEX idx_projects_org ON projects(organization_id);
CREATE INDEX idx_projects_created_by ON projects(created_by);
CREATE INDEX idx_projects_updated_by ON projects(updated_by);

CREATE INDEX idx_retry_policies_created_by ON retry_policies(created_by);
CREATE INDEX idx_retry_policies_updated_by ON retry_policies(updated_by);

CREATE INDEX idx_queues_project ON queues(project_id);
CREATE INDEX idx_queues_retry_policy ON queues(retry_policy_id);
CREATE INDEX idx_queues_created_by ON queues(created_by);
CREATE INDEX idx_queues_updated_by ON queues(updated_by);

CREATE INDEX idx_workers_created_by ON workers(created_by);
CREATE INDEX idx_workers_updated_by ON workers(updated_by);

CREATE INDEX idx_jobs_queue ON jobs(queue_id);
CREATE INDEX idx_jobs_worker ON jobs(worker_id);
CREATE INDEX idx_jobs_parent ON jobs(parent_id);
CREATE INDEX idx_jobs_created_by ON jobs(created_by);
CREATE INDEX idx_jobs_updated_by ON jobs(updated_by);

CREATE INDEX idx_scheduled_jobs_project ON scheduled_jobs(project_id);
CREATE INDEX idx_scheduled_jobs_queue ON scheduled_jobs(target_queue_id);
CREATE INDEX idx_scheduled_jobs_created_by ON scheduled_jobs(created_by);
CREATE INDEX idx_scheduled_jobs_updated_by ON scheduled_jobs(updated_by);

CREATE INDEX idx_job_executions_job ON job_executions(job_id);
CREATE INDEX idx_job_executions_worker ON job_executions(worker_id);
CREATE INDEX idx_job_executions_created_by ON job_executions(created_by);
CREATE INDEX idx_job_executions_updated_by ON job_executions(updated_by);

CREATE INDEX idx_worker_heartbeats_worker ON worker_heartbeats(worker_id);
CREATE INDEX idx_worker_heartbeats_created_by ON worker_heartbeats(created_by);
CREATE INDEX idx_worker_heartbeats_updated_by ON worker_heartbeats(updated_by);

CREATE INDEX idx_job_logs_execution ON job_logs(job_execution_id);
CREATE INDEX idx_job_logs_job ON job_logs(job_id);
CREATE INDEX idx_job_logs_created_by ON job_logs(created_by);
CREATE INDEX idx_job_logs_updated_by ON job_logs(updated_by);

CREATE INDEX idx_dead_letter_queues_job ON dead_letter_queues(job_id);
CREATE INDEX idx_dead_letter_queues_created_by ON dead_letter_queues(created_by);
CREATE INDEX idx_dead_letter_queues_updated_by ON dead_letter_queues(updated_by);

CREATE INDEX idx_notifications_org ON notifications(organization_id);
CREATE INDEX idx_notifications_created_by ON notifications(created_by);
CREATE INDEX idx_notifications_updated_by ON notifications(updated_by);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_by ON audit_logs(created_by);
CREATE INDEX idx_audit_logs_updated_by ON audit_logs(updated_by);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_created_by ON refresh_tokens(created_by);
CREATE INDEX idx_refresh_tokens_updated_by ON refresh_tokens(updated_by);


-- 2. COMPOSITE & OPTIMIZATION INDEXES

-- Queue Processing Optimization (Polled constantly by Scheduler & Workers)
-- Helps locate ready-to-run high priority jobs quickly
CREATE INDEX idx_jobs_claim_optimizer ON jobs(status, scheduled_at, priority DESC) 
WHERE status = 'queued' AND deleted_at IS NULL;

-- Worker Availability Optimization
CREATE INDEX idx_workers_heartbeat_status ON workers(status, last_heartbeat DESC)
WHERE deleted_at IS NULL;

-- Scheduled Jobs Trigger Optimization
CREATE INDEX idx_scheduled_jobs_trigger_opt ON scheduled_jobs(is_active, next_run_time ASC)
WHERE is_active = TRUE AND deleted_at IS NULL;

-- Log Search Performance Index
CREATE INDEX idx_job_logs_search ON job_logs(job_id, log_level, created_at DESC);

-- Audit Trail Verification Index
CREATE INDEX idx_audit_logs_tracking ON audit_logs(entity_type, entity_id, created_at DESC);
