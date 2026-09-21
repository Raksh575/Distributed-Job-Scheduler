-- ========================================================
-- DISTRIBUTED JOB SCHEDULER FUNCTIONS & PROCEDURES
-- ========================================================

-- 1. FUNCTION: ENQUEUE JOB
-- Safely inserts a job into the queue, enforcing bounds and scheduling it.
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


-- 2. FUNCTION: CLAIM JOB ATOMICALLY
-- Atomically claims the next ready-to-run high-priority job for a worker using SKIP LOCKED.
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
    -- Query, lock, and claim one eligible job
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

    -- Return the details of the claimed job if found
    IF v_claimed_id IS NOT NULL THEN
        RETURN QUERY 
        SELECT id, name, payload 
        FROM jobs 
        WHERE id = v_claimed_id;
    END IF;
END;
$$ LANGUAGE plpgsql;


-- 3. FUNCTION: REPLAY DLQ JOB
-- Restores a permanently failed job from the Dead Letter Queue back into active execution.
CREATE OR REPLACE FUNCTION replay_dlq_job(
    p_job_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    v_deleted_count INT;
BEGIN
    -- 1. Verify existence in DLQ and delete
    DELETE FROM dead_letter_queues
    WHERE job_id = p_job_id;
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

    -- 2. Re-queue the job if it existed in DLQ
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
