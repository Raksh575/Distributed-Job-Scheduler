from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_db_session
from app.core.config import settings

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str

class ReadinessResponse(BaseModel):
    status: str
    database: str

@router.get("", response_model=HealthResponse)
async def check_health():
    """System health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=settings.ENVIRONMENT
    )

@router.get("/liveness", status_code=status.HTTP_200_OK)
async def liveness_check():
    """Liveness probe returning fast OK if app runs."""
    return {"status": "alive"}

@router.get("/readiness", response_model=ReadinessResponse)
async def readiness_check(db: AsyncSession = Depends(get_db_session)):
    """Readiness probe checking database connectivity."""
    try:
        # Execute basic raw SQL ping
        await db.execute(text("SELECT 1"))
        return ReadinessResponse(
            status="ready",
            database="connected"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connectivity failed: {str(e)}"
        )
