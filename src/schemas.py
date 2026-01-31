"""Pydantic v2 models for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    question: str = Field(
        ..., min_length=1, max_length=5000, description="User question"
    )
    session_id: Optional[str] = Field(
        None, max_length=128, description="Optional session identifier"
    )

    @field_validator("question")
    @classmethod
    def strip_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question must not be blank")
        return v


class DocumentChatRequest(BaseModel):
    """Metadata sent alongside a file upload for document Q&A."""

    question: str = Field(
        ..., min_length=1, max_length=5000, description="Question about the document"
    )
    session_id: Optional[str] = Field(None, max_length=128)

    @field_validator("question")
    @classmethod
    def strip_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question must not be blank")
        return v


class TokenRequest(BaseModel):
    """Request body for token generation."""

    username: str = Field(..., min_length=1, max_length=256)
    password: str = Field(..., min_length=1, max_length=256)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class ChatResponse(BaseModel):
    """Standard chat response."""

    answer: str
    session_id: Optional[str] = None
    model: str = ""
    processing_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DocumentChatResponse(BaseModel):
    """Response for document-based Q&A."""

    answer: str
    source_chunks: int = 0
    session_id: Optional[str] = None
    processing_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    environment: str
    uptime_seconds: float
    checks: Dict[str, str] = {}


class ErrorResponse(BaseModel):
    """Structured error response."""

    error: bool = True
    status_code: int
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class AuditLogEntry(BaseModel):
    """Audit log record stored in the database."""

    event_type: str
    user: Optional[str] = None
    request_id: Optional[str] = None
    payload: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PredictionAudit(BaseModel):
    """Audit record for LLM predictions."""

    request_id: Optional[str] = None
    question: str
    answer: str
    model: str
    processing_time_ms: float
    source: str = "chat"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
