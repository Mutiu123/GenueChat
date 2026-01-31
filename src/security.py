"""Security utilities: JWT auth, rate limiting, input sanitization."""

import html
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import get_settings
from src.exceptions import AuthenticationError, RateLimitError

settings = get_settings()

# ---------------------------------------------------------------------------
# JWT Authentication
# ---------------------------------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(
    subject: str, extra_claims: Optional[Dict] = None
) -> Tuple[str, int]:
    """Create a signed JWT token. Returns (token, expires_in_seconds)."""
    expires_delta = timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, int(expires_delta.total_seconds())


def verify_token(token: str) -> Dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Dict:
    """FastAPI dependency that extracts and validates the JWT bearer token."""
    if credentials is None:
        raise AuthenticationError("Missing authorization header")
    return verify_token(credentials.credentials)


# ---------------------------------------------------------------------------
# Token-Bucket Rate Limiter
# ---------------------------------------------------------------------------


class TokenBucketRateLimiter:
    """In-memory token-bucket rate limiter keyed by client IP."""

    def __init__(
        self,
        max_tokens: int = settings.RATE_LIMIT_REQUESTS,
        window_seconds: int = settings.RATE_LIMIT_WINDOW_SECONDS,
    ):
        self.max_tokens = max_tokens
        self.window_seconds = window_seconds
        self._buckets: Dict[str, Tuple[float, float]] = {}

    def _refill(self, tokens: float, last_time: float, now: float) -> float:
        elapsed = now - last_time
        rate = self.max_tokens / self.window_seconds
        return min(self.max_tokens, tokens + elapsed * rate)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        tokens, last_time = self._buckets.get(key, (float(self.max_tokens), now))
        tokens = self._refill(tokens, last_time, now)
        if tokens >= 1:
            self._buckets[key] = (tokens - 1, now)
            return True
        self._buckets[key] = (tokens, now)
        return False


rate_limiter = TokenBucketRateLimiter()


async def check_rate_limit(request: Request) -> None:
    """FastAPI dependency that enforces per-IP rate limiting."""
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.allow(client_ip):
        raise RateLimitError(
            f"Rate limit exceeded. Max {settings.RATE_LIMIT_REQUESTS} "
            f"requests per {settings.RATE_LIMIT_WINDOW_SECONDS}s."
        )


# ---------------------------------------------------------------------------
# Input Sanitization
# ---------------------------------------------------------------------------

_SCRIPT_RE = re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.I | re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_MONGO_INJECTION_CHARS = re.compile(r"[\${}]")


def sanitize_input(value: str) -> str:
    """Sanitize user input by stripping dangerous HTML and control characters."""
    value = _SCRIPT_RE.sub("", value)
    value = _TAG_RE.sub("", value)
    value = html.escape(value, quote=True)
    return value.strip()


def sanitize_for_db(value: str) -> str:
    """Remove characters commonly used in NoSQL injection attacks."""
    return _MONGO_INJECTION_CHARS.sub("", value)
