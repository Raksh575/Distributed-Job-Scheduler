-- ========================================================
-- DISTRIBUTED JOB SCHEDULER SEED DATA
-- ========================================================

-- Define constant UUIDs to guarantee reference integrity across inserts
DO $$
DECLARE
    -- Users
    v_user_owner UUID := '90a36e6e-cb91-4974-bc5c-bf7d5f0e1371';
    v_user_admin UUID := 'b051b8fc-c52b-42fa-b7bd-b65fb5dfa14a';
    v_user_dev   UUID := 'c1f71a9a-5b12-4fb2-b7e6-14bc125f190e';
    
    -- Organizations
    v_org_acme   UUID := '10bf5555-d36c-4874-954d-17631853d999';
    
    -- Projects
    v_proj_core  UUID := '20bf6666-e82c-4749-8fa9-27632853e000';
    
    -- Retry Policies
    v_policy_exp UUID := '30bf7777-f93c-4874-bc5c-bf7d5f0e1111';
    v_policy_fix UUID := '40bf8888-0012-4fb2-b7e6-14bc125f2222';
    
    -- Queues
    v_queue_high UUID := '50bf9999-1123-42fa-b7bd-b65fb5df3333';
    v_queue_low  UUID := '60bfaaaa-2234-4974-bc5c-bf7d5f0e4444';
    
    -- Workers
    v_worker_1   UUID := '70bfbbbb-3345-4fb2-b7e6-14bc125f5555';
    v_worker_2   UUID := '80bfcccc-4456-42fa-b7bd-b65fb5df6666';
