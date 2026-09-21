import pytest
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.job_service import JobService
from app.models.core import Job, JobExecution, Queue

@pytest.mark.asyncio
async def test_calculate_retry_backoff(mock_db_session):
    job = Job(
        id=uuid.uuid4(),
        queue_id=uuid.uuid4(),
        name="test_task",
        status="queued",
        max_retries=3,
        retries_count=1,
        payload={}
    )
    
    # Mock database session returning no custom policies (fallbacks applied)
    mock_res = MagicMock()
    mock_res.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=mock_res)
    
    service = JobService(mock_db_session)
    delay = await service._calculate_retry_backoff(job)
    
    # Fallback delay: 5 * (2.0 ** retries_count) -> 5 * 2 = 10
    assert delay == 10

@pytest.mark.asyncio
async def test_job_replay(mock_db_session):
    job_id = uuid.uuid4()
    job = Job(
        id=job_id,
        queue_id=uuid.uuid4(),
        name="test_task",
        status="failed",
        error_message="fatal",
        max_retries=3,
        retries_count=3,
        payload={}
    )
    
    service = JobService(mock_db_session)
    
    # Mock job retrieval
    service.get_job = AsyncMock(return_value=job)
    service.job_repo.update = AsyncMock(return_value=job)
    
    replayed = await service.replay_job(job_id)
    
    # Confirm status resets
    assert service.job_repo.update.called
    update_data = service.job_repo.update.call_args[0][1]
    assert update_data["status"] == "queued"
    assert update_data["retries_count"] == 0
    assert update_data["error_message"] is None
