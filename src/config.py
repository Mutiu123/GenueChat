"""Centralized configuration management for GenueChat.

Provides type-safe settings loaded from environment variables with
support for dev, staging, and production environments.
"""

import os
from enum import Enum
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Application environment enum."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "GenueChat"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT token signing",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "genuechat"
    MONGODB_MIN_POOL_SIZE: int = 10
    MONGODB_MAX_POOL_SIZE: int = 50
    MONGODB_TIMEOUT_MS: int = 5000

    # LLM
    GROQ_API_KEY: str = Field(default="", description="Groq API key for LLM access")
    LLM_MODEL_NAME: str = "llama-3.1-8b-instant"
    LLM_TEMPERATURE: float = 0.0

    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    METRICS_PREFIX: str = "genuechat"

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        origins = [o.strip() for o in v.split(",") if o.strip()]
        if not origins:
            raise ValueError("At least one CORS origin must be specified")
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
