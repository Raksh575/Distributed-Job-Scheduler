-- ========================================================
-- DISTRIBUTED JOB SCHEDULER VIEWS
-- ========================================================

-- 1. VIEW: ACTIVE JOBS SUMMARY
-- Shows currently executing, queued, and waiting jobs grouped by queues.
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

-- 2. VIEW: QUEUE PERFORMANCE METRICS
-- Analyzes execution durations, failure rates, and success rates across all queues.
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

-- 3. VIEW: WORKER LOAD TELEMETRY
-- Provides worker health details, recent heartbeats, and average resource utilization.
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
