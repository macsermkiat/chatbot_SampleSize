"""Tests for JWT authentication module."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import jwt as pyjwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.auth import AuthUser, get_current_user, get_optional_user
from app.main import app

# A stable secret for tests
_TEST_SECRET = "test-jwt-secret-256-bit-long-key!"


def _make_token(
    sub: str = "user-123",
    email: str = "test@example.com",
    role: str = "authenticated",
    aud: str = "authenticated",
    exp_offset: int = 3600,
) -> str:
    payload = {
        "sub": sub,
        "email": email,
        "role": role,
        "aud": aud,
        "iat": int(time.time()),
        "exp": int(time.time()) + exp_offset,
    }
    return pyjwt.encode(payload, _TEST_SECRET, algorithm="HS256")


class TestGetCurrentUser:
    """Tests for the get_current_user dependency."""

    async def test_valid_token_returns_user(self):
        token = _make_token(sub="abc-123", email="researcher@uni.edu")
        with (
            patch("app.auth.settings") as mock_settings,
            patch(
                "app.api.billing.get_user_subscription",
                AsyncMock(return_value=None),
            ),
        ):
            mock_settings.supabase_jwt_secret = _TEST_SECRET
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/billing/subscription",
                    headers={"Authorization": f"Bearer {token}"},
                )
            # 200 with free tier means auth passed successfully
            assert response.status_code == 200
            assert response.json()["tier"] == "free"

    async def test_missing_token_returns_401(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/billing/subscription")
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]

    async def test_expired_token_returns_401(self):
        token = _make_token(exp_offset=-3600)
        with patch("app.auth.settings") as mock_settings:
            mock_settings.supabase_jwt_secret = _TEST_SECRET
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/billing/subscription",
                    headers={"Authorization": f"Bearer {token}"},
                )
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    async def test_invalid_token_returns_401(self):
        with patch("app.auth.settings") as mock_settings:
            mock_settings.supabase_jwt_secret = _TEST_SECRET
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/billing/subscription",
                    headers={"Authorization": "Bearer not.a.valid.jwt"},
                )
        assert response.status_code == 401

    async def test_wrong_secret_returns_401(self):
        token = _make_token()
        with patch("app.auth.settings") as mock_settings:
            mock_settings.supabase_jwt_secret = "wrong-secret-key-totally-different"
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/billing/subscription",
                    headers={"Authorization": f"Bearer {token}"},
                )
        assert response.status_code == 401

    async def test_missing_jwt_secret_returns_503(self):
        token = _make_token()
        with patch("app.auth.settings") as mock_settings:
            mock_settings.supabase_jwt_secret = ""
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/billing/subscription",
                    headers={"Authorization": f"Bearer {token}"},
                )
        assert response.status_code == 503


class TestGetOptionalUser:
    """Tests for the get_optional_user dependency (graceful anonymous fallback)."""

    async def test_no_token_returns_none(self):
        from fastapi.security import HTTPAuthorizationCredentials

        with patch("app.auth.settings") as mock_settings:
            mock_settings.supabase_jwt_secret = _TEST_SECRET
            result = await get_optional_user(None)
        assert result is None

    async def test_valid_token_returns_user(self):
        from fastapi.security import HTTPAuthorizationCredentials

        token = _make_token(sub="user-456", email="doc@hospital.org")
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with patch("app.auth.settings") as mock_settings:
            mock_settings.supabase_jwt_secret = _TEST_SECRET
            result = await get_optional_user(creds)
        assert result is not None
        assert result.id == "user-456"
        assert result.email == "doc@hospital.org"

    async def test_invalid_token_returns_none(self):
        from fastapi.security import HTTPAuthorizationCredentials

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="garbage")
        with patch("app.auth.settings") as mock_settings:
            mock_settings.supabase_jwt_secret = _TEST_SECRET
            result = await get_optional_user(creds)
        assert result is None

    async def test_missing_secret_returns_none(self):
        from fastapi.security import HTTPAuthorizationCredentials

        token = _make_token()
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with patch("app.auth.settings") as mock_settings:
            mock_settings.supabase_jwt_secret = ""
            result = await get_optional_user(creds)
        assert result is None


class TestAuthUserModel:
    """Tests for the AuthUser pydantic model."""

    def test_default_role(self):
        user = AuthUser(id="abc", email="test@test.com")
        assert user.role == "authenticated"

    def test_custom_role(self):
        user = AuthUser(id="abc", email="test@test.com", role="admin")
        assert user.role == "admin"
