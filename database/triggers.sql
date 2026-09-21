-- ========================================================
-- DISTRIBUTED JOB SCHEDULER TRIGGERS
-- ========================================================

-- Generic function to update the updated_at timestamp automatically on UPDATE
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all tables
CREATE TRIGGER set_timestamp_users
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_organizations
BEFORE UPDATE ON organizations
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_memberships
BEFORE UPDATE ON memberships
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_projects
BEFORE UPDATE ON projects
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_retry_policies
BEFORE UPDATE ON retry_policies
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_queues
BEFORE UPDATE ON queues
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_workers
BEFORE UPDATE ON workers
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_jobs
BEFORE UPDATE ON jobs
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_scheduled_jobs
BEFORE UPDATE ON scheduled_jobs
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_job_executions
BEFORE UPDATE ON job_executions
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_worker_heartbeats
BEFORE UPDATE ON worker_heartbeats
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_job_logs
BEFORE UPDATE ON job_logs
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_dead_letter_queues
BEFORE UPDATE ON dead_letter_queues
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_notifications
BEFORE UPDATE ON notifications
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_audit_logs
BEFORE UPDATE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

CREATE TRIGGER set_timestamp_refresh_tokens
BEFORE UPDATE ON refresh_tokens
FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();


-- Trigger function to automatically register audit logs for critical database actions
CREATE OR REPLACE FUNCTION trigger_audit_log_actions()
RETURNS TRIGGER AS $$
DECLARE
  v_user_id UUID;
  v_changes JSONB;
BEGIN
  -- Attempt to discover action changes and associated user
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

-- Bind audit trigger to high-importance configuration changes
CREATE TRIGGER audit_log_queues
AFTER INSERT OR UPDATE OR DELETE ON queues
FOR EACH ROW EXECUTE FUNCTION trigger_audit_log_actions();

CREATE TRIGGER audit_log_scheduled_jobs
AFTER INSERT OR UPDATE OR DELETE ON scheduled_jobs
FOR EACH ROW EXECUTE FUNCTION trigger_audit_log_actions();
