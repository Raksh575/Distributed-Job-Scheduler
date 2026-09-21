import os
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    PROJECT_NAME: str = "Distributed Job Scheduler"
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://djs_admin:djs_password@localhost:5432/djs_db"
    )

    # Cache/Broker
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # JWT Authentication
    SECRET_KEY: str = Field(default="super_secret_jwt_key_at_least_32_characters_long_for_security")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

settings = Settings()
