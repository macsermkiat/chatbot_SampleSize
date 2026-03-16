"""Tests for saved-projects API endpoints (list, update, delete, messages, limits)."""

from __future__ import annotations

import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.billing import PROJECT_LIMITS, get_project_limit_for_tier

_TEST_SECRET = "test-jwt-secret-256-bit-long-key!"
VALID_UUID = "550e8400-e29b-41d4-a716-446655440000"
VALID_UUID_2 = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
OTHER_USER_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def _make_token(sub: str = VALID_UUID, email: str = "test@example.com") -> str:
    payload = {
        "sub": sub,
        "email": email,
        "role": "authenticated",
        "aud": "authenticated",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return pyjwt.encode(payload, _TEST_SECRET, algorithm="HS256")


@pytest.fixture()
def mock_pool():
    pool = MagicMock()
    conn = MagicMock()
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=False)
    pool.acquire.return_value = conn
    return pool, conn


@pytest.fixture()
def auth_header():
    token = _make_token()
    return {"Authorization": f"Bearer {token}"}


def _settings_patch():
    return patch("app.auth.settings", MagicMock(supabase_jwt_secret=_TEST_SECRET))


class TestListProjects:
    """Tests for GET /api/projects."""

    async def test_returns_empty_for_new_user(self, mock_pool, auth_header):
        pool, conn = mock_pool
        conn.fetchval = AsyncMock(return_value=0)
        conn.fetch = AsyncMock(return_value=[])

        with (
            patch("app.api.projects.get_pool", AsyncMock(return_value=pool)),
            _settings_patch(),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/projects", headers=auth_header)

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_returns_user_sessions(self, mock_pool, auth_header):
        pool, conn = mock_pool
        now = datetime(2026, 3, 16, 10, 0, 0)
        conn.fetchval = AsyncMock(return_value=1)
        conn.fetch = AsyncMock(return_value=[
            {
                "session_id": VALID_UUID,
                "name": "My Research",
                "description": "Testing AI",
                "current_phase": "methodology",
                "created_at": now,
                "updated_at": now,
                "ended_at": None,
            },
        ])

        with (
            patch("app.api.projects.get_pool", AsyncMock(return_value=pool)),
            _settings_patch(),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/projects", headers=auth_header)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["session_id"] == VALID_UUID
        assert data["items"][0]["name"] == "My Research"
        assert data["total"] == 1

    async def test_search_filters_by_query(self, mock_pool, auth_header):
        pool, conn = mock_pool
        conn.fetchval = AsyncMock(return_value=0)
        conn.fetch = AsyncMock(return_value=[])

        with (
            patch("app.api.projects.get_pool", AsyncMock(return_value=pool)),
            _settings_patch(),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/projects?q=colonoscopy", headers=auth_header,
                )

        assert response.status_code == 200
        # Verify the search query was passed to the SQL (conn.fetch was called)
        conn.fetch.assert_called_once()
        call_args = conn.fetch.call_args
        # search_pattern is the second positional arg (after user_id)
        positional_args = call_args[0]
        assert any("%colonoscopy%" == arg for arg in positional_args if isinstance(arg, str))

    async def test_pagination_params(self, mock_pool, auth_header):
        pool, conn = mock_pool
        conn.fetchval = AsyncMock(return_value=50)
        conn.fetch = AsyncMock(return_value=[])

        with (
            patch("app.api.projects.get_pool", AsyncMock(return_value=pool)),
            _settings_patch(),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/projects?limit=10&offset=20", headers=auth_header,
                )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 50

    async def test_requires_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/projects")

        assert response.status_code == 401


class TestUpdateProject:
    """Tests for PATCH /api/projects/{session_id}."""

    async def test_update_name_and_description(self, mock_pool, auth_header):
        pool, conn = mock_pool
        now = datetime(2026, 3, 16, 10, 0, 0)
        conn.fetchrow = AsyncMock(return_value={
            "session_id": VALID_UUID,
            "name": "Updated Name",
            "description": "Updated Desc",
            "updated_at": now,
        })

        with (
            patch("app.api.projects.get_pool", AsyncMock(return_value=pool)),
            _settings_patch(),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.patch(
                    f"/api/projects/{VALID_UUID}",
                    json={"name": "Updated Name", "description": "Updated Desc"},
                    headers=auth_header,
                )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated Desc"

    async def test_update_not_found(self, mock_pool, auth_header):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)

        with (
            patch("app.api.projects.get_pool", AsyncMock(return_value=pool)),
            _settings_patch(),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.patch(
                    f"/api/projects/{VALID_UUID_2}",
                    json={"name": "New Name"},
                    headers=auth_header,
                )

        assert response.status_code == 404

    async def test_update_requires_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/api/projects/{VALID_UUID}",
                json={"name": "New Name"},
            )

        assert response.status_code == 401


class TestDeleteProject:
    """Tests for DELETE /api/projects/{session_id}."""

    async def test_soft_delete_sets_deleted_at(self, mock_pool, auth_header):
        pool, conn = mock_pool
        conn.execute = AsyncMock(return_value="UPDATE 1")

        with (
            patch("app.api.projects.get_pool", AsyncMock(return_value=pool)),
            _settings_patch(),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete(
                    f"/api/projects/{VALID_UUID}", headers=auth_header,
                )

        assert response.status_code == 204
        conn.execute.assert_called_once()
        sql = conn.execute.call_args[0][0]
        assert "deleted_at" in sql

    async def test_delete_not_found(self, mock_pool, auth_header):
        pool, conn = mock_pool
        conn.execute = AsyncMock(return_value="UPDATE 0")

        with (
            patch("app.api.projects.get_pool", AsyncMock(return_value=pool)),
            _settings_patch(),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete(
                    f"/api/projects/{VALID_UUID_2}", headers=auth_header,
                )

        assert response.status_code == 404

    async def test_delete_requires_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/api/projects/{VALID_UUID}")

        assert response.status_code == 401


class TestGetMessages:
    """Tests for GET /api/sessions/{session_id}/messages."""

    async def test_returns_message_history(self, mock_pool, auth_header):
        pool, conn = mock_pool
        now = datetime(2026, 3, 16, 10, 0, 0)
        conn.fetchrow = AsyncMock(return_value={"session_id": VALID_UUID, "user_id": VALID_UUID})
        conn.fetch = AsyncMock(return_value=[
            {
                "role": "user",
                "content": "What sample size?",
                "node": None,
                "phase": "orchestrator",
                "created_at": now,
            },
            {
                "role": "assistant",
                "content": "For a two-arm RCT...",
                "node": "biostatistics_agent",
                "phase": "biostatistics",
                "created_at": now,
            },
        ])

        with (
            patch("app.api.sessions.get_pool", AsyncMock(return_value=pool)),
            _settings_patch(),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    f"/api/sessions/{VALID_UUID}/messages", headers=auth_header,
                )

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["content"] == "For a two-arm RCT..."

    async def test_returns_empty_for_no_messages(self, mock_pool, auth_header):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value={"session_id": VALID_UUID, "user_id": VALID_UUID})
        conn.fetch = AsyncMock(return_value=[])

        with (
            patch("app.api.sessions.get_pool", AsyncMock(return_value=pool)),
            _settings_patch(),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    f"/api/sessions/{VALID_UUID}/messages", headers=auth_header,
                )

        assert response.status_code == 200
        data = response.json()
        assert data["messages"] == []

    async def test_messages_requires_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/sessions/{VALID_UUID}/messages")

        assert response.status_code == 401

    async def test_messages_session_not_found(self, mock_pool, auth_header):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)

        with (
            patch("app.api.sessions.get_pool", AsyncMock(return_value=pool)),
            _settings_patch(),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    f"/api/sessions/{VALID_UUID}/messages", headers=auth_header,
                )

        assert response.status_code == 404


class TestProjectLimits:
    """Tests for project count limits by tier."""

    def test_project_limits_defined(self):
        assert PROJECT_LIMITS["free"] == 1
        assert PROJECT_LIMITS["researcher"] == 3
        assert PROJECT_LIMITS["pro"] == 10
        assert PROJECT_LIMITS["institutional"] is None

    def test_get_project_limit_for_tier(self):
        assert get_project_limit_for_tier("free") == 1
        assert get_project_limit_for_tier("researcher") == 3
        assert get_project_limit_for_tier("researcher_annual") == 3
        assert get_project_limit_for_tier("pro") == 10
        assert get_project_limit_for_tier("pro_annual") == 10
        assert get_project_limit_for_tier("institutional") is None
        # Unknown tier defaults to free limit
        assert get_project_limit_for_tier("nonexistent") == 1
