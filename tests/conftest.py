"""Shared pytest fixtures for the GenueChat test suite."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    """Ensure safe defaults for every test."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-unit-tests")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("MONGODB_URL", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DATABASE", "genuechat_test")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    # Clear lru_cache so settings reload with test env vars
    from src.config import get_settings

    get_settings.cache_clear()


@pytest.fixture()
def settings():
    from src.config import get_settings

    return get_settings()


@pytest.fixture()
def mock_db():
    """Return a mock Database whose health_check passes."""
    db = MagicMock()
    db.connect = AsyncMock()
    db.close = AsyncMock()
    db.health_check = AsyncMock(return_value=True)
    return db


@pytest.fixture()
def client(mock_db):
    """Provide a TestClient with the DB mocked out."""
    with patch("src.database.Database.__new__", return_value=mock_db):
        with patch("app.get_database", return_value=mock_db):
            from app import app

            with TestClient(app, raise_server_exceptions=False) as c:
                yield c


@pytest.fixture()
def auth_headers(settings):
    """Return Authorization headers with a valid JWT."""
    from src.security import create_access_token

    token, _ = create_access_token(subject="testuser")
    return {"Authorization": f"Bearer {token}"}
