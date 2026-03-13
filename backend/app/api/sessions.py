"""Session API -- CRUD for chat sessions."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Path

from app.db import get_pool
from app.models import SessionEndResponse, SessionResponse, SummaryResponse
from app.services.summary import generate_summary

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["sessions"])

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _validate_session_id(session_id: str) -> None:
    """Raise 422 if session_id is not a valid UUID."""
    if not _UUID_RE.match(session_id):
        raise HTTPException(status_code=422, detail="Invalid session ID format.")


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session():
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
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
                """
                INSERT INTO sessions (session_id, current_phase)
                VALUES ($1, $2)
                ON CONFLICT (session_id) DO NOTHING
                RETURNING session_id, created_at, current_phase
                """,
                session_id,
                "orchestrator",
            )
    except Exception as exc:
        _logger.exception("Failed to create session %s", session_id)
        raise HTTPException(status_code=503, detail="Database operation failed.") from exc

    return SessionResponse(
        session_id=row["session_id"] if row else session_id,
        created_at=row["created_at"] if row else datetime.now(tz=timezone.utc),
        current_phase=row["current_phase"] if row else "orchestrator",
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


@router.post(
    "/sessions/{session_id}/end",
    response_model=SessionEndResponse,
)
async def end_session(session_id: str):
    """Mark a session as ended."""
    _validate_session_id(session_id)
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
                """
                UPDATE sessions
                SET ended_at = (now() AT TIME ZONE 'Asia/Bangkok')
                WHERE session_id = $1 AND ended_at IS NULL
                RETURNING session_id, ended_at
                """,
                session_id,
            )
    except Exception as exc:
        _logger.exception("Failed to end session %s", session_id)
        raise HTTPException(status_code=503, detail="Database operation failed.") from exc

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Session not found or already ended.",
        )

    return SessionEndResponse(
        session_id=row["session_id"],
        ended_at=row["ended_at"],
    )


@router.get(
    "/sessions/{session_id}/summary",
    response_model=SummaryResponse,
)
async def get_session_summary(session_id: str):
    """Generate a brief consultation summary for the session."""
    _validate_session_id(session_id)
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
            # Verify session exists
            session = await conn.fetchrow(
                "SELECT session_id FROM sessions WHERE session_id = $1",
                session_id,
            )
            if not session:
                raise HTTPException(status_code=404, detail="Session not found.")

            # Fetch conversation messages
            rows = await conn.fetch(
                """
                SELECT role, content
                FROM message_logs
                WHERE session_id = $1
                ORDER BY created_at ASC
                """,
                session_id,
            )
    except HTTPException:
        raise
    except Exception as exc:
        _logger.exception("Failed to fetch messages for session %s", session_id)
        raise HTTPException(status_code=503, detail="Database operation failed.") from exc

    messages = [{"role": r["role"], "content": r["content"]} for r in rows]

    try:
        summary_text = await generate_summary(messages)
    except RuntimeError as exc:
        _logger.error("Summary generation failed for session %s: %s", session_id, exc)
        raise HTTPException(
            status_code=502,
            detail="Summary generation failed. Please try again later.",
        ) from exc

    return SummaryResponse(
        session_id=session_id,
        summary_text=summary_text,
        generated_at=datetime.now(tz=timezone.utc),
    )
