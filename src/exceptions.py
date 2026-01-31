"""Custom exception classes and global exception handlers for GenueChat."""

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class GenueException(Exception):
    """Base exception for GenueChat application."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(GenueException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, status_code=401)


class AuthorizationError(GenueException):
    """Raised when user lacks permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, status_code=403)


class RateLimitError(GenueException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message=message, status_code=429)


class ValidationError(GenueException):
    """Raised for input validation failures."""

    def __init__(
        self, message: str = "Validation error", details: Optional[Dict] = None
    ):
        super().__init__(message=message, status_code=422, details=details)


class DatabaseError(GenueException):
    """Raised for database-related errors."""

    def __init__(self, message: str = "Database error"):
        super().__init__(message=message, status_code=503)


class LLMError(GenueException):
    """Raised for LLM service errors."""

    def __init__(self, message: str = "LLM service error"):
        super().__init__(message=message, status_code=502)


class DocumentProcessingError(GenueException):
    """Raised when document processing fails."""

    def __init__(self, message: str = "Document processing failed"):
        super().__init__(message=message, status_code=400)


def _error_response(
    status_code: int,
    message: str,
    details: Optional[Dict] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    body: Dict[str, Any] = {
        "error": True,
        "status_code": status_code,
        "message": message,
    }
    if details:
        body["details"] = details
    if request_id:
        body["request_id"] = request_id
    return JSONResponse(status_code=status_code, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(GenueException)
    async def genue_exception_handler(
        request: Request, exc: GenueException
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return _error_response(
            exc.status_code, exc.message, exc.details, request_id
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return _error_response(exc.status_code, str(exc.detail), None, request_id)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        details = {"errors": exc.errors()}
        return _error_response(422, "Request validation failed", details, request_id)

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return _error_response(500, "Internal server error", None, request_id)
