"""User profile API — get and update profile, onboarding status."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth import AuthUser, get_current_user
from app.db import get_pool

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["profile"])


class ProfileResponse(BaseModel):
    user_id: str
    full_name: str | None = None
    role: str | None = None
    institution: str | None = None
    research_area: str | None = None
    onboarding_completed: bool = False


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=200)
    role: str | None = Field(None, max_length=100)
    institution: str | None = Field(None, max_length=300)
    research_area: str | None = Field(None, max_length=200)


VALID_ROLES = {
    "medical_student",
    "resident_fellow",
    "junior_faculty",
    "senior_faculty",
    "phd_student",
    "cro_staff",
    "other",
}

VALID_RESEARCH_AREAS = {
    "clinical_medicine",
    "surgery",
    "public_health",
    "epidemiology",
    "nursing",
    "pharmacy",
    "other",
}


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user: AuthUser = Depends(get_current_user)) -> ProfileResponse:
    """Get the current user's profile. Creates a stub if none exists."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, full_name, role, institution, research_area, onboarding_completed "
            "FROM user_profiles WHERE user_id = $1",
            user.id,
        )
        if row:
            return ProfileResponse(**dict(row))

        # Auto-create stub profile on first access
        await conn.execute(
            "INSERT INTO user_profiles (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
            user.id,
        )
        return ProfileResponse(user_id=user.id)


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdate,
    user: AuthUser = Depends(get_current_user),
) -> ProfileResponse:
    """Update the current user's profile fields."""
    if body.role and body.role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail=f"Invalid role: {body.role}")
    if body.research_area and body.research_area not in VALID_RESEARCH_AREAS:
        raise HTTPException(
            status_code=422, detail=f"Invalid research_area: {body.research_area}"
        )

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Upsert: create if missing, then update provided fields
        await conn.execute(
            "INSERT INTO user_profiles (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
            user.id,
        )

        # Build dynamic SET clause for non-null fields only
        updates: list[str] = []
        values: list = []
        idx = 2  # $1 is user_id

        for field_name in ("full_name", "role", "institution", "research_area"):
            value = getattr(body, field_name)
            if value is not None:
                updates.append(f"{field_name} = ${idx}")
                values.append(value)
                idx += 1

        if not updates:
            raise HTTPException(status_code=422, detail="No fields to update")

        updates.append(f"updated_at = now() AT TIME ZONE 'Asia/Bangkok'")

        query = f"UPDATE user_profiles SET {', '.join(updates)} WHERE user_id = $1"
        await conn.execute(query, user.id, *values)

        row = await conn.fetchrow(
            "SELECT user_id, full_name, role, institution, research_area, onboarding_completed "
            "FROM user_profiles WHERE user_id = $1",
            user.id,
        )
        return ProfileResponse(**dict(row))


@router.post("/profile/complete-onboarding", response_model=ProfileResponse)
async def complete_onboarding(
    body: ProfileUpdate,
    user: AuthUser = Depends(get_current_user),
) -> ProfileResponse:
    """Save onboarding profile and mark onboarding as completed."""
    if body.role and body.role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail=f"Invalid role: {body.role}")
    if body.research_area and body.research_area not in VALID_RESEARCH_AREAS:
        raise HTTPException(
            status_code=422, detail=f"Invalid research_area: {body.research_area}"
        )

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO user_profiles (user_id, full_name, role, institution, research_area, onboarding_completed, updated_at)
            VALUES ($1, $2, $3, $4, $5, TRUE, now() AT TIME ZONE 'Asia/Bangkok')
            ON CONFLICT (user_id) DO UPDATE SET
                full_name = COALESCE($2, user_profiles.full_name),
                role = COALESCE($3, user_profiles.role),
                institution = COALESCE($4, user_profiles.institution),
                research_area = COALESCE($5, user_profiles.research_area),
                onboarding_completed = TRUE,
                updated_at = now() AT TIME ZONE 'Asia/Bangkok'
            """,
            user.id,
            body.full_name,
            body.role,
            body.institution,
            body.research_area,
        )

        row = await conn.fetchrow(
            "SELECT user_id, full_name, role, institution, research_area, onboarding_completed "
            "FROM user_profiles WHERE user_id = $1",
            user.id,
        )
        return ProfileResponse(**dict(row))
