"""Session API -- CRUD for chat sessions."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.db import get_pool
from app.models import SessionResponse

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["sessions"])


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session():
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc)

    try:
        pool = await get_pool()
    except RuntimeError as exc:
        _logger.error("Database not configured: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.") from exc
    except Exception as exc:
        _logger.exception("Failed to get database pool")
        raise HTTPException(status_code=503, detail="Database unavailable.") from exc

    try:
        async with pool.acquire(timeout=5) as conn:
            await conn.execute(
                """
                INSERT INTO sessions (session_id, created_at, current_phase)
                VALUES ($1, $2, $3)
                ON CONFLICT (session_id) DO NOTHING
                """,
                session_id,
                now,
                "orchestrator",
            )
    except Exception as exc:
        _logger.exception("Failed to create session %s", session_id)
        raise HTTPException(status_code=503, detail="Database operation failed.") from exc

    return SessionResponse(
        session_id=session_id,
        created_at=now,
        current_phase="orchestrator",
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Retrieve an existing session."""
    try:
        pool = await get_pool()
    except RuntimeError as exc:
        _logger.error("Database not configured: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.") from exc
    except Exception as exc:
        _logger.exception("Failed to get database pool")
        raise HTTPException(status_code=503, detail="Database unavailable.") from exc

    try:
        async with pool.acquire(timeout=5) as conn:
            row = await conn.fetchrow(
                "SELECT session_id, created_at, current_phase FROM sessions WHERE session_id = $1",
                session_id,
            )
    except Exception as exc:
        _logger.exception("Failed to fetch session %s", session_id)
        raise HTTPException(status_code=503, detail="Database operation failed.") from exc

    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")

    return SessionResponse(
        session_id=row["session_id"],
        created_at=row["created_at"],
        current_phase=row["current_phase"],
    )
