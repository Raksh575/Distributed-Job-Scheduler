-- Mock Data Seed Script for Distributed Job Scheduler

-- Disable constraints temporarily to allow arbitrary insert order
SET session_replication_role = 'replica';

-- 1. Users
-- Password for both users is: "password123"
INSERT INTO users (id, email, hashed_password, first_name, last_name, username, is_verified, is_active, created_at, updated_at, version, login_attempts) 
VALUES 
('11111111-1111-1111-1111-111111111111', 'admin@example.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Admin', 'User', 'admin', true, true, NOW(), NOW(), 1, 0),
('22222222-2222-2222-2222-222222222222', 'developer@example.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Dev', 'Eloper', 'dev1', true, true, NOW(), NOW(), 1, 0);

-- 2. Organizations
INSERT INTO organizations (id, name, slug, owner_id, plan, status, created_at, updated_at, version)
VALUES 
('33333333-3333-3333-3333-333333333333', 'Acme Corp', 'acme-corp', '11111111-1111-1111-1111-111111111111', 'Enterprise', 'Active', NOW(), NOW(), 1),
('44444444-4444-4444-4444-444444444444', 'Startup Inc', 'startup-inc', '22222222-2222-2222-2222-222222222222', 'Free', 'Active', NOW(), NOW(), 1);

-- 3. Memberships
INSERT INTO memberships (id, user_id, organization_id, role, created_at, updated_at, version)
VALUES 
('55555555-5555-5555-5555-555555555555', '11111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333', 'Super Admin', NOW(), NOW(), 1),
('66666666-6666-6666-6666-666666666666', '22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333', 'Developer', NOW(), NOW(), 1),
('77777777-7777-7777-7777-777777777777', '22222222-2222-2222-2222-222222222222', '44444444-4444-4444-4444-444444444444', 'Super Admin', NOW(), NOW(), 1);

-- 4. Projects
INSERT INTO projects (id, organization_id, name, slug, environment, status, created_at, updated_at, version)
VALUES 
('88888888-8888-8888-8888-888888888888', '33333333-3333-3333-3333-333333333333', 'Data Pipeline', 'data-pipeline', 'production', 'active', NOW(), NOW(), 1),
('99999999-9999-9999-9999-999999999999', '33333333-3333-3333-3333-333333333333', 'Email Service', 'email-service', 'production', 'active', NOW(), NOW(), 1);

-- 5. Queues
INSERT INTO queues (id, project_id, name, priority, concurrency_limit, rate_limit, is_active, is_paused, created_at, updated_at, version)
VALUES 
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '88888888-8888-8888-8888-888888888888', 'high-priority-etl', 100, 50, 100, true, false, NOW(), NOW(), 1),
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '99999999-9999-9999-9999-999999999999', 'send-emails', 50, 10, NULL, true, false, NOW(), NOW(), 1);

-- 6. Jobs
INSERT INTO jobs (id, queue_id, name, status, payload, priority, max_retries, retries_count, progress, created_at, updated_at, run_at, version)
VALUES 
('cccccccc-cccc-cccc-cccc-cccccccccccc', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'extract-data', 'queued', '{"source": "db1", "target": "s3"}', 100, 3, 0, 0, NOW(), NOW(), NOW(), 1),
('dddddddd-dddd-dddd-dddd-dddddddddddd', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'transform-data', 'running', '{"source": "s3", "format": "parquet"}', 100, 3, 0, 45, NOW(), NOW(), NOW(), 1),
('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'send-welcome-email', 'success', '{"user_id": 123}', 50, 3, 0, 100, NOW() - INTERVAL '1 hour', NOW() - INTERVAL '59 minutes', NOW() - INTERVAL '1 hour', 1),
('ffffffff-ffff-ffff-ffff-ffffffffffff', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'send-invoice', 'failed', '{"invoice_id": 987}', 50, 3, 3, 10, NOW() - INTERVAL '2 days', NOW(), NOW() - INTERVAL '2 days', 1);

-- 7. Workers
INSERT INTO workers (id, name, ip_address, status, system_info, last_heartbeat, created_at, updated_at, version)
VALUES 
('00000001-0000-0000-0000-000000000000', 'worker-node-1', '192.168.1.10', 'active', '{"os": "linux", "cores": 8, "memory_gb": 16}', NOW(), NOW() - INTERVAL '1 day', NOW(), 1),
('00000002-0000-0000-0000-000000000000', 'worker-node-2', '192.168.1.11', 'idle', '{"os": "linux", "cores": 4, "memory_gb": 8}', NOW() - INTERVAL '5 minutes', NOW() - INTERVAL '1 day', NOW(), 1),
('00000003-0000-0000-0000-000000000000', 'worker-node-3', '192.168.1.12', 'offline', '{"os": "windows", "cores": 8, "memory_gb": 32}', NOW() - INTERVAL '2 days', NOW() - INTERVAL '10 days', NOW() - INTERVAL '2 days', 1);

-- 8. Worker Heartbeats
INSERT INTO worker_heartbeats (id, worker_id, status, cpu_usage, memory_usage, active_jobs_count, created_at, updated_at, version)
VALUES 
('10000000-0000-0000-0000-000000000001', '00000001-0000-0000-0000-000000000000', 'active', 45.5, 60.2, 5, NOW(), NOW(), 1),
('20000000-0000-0000-0000-000000000002', '00000002-0000-0000-0000-000000000000', 'idle', 5.0, 20.0, 0, NOW(), NOW(), 1);

-- 9. Dead Letter Queue
INSERT INTO dead_letter_queues (id, job_id, reason, failed_at, created_at, updated_at, version)
VALUES 
('30000000-0000-0000-0000-000000000003', 'ffffffff-ffff-ffff-ffff-ffffffffffff', 'SMTP Connection Timeout after 3 retries', NOW(), NOW(), NOW(), 1);

-- Re-enable constraints
SET session_replication_role = 'origin';