BEGIN

    -- 1. SEED USERS
    -- hashed_password matches pbkdf2_sha256 format for "Password123!"
    INSERT INTO users (id, first_name, last_name, username, full_name, email, hashed_password, country, timezone, is_verified, is_active)
    VALUES 
    (v_user_owner, 'John', 'Doe', 'johndoe', 'John Doe', 'owner@acme.com', '$2b$12$Z0Gf9n3F4m459Z.qf9m4eu/X5vY4.gZ4v.gZ4v.gZ4v.gZ4v.gZ4v', 'United States', 'America/New_York', TRUE, TRUE),
    (v_user_admin, 'Alice', 'Smith', 'alicesmith', 'Alice Smith', 'admin@acme.com', '$2b$12$Z0Gf9n3F4m459Z.qf9m4eu/X5vY4.gZ4v.gZ4v.gZ4v.gZ4v.gZ4v', 'Canada', 'America/Toronto', TRUE, TRUE),
    (v_user_dev, 'Bob', 'Johnson', 'bobjohnson', 'Bob Johnson', 'dev@acme.com', '$2b$12$Z0Gf9n3F4m459Z.qf9m4eu/X5vY4.gZ4v.gZ4v.gZ4v.gZ4v.gZ4v', 'United Kingdom', 'Europe/London', TRUE, TRUE)
    ON CONFLICT (username) DO NOTHING;

    -- 2. SEED ORGANIZATIONS
    INSERT INTO organizations (id, name, slug, description, owner_id, plan, status)
    VALUES 
    (v_org_acme, 'Acme Corporation', 'acme-corp', 'Global provider of innovative solutions.', v_user_owner, 'Enterprise', 'Active')
    ON CONFLICT (slug) DO NOTHING;

    -- 3. SEED MEMBERSHIPS
    INSERT INTO memberships (user_id, organization_id, role)
    VALUES 
    (v_user_owner, v_org_acme, 'Owner'),
    (v_user_admin, v_org_acme, 'Admin'),
    (v_user_dev, v_org_acme, 'Developer')
    ON CONFLICT (user_id, organization_id) DO NOTHING;

    -- 4. SEED PROJECTS
    INSERT INTO projects (id, organization_id, name, description, environment, status)
    VALUES 
    (v_proj_core, v_org_acme, 'Core Production Scheduler', 'Handles all back-end jobs and billing workflows.', 'Production', 'Active')
    ON CONFLICT (organization_id, name) DO NOTHING;

    -- 5. SEED RETRY POLICIES
    INSERT INTO retry_policies (id, name, type, delay, max_attempts, backoff_factor)
    VALUES 
    (v_policy_exp, 'Exponential Backoff Policy', 'Exponential Backoff', 5, 5, 2.00),
    (v_policy_fix, 'Fixed Delay Policy', 'Fixed Delay', 10, 3, 1.00);

    -- 6. SEED QUEUES
    INSERT INTO queues (id, project_id, name, priority, concurrency_limit, retry_policy_id, is_paused, rate_limit)
    VALUES 
    (v_queue_high, v_proj_core, 'billing-transactions', 10, 20, v_policy_exp, FALSE, 250),
    (v_queue_low, v_proj_core, 'email-delivery', 3, 50, v_policy_fix, FALSE, 50)
    ON CONFLICT (project_id, name) DO NOTHING;

    -- 7. SEED WORKERS
    INSERT INTO workers (id, hostname, ip_address, status, cpu_usage, memory_usage, active_jobs, last_heartbeat)
    VALUES 
    (v_worker_1, 'worker-us-east-1', '10.0.1.5', 'active', 42.50, 68.20, 4, NOW()),
    (v_worker_2, 'worker-us-east-2', '10.0.1.6', 'idle', 5.10, 12.40, 0, NOW())
    ON CONFLICT (hostname) DO NOTHING;

    -- 8. SEED WORKER HEARTBEATS
    INSERT INTO worker_heartbeats (worker_id, cpu, memory, disk, heartbeat_time)
    VALUES 
    (v_worker_1, 45.20, 65.50, 28.10, NOW() - INTERVAL '1 minute'),
    (v_worker_1, 42.50, 68.20, 28.10, NOW()),
    (v_worker_2, 5.10, 12.40, 10.50, NOW());

    -- 9. SEED JOBS
    -- Completed Job
    INSERT INTO jobs (id, queue_id, worker_id, name, payload, status, priority, scheduled_at, started_at, completed_at, attempts, max_attempts)
    VALUES 
    ('e1fa5b12-b7bd-42fa-b7bd-b65fb5dfa001', v_queue_high, v_worker_1, 'charge-customer-invoice', '{"customer_id": "cust_999", "amount": 1500}', 'success', 10, NOW() - INTERVAL '10 minutes', NOW() - INTERVAL '9 minutes 58 seconds', NOW() - INTERVAL '9 minutes 55 seconds', 1, 5);

    -- Running Job
    INSERT INTO jobs (id, queue_id, worker_id, name, payload, status, priority, scheduled_at, started_at, attempts, max_attempts)
    VALUES 
    ('e2fa5b12-b7bd-42fa-b7bd-b65fb5dfa002', v_queue_high, v_worker_1, 'sync-ledger-transactions', '{"batch_id": "batch_283"}', 'running', 8, NOW() - INTERVAL '1 minute', NOW() - INTERVAL '58 seconds', 1, 5);

    -- Queued Job
    INSERT INTO jobs (id, queue_id, name, payload, status, priority, scheduled_at, attempts, max_attempts)
    VALUES 
    ('e3fa5b12-b7bd-42fa-b7bd-b65fb5dfa003', v_queue_low, 'send-welcome-emails', '{"user_email": "newuser@gmail.com"}', 'queued', 3, NOW() + INTERVAL '5 minutes', 0, 3);

    -- Failed Job (moved to DLQ)
    INSERT INTO jobs (id, queue_id, name, payload, status, priority, scheduled_at, attempts, max_attempts)
    VALUES 
    ('e4fa5b12-b7bd-42fa-b7bd-b65fb5dfa004', v_queue_high, 'process-video-transcoding', '{"source_url": "s3://bucket/video.mp4"}', 'failed', 5, NOW() - INTERVAL '1 hour', 5, 5);

    -- 10. SEED JOB EXECUTIONS
    INSERT INTO job_executions (job_id, worker_id, status, started_at, finished_at, execution_time, cpu_usage, memory_usage, response)
    VALUES 
    ('e1fa5b12-b7bd-42fa-b7bd-b65fb5dfa001', v_worker_1, 'success', NOW() - INTERVAL '9 minutes 58 seconds', NOW() - INTERVAL '9 minutes 55 seconds', 3000, 15.50, 42.10, '{"transaction_id": "tx_abc123", "status": "approved"}');

    INSERT INTO job_executions (job_id, worker_id, status, started_at, finished_at, execution_time, cpu_usage, memory_usage, error_message, stack_trace)
    VALUES 
    ('e4fa5b12-b7bd-42fa-b7bd-b65fb5dfa004', v_worker_1, 'failed', NOW() - INTERVAL '1 hour', NOW() - INTERVAL '59 minutes', 60000, 95.00, 90.00, 'Transcoding timeout exceeded limits', 'Traceback (most recent call last):\n  File "worker.py", line 123, in run\n    raise TimeoutError("Limits exceeded")');

    -- 11. SEED JOB LOGS
    INSERT INTO job_logs (job_execution_id, job_id, log_level, message)
    VALUES 
    (NULL, 'e1fa5b12-b7bd-42fa-b7bd-b65fb5dfa001', 'INFO', 'Job initialized.'),
    (NULL, 'e1fa5b12-b7bd-42fa-b7bd-b65fb5dfa001', 'INFO', 'Connecting to payment provider Gateway...'),
    (NULL, 'e1fa5b12-b7bd-42fa-b7bd-b65fb5dfa001', 'INFO', 'Payment processed successfully.');

    -- 12. SEED DEAD LETTER QUEUE
    INSERT INTO dead_letter_queues (job_id, failed_at, reason, payload)
    VALUES 
    ('e4fa5b12-b7bd-42fa-b7bd-b65fb5dfa004', NOW() - INTERVAL '59 minutes', 'Transcoding timeout exceeded limits', '{"source_url": "s3://bucket/video.mp4"}');

    -- 13. SEED SCHEDULED JOBS
    INSERT INTO scheduled_jobs (project_id, name, trigger_type, cron_expression, target_queue_id, job_name, job_payload, is_active, next_run_time)
    VALUES 
    (v_proj_core, 'Daily Accounts Reconciliation', 'cron', '0 0 * * *', v_queue_high, 'reconcile-accounts', '{"dry_run": false}', TRUE, NOW() + INTERVAL '12 hours');

    -- 14. SEED NOTIFICATIONS
    INSERT INTO notifications (title, message, type, read_status, organization_id)
    VALUES 
    ('Worker Offline Alert', 'Worker worker-us-east-2 heartbeat lost for over 60 seconds.', 'Alert', FALSE, v_org_acme);

    -- 15. SEED AUDIT LOGS
    INSERT INTO audit_logs (action, entity_type, entity_id, user_id, changes, ip_address)
    VALUES 
    ('Queue Created', 'queues', v_queue_high, v_user_owner, '{"name": "billing-transactions"}', '192.168.1.50');

END $$;
