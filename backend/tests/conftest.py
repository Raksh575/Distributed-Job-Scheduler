import asyncio
import pytest
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_db_session():
    """Provides a mocked SQLAlchemy AsyncSession for unit testing service layers."""
    session = AsyncMock(spec=AsyncSession)
    
    # Mock context manager behaviors
    session.begin = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    
    return session
