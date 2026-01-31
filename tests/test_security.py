"""Tests for src.security (JWT, rate limiter, sanitization)."""

import time

import pytest

from src.security import (
    TokenBucketRateLimiter,
    create_access_token,
    sanitize_for_db,
    sanitize_input,
    verify_token,
)


class TestJWT:
    def test_create_and_verify(self):
        token, expires_in = create_access_token("alice")
        assert isinstance(token, str)
        assert expires_in > 0
        payload = verify_token(token)
        assert payload["sub"] == "alice"

    def test_extra_claims(self):
        token, _ = create_access_token("bob", extra_claims={"role": "admin"})
        payload = verify_token(token)
        assert payload["role"] == "admin"

    def test_invalid_token_raises(self):
        from src.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError):
            verify_token("not.a.real.token")

    def test_expired_token_raises(self, monkeypatch):
        from src.config import get_settings

        get_settings.cache_clear()
        monkeypatch.setenv("JWT_EXPIRATION_MINUTES", "0")
        get_settings.cache_clear()
        # Re-import won't help because module-level settings is cached.
        # Instead just verify with a manually expired token.
        import jwt as pyjwt
        from datetime import datetime, timedelta, timezone

        expired = pyjwt.encode(
            {"sub": "x", "exp": datetime.now(timezone.utc) - timedelta(seconds=10)},
            "test-secret-key-for-unit-tests",
            algorithm="HS256",
        )
        from src.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError, match="expired"):
            verify_token(expired)


class TestRateLimiter:
    def test_allows_within_limit(self):
        rl = TokenBucketRateLimiter(max_tokens=5, window_seconds=60)
        for _ in range(5):
            assert rl.allow("ip1") is True

    def test_blocks_over_limit(self):
        rl = TokenBucketRateLimiter(max_tokens=2, window_seconds=60)
        assert rl.allow("ip2") is True
        assert rl.allow("ip2") is True
        assert rl.allow("ip2") is False


class TestSanitization:
    def test_strip_script_tags(self):
        result = sanitize_input('<script>alert("xss")</script>hello')
        assert "script" not in result.lower()
        assert "hello" in result

    def test_strip_html_tags(self):
        result = sanitize_input("<b>bold</b>")
        assert "<b>" not in result

    def test_html_entities_escaped(self):
        result = sanitize_input('a < b & c > d "e"')
        assert "&lt;" in result
        assert "&amp;" in result

    def test_sanitize_for_db_removes_dollar(self):
        result = sanitize_for_db("$where")
        assert "$" not in result

    def test_sanitize_for_db_removes_braces(self):
        result = sanitize_for_db("{key: value}")
        assert "{" not in result
