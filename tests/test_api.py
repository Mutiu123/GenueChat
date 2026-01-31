"""Integration tests for API endpoints."""

from unittest.mock import AsyncMock, patch


class TestRootEndpoint:
    def test_root_returns_app_info(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["app"] == "GenueChat"


class TestHealthEndpoints:
    def test_health(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")

    def test_liveness(self, client):
        resp = client.get("/api/v1/health/live")
        assert resp.status_code == 200
        assert resp.json()["status"] == "alive"

    def test_readiness(self, client, mock_db):
        mock_db.health_check = AsyncMock(return_value=True)
        resp = client.get("/api/v1/health/ready")
        assert resp.status_code == 200

    def test_status(self, client):
        resp = client.get("/api/v1/status")
        assert resp.status_code == 200
        assert "version" in resp.json()


class TestAuthEndpoints:
    def test_generate_token(self, client):
        resp = client.post(
            "/api/v1/auth/token",
            json={"username": "testuser", "password": "testpass"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_me_without_token(self, client):
        resp = client.get("/api/v1/auth/me")
        # Should fail with 401
        assert resp.status_code == 401

    def test_me_with_token(self, client, auth_headers):
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["user"] == "testuser"


class TestChatEndpoints:
    def test_chat_requires_auth(self, client):
        resp = client.post("/api/v1/chat/", json={"question": "hello"})
        assert resp.status_code == 401

    @patch("src.routes.chat.handle_chat_async", new_callable=AsyncMock)
    def test_chat_success(self, mock_chat, client, auth_headers):
        mock_chat.return_value = "Hi there!"
        resp = client.post(
            "/api/v1/chat/",
            json={"question": "hello"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["answer"] == "Hi there!"

    def test_document_chat_requires_auth(self, client):
        resp = client.post("/api/v1/chat/document")
        assert resp.status_code in (401, 422)

    def test_document_chat_rejects_non_pdf(self, client, auth_headers):
        resp = client.post(
            "/api/v1/chat/document",
            headers=auth_headers,
            data={"question": "what?"},
            files={"file": ("test.txt", b"data", "text/plain")},
        )
        assert resp.status_code == 400
