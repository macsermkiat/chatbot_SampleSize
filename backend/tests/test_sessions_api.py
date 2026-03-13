"""Tests for session API endpoints (end session, get summary)."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# Valid UUID for tests that should pass validation
VALID_UUID = "550e8400-e29b-41d4-a716-446655440000"
VALID_UUID_2 = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"


@pytest.fixture()
def mock_pool():
    """Create a mock database pool with configurable query results."""
    pool = MagicMock()
    conn = MagicMock()
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=False)
    pool.acquire.return_value = conn
    return pool, conn


class TestSessionIdValidation:
    """Tests for UUID validation on session_id path parameters."""

    async def test_end_session_rejects_invalid_uuid(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/sessions/not-a-uuid/end")
        assert response.status_code == 422

    async def test_summary_rejects_path_traversal(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/sessions/not-valid/summary")
        assert response.status_code == 422

    async def test_end_session_accepts_valid_uuid(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)
        with patch("app.api.sessions.get_pool", AsyncMock(return_value=pool)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(f"/api/sessions/{VALID_UUID}/end")
        # 404 (not found) means validation passed
        assert response.status_code == 404


class TestEndSession:
    """Tests for POST /api/sessions/{session_id}/end."""

    async def test_end_session_success(self, mock_pool):
        pool, conn = mock_pool
        now = datetime(2026, 3, 14, 10, 0, 0)
        conn.fetchrow = AsyncMock(
            return_value={"session_id": VALID_UUID, "ended_at": now},
        )

        with patch("app.api.sessions.get_pool", AsyncMock(return_value=pool)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(f"/api/sessions/{VALID_UUID}/end")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == VALID_UUID
        assert "ended_at" in data

    async def test_end_session_not_found(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)

        with patch("app.api.sessions.get_pool", AsyncMock(return_value=pool)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(f"/api/sessions/{VALID_UUID_2}/end")

        assert response.status_code == 404
        assert "not found or already ended" in response.json()["detail"]

    async def test_end_session_db_unavailable(self):
        with patch(
            "app.api.sessions.get_pool",
            AsyncMock(side_effect=RuntimeError("No DB")),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(f"/api/sessions/{VALID_UUID}/end")

        assert response.status_code == 503


class TestGetSessionSummary:
    """Tests for GET /api/sessions/{session_id}/summary."""

    async def test_summary_success(self, mock_pool):
        pool, conn = mock_pool

        conn.fetchrow = AsyncMock(return_value={"session_id": VALID_UUID})
        conn.fetch = AsyncMock(
            return_value=[
                {"role": "user", "content": "What sample size?"},
                {"role": "assistant", "content": "For a two-arm RCT..."},
            ],
        )

        with (
            patch("app.api.sessions.get_pool", AsyncMock(return_value=pool)),
            patch(
                "app.api.sessions.generate_summary",
                AsyncMock(return_value="Brief consultation summary."),
            ),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(f"/api/sessions/{VALID_UUID}/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == VALID_UUID
        assert data["summary_text"] == "Brief consultation summary."
        assert "generated_at" in data

    async def test_summary_session_not_found(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)

        with patch("app.api.sessions.get_pool", AsyncMock(return_value=pool)):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(f"/api/sessions/{VALID_UUID_2}/summary")

        assert response.status_code == 404

    async def test_summary_generation_failure(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value={"session_id": VALID_UUID})
        conn.fetch = AsyncMock(return_value=[])

        with (
            patch("app.api.sessions.get_pool", AsyncMock(return_value=pool)),
            patch(
                "app.api.sessions.generate_summary",
                AsyncMock(side_effect=RuntimeError("LLM failed")),
            ),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(f"/api/sessions/{VALID_UUID}/summary")

        assert response.status_code == 502
        # Verify generic error message (no internal details leaked)
        assert response.json()["detail"] == "Summary generation failed. Please try again later."

    async def test_summary_db_unavailable(self):
        with patch(
            "app.api.sessions.get_pool",
            AsyncMock(side_effect=RuntimeError("No DB")),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(f"/api/sessions/{VALID_UUID}/summary")

        assert response.status_code == 503
