"""Tests for src.exceptions."""

from src.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    DocumentProcessingError,
    GenueException,
    LLMError,
    RateLimitError,
    ValidationError,
)


class TestExceptions:
    def test_base_exception_defaults(self):
        exc = GenueException()
        assert exc.status_code == 500
        assert exc.message == "An unexpected error occurred"
        assert exc.details == {}

    def test_base_exception_custom(self):
        exc = GenueException("custom", 418, {"key": "val"})
        assert exc.status_code == 418
        assert exc.message == "custom"
        assert exc.details == {"key": "val"}

    def test_authentication_error(self):
        exc = AuthenticationError()
        assert exc.status_code == 401

    def test_authorization_error(self):
        exc = AuthorizationError()
        assert exc.status_code == 403

    def test_rate_limit_error(self):
        exc = RateLimitError()
        assert exc.status_code == 429

    def test_validation_error(self):
        exc = ValidationError(details={"field": "bad"})
        assert exc.status_code == 422
        assert exc.details["field"] == "bad"

    def test_database_error(self):
        exc = DatabaseError()
        assert exc.status_code == 503

    def test_llm_error(self):
        exc = LLMError()
        assert exc.status_code == 502

    def test_document_processing_error(self):
        exc = DocumentProcessingError()
        assert exc.status_code == 400
