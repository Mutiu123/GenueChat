"""Tests for src.schemas (Pydantic models)."""

import pytest
from pydantic import ValidationError

from src.schemas import (
    ChatRequest,
    ChatResponse,
    DocumentChatRequest,
    ErrorResponse,
    HealthResponse,
    TokenRequest,
    TokenResponse,
)


class TestChatRequest:
    def test_valid_request(self):
        req = ChatRequest(question="Hello?")
        assert req.question == "Hello?"

    def test_empty_question_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(question="")

    def test_whitespace_only_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(question="   ")

    def test_question_stripped(self):
        req = ChatRequest(question="  Hi  ")
        assert req.question == "Hi"

    def test_max_length_enforced(self):
        with pytest.raises(ValidationError):
            ChatRequest(question="a" * 5001)


class TestDocumentChatRequest:
    def test_valid(self):
        req = DocumentChatRequest(question="Summarise")
        assert req.question == "Summarise"


class TestTokenRequest:
    def test_valid(self):
        req = TokenRequest(username="user", password="pass")
        assert req.username == "user"

    def test_empty_username_rejected(self):
        with pytest.raises(ValidationError):
            TokenRequest(username="", password="pass")


class TestResponseModels:
    def test_chat_response(self):
        resp = ChatResponse(answer="hi")
        assert resp.answer == "hi"

    def test_token_response(self):
        resp = TokenResponse(access_token="abc", expires_in=3600)
        assert resp.token_type == "bearer"

    def test_health_response(self):
        resp = HealthResponse(
            status="healthy",
            version="1.0",
            environment="dev",
            uptime_seconds=42.0,
        )
        assert resp.status == "healthy"

    def test_error_response(self):
        resp = ErrorResponse(status_code=404, message="not found")
        assert resp.error is True
