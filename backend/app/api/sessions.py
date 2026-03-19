"""Session API -- CRUD for chat sessions + protocol export."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import Response

from app.auth import AuthUser, get_current_user
from app.db import get_pool
from app.models import (
    EvaluationRequest,
    EvaluationResponse,
    MessageItem,
    MessageListResponse,
    SessionEndResponse,
    SessionResponse,
    SummaryResponse,
)
from app.services.protocol_export import generate_protocol
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
            # Verify session exists and check for cached summary
            session = await conn.fetchrow(
                "SELECT session_id, summary_cache FROM sessions WHERE session_id = $1",
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

    # Use cached summary if available
    cached_summary = session.get("summary_cache")
    if cached_summary:
        return SummaryResponse(
            session_id=session_id,
            summary_text=cached_summary,
            generated_at=datetime.now(tz=timezone.utc),
        )

    messages = [{"role": r["role"], "content": r["content"]} for r in rows]

    try:
        summary_text = await generate_summary(messages)
    except RuntimeError as exc:
        _logger.error("Summary generation failed for session %s: %s", session_id, exc)
        raise HTTPException(
            status_code=502,
            detail="Summary generation failed. Please try again later.",
        ) from exc

    # Cache the summary for future requests (fire-and-forget)
    try:
        async with pool.acquire(timeout=5) as conn:
            await conn.execute(
                "UPDATE sessions SET summary_cache = $1 WHERE session_id = $2",
                summary_text,
                session_id,
            )
    except Exception:
        _logger.warning("Failed to cache summary for session %s", session_id)

    return SummaryResponse(
        session_id=session_id,
        summary_text=summary_text,
        generated_at=datetime.now(tz=timezone.utc),
    )


@router.post(
    "/sessions/{session_id}/evaluate",
    response_model=EvaluationResponse,
    status_code=201,
)
async def evaluate_session(session_id: str, body: EvaluationRequest):
    """Store a user evaluation (star rating + comment) for a session."""
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
                INSERT INTO session_evaluations (session_id, rating, comment)
                VALUES ($1, $2, $3)
                ON CONFLICT (session_id) DO UPDATE
                  SET rating = EXCLUDED.rating,
                      comment = EXCLUDED.comment,
                      created_at = (now() AT TIME ZONE 'Asia/Bangkok')
                RETURNING session_id, rating, comment, created_at
                """,
                session_id,
                body.rating,
                body.comment,
            )
    except Exception as exc:
        _logger.exception("Failed to store evaluation for session %s", session_id)
        raise HTTPException(status_code=503, detail="Database operation failed.") from exc

    return EvaluationResponse(
        session_id=row["session_id"],
        rating=row["rating"],
        comment=row["comment"],
        created_at=row["created_at"],
    )


@router.get(
    "/sessions/{session_id}/messages",
    response_model=MessageListResponse,
)
async def get_session_messages(
    session_id: str,
    user: AuthUser = Depends(get_current_user),
):
    """Return the full message history for a session (for resuming)."""
    _validate_session_id(session_id)
    try:
        pool = await get_pool()
    except Exception as exc:
        _logger.error("Database unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.") from exc

    try:
        async with pool.acquire(timeout=5) as conn:
            session = await conn.fetchrow(
                "SELECT session_id, user_id FROM sessions WHERE session_id = $1",
                session_id,
            )
            if not session:
                raise HTTPException(status_code=404, detail="Session not found.")
            if session["user_id"] is not None and session["user_id"] != user.id:
                raise HTTPException(status_code=404, detail="Session not found.")

            rows = await conn.fetch(
                """
                SELECT role, content, node, phase, created_at
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

    messages = [
        MessageItem(
            role=r["role"],
            content=r["content"],
            node=r.get("node"),
            phase=r.get("phase"),
            created_at=r["created_at"],
        )
        for r in rows
    ]
    return MessageListResponse(messages=messages)


@router.get("/sessions/{session_id}/export")
async def export_session_protocol(
    session_id: str,
    format: Literal["docx", "pdf"] = Query("docx", description="Export format: docx or pdf"),
    user: AuthUser = Depends(get_current_user),
):
    """Export session as a formatted research protocol document (DOCX or PDF)."""
    _validate_session_id(session_id)

    try:
        pool = await get_pool()
    except (RuntimeError, Exception) as exc:
        _logger.error("Database unavailable for export: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.") from exc

    try:
        async with pool.acquire(timeout=5) as conn:
            session = await conn.fetchrow(
                "SELECT session_id, user_id, summary_cache FROM sessions WHERE session_id = $1",
                session_id,
            )
            if not session:
                raise HTTPException(status_code=404, detail="Session not found.")
            if session["user_id"] is not None and session["user_id"] != user.id:
                raise HTTPException(status_code=404, detail="Session not found.")

            rows = await conn.fetch(
                """
                SELECT role, content, phase
                FROM message_logs
                WHERE session_id = $1
                ORDER BY created_at ASC
                """,
                session_id,
            )
    except HTTPException:
        raise
    except Exception as exc:
        _logger.exception("Failed to fetch data for export: session %s", session_id)
        raise HTTPException(status_code=503, detail="Database operation failed.") from exc

    messages = [
        {"role": r["role"], "content": r["content"], "phase": r.get("phase", "")}
        for r in rows
    ]

    # Use cached summary if available; otherwise generate and cache it
    cached_summary = session.get("summary_cache")
    if cached_summary:
        summary_text = cached_summary
    else:
        try:
            summary_text = await generate_summary(messages)
        except RuntimeError:
            summary_text = "(Summary generation unavailable)"

        # Cache the summary for future exports (fire-and-forget)
        if summary_text != "(Summary generation unavailable)":
            try:
                async with pool.acquire(timeout=5) as conn:
                    await conn.execute(
                        "UPDATE sessions SET summary_cache = $1 WHERE session_id = $2",
                        summary_text,
                        session_id,
                    )
            except Exception:
                _logger.warning("Failed to cache summary for session %s", session_id)

    try:
        file_bytes, content_type, filename = generate_protocol(
            summary_text, messages, session_id, format=format,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
