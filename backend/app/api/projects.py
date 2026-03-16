"""Projects API -- list, rename, and delete saved research sessions."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.auth import AuthUser, get_current_user
from app.db import get_pool
from app.models import (
    ProjectListResponse,
    ProjectListItem,
    ProjectUpdateRequest,
    ProjectUpdateResponse,
)

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["projects"])


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    user: AuthUser = Depends(get_current_user),
    q: str | None = Query(default=None, max_length=200, description="Search name/description"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List the authenticated user's research sessions (projects)."""
    try:
        pool = await get_pool()
    except Exception as exc:
        _logger.error("Database unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.") from exc

    try:
        async with pool.acquire(timeout=5) as conn:
            if q:
                search_pattern = f"%{q}%"
                total = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM sessions
                    WHERE user_id = $1
                      AND ended_at IS NULL
                      AND (name ILIKE $2 OR description ILIKE $2)
                    """,
                    user.id,
                    search_pattern,
                )
                rows = await conn.fetch(
                    """
                    SELECT session_id, name, description, current_phase,
                           created_at, updated_at, ended_at
                    FROM sessions
                    WHERE user_id = $1
                      AND ended_at IS NULL
                      AND (name ILIKE $2 OR description ILIKE $2)
                    ORDER BY COALESCE(updated_at, created_at) DESC
                    LIMIT $3 OFFSET $4
                    """,
                    user.id,
                    search_pattern,
                    limit,
                    offset,
                )
            else:
                total = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM sessions
                    WHERE user_id = $1 AND ended_at IS NULL
                    """,
                    user.id,
                )
                rows = await conn.fetch(
                    """
                    SELECT session_id, name, description, current_phase,
                           created_at, updated_at, ended_at
                    FROM sessions
                    WHERE user_id = $1 AND ended_at IS NULL
                    ORDER BY COALESCE(updated_at, created_at) DESC
                    LIMIT $2 OFFSET $3
                    """,
                    user.id,
                    limit,
                    offset,
                )
    except Exception as exc:
        _logger.exception("Failed to list projects for user %s", user.id)
        raise HTTPException(status_code=503, detail="Database operation failed.") from exc

    items = [
        ProjectListItem(
            session_id=r["session_id"],
            name=r["name"],
            description=r["description"],
            current_phase=r["current_phase"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            ended_at=r["ended_at"],
        )
        for r in rows
    ]
    return ProjectListResponse(items=items, total=total)


@router.patch("/projects/{session_id}", response_model=ProjectUpdateResponse)
async def update_project(
    session_id: str,
    body: ProjectUpdateRequest,
    user: AuthUser = Depends(get_current_user),
):
    """Update name and/or description for a session (project)."""
    try:
        pool = await get_pool()
    except Exception as exc:
        _logger.error("Database unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.") from exc

    try:
        async with pool.acquire(timeout=5) as conn:
            row = await conn.fetchrow(
                """
                UPDATE sessions
                SET name = $1,
                    description = $2,
                    updated_at = (now() AT TIME ZONE 'Asia/Bangkok')
                WHERE session_id = $3 AND user_id = $4
                RETURNING session_id, name, description, updated_at
                """,
                body.name,
                body.description,
                session_id,
                user.id,
            )
    except Exception as exc:
        _logger.exception("Failed to update project %s", session_id)
        raise HTTPException(status_code=503, detail="Database operation failed.") from exc

    if not row:
        raise HTTPException(status_code=404, detail="Project not found.")

    return ProjectUpdateResponse(
        session_id=row["session_id"],
        name=row["name"],
        description=row["description"],
        updated_at=row["updated_at"],
    )


@router.delete("/projects/{session_id}", status_code=204)
async def delete_project(
    session_id: str,
    user: AuthUser = Depends(get_current_user),
):
    """Soft-delete a session (project) by setting ended_at."""
    try:
        pool = await get_pool()
    except Exception as exc:
        _logger.error("Database unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.") from exc

    try:
        async with pool.acquire(timeout=5) as conn:
            result = await conn.execute(
                """
                UPDATE sessions
                SET ended_at = (now() AT TIME ZONE 'Asia/Bangkok')
                WHERE session_id = $1 AND user_id = $2 AND ended_at IS NULL
                """,
                session_id,
                user.id,
            )
    except Exception as exc:
        _logger.exception("Failed to delete project %s", session_id)
        raise HTTPException(status_code=503, detail="Database operation failed.") from exc

    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Project not found.")

    return Response(status_code=204)
