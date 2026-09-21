from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings

# Create asynchronous engine
# Echo SQL commands in development for transparent debugging
is_dev = settings.ENVIRONMENT == "development"
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=is_dev,
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10
)

# Async session factory
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to inject database sessions."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
