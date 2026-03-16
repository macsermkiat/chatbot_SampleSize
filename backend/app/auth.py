"""Supabase JWT authentication for FastAPI."""

from __future__ import annotations

import logging

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import settings

_logger = logging.getLogger(__name__)

_security = HTTPBearer(auto_error=False)


class AuthUser(BaseModel):
    """Authenticated user extracted from a Supabase JWT."""

    id: str
    email: str
    role: str = "authenticated"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> AuthUser:
    """Validate Supabase JWT and return the authenticated user.

    Raises 401 if the token is missing, expired, or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not settings.supabase_jwt_secret:
        _logger.error("SUPABASE_JWT_SECRET is not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable.",
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        _logger.warning("Invalid JWT: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthUser(
        id=payload["sub"],
        email=payload.get("email", ""),
        role=payload.get("role", "authenticated"),
    )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> AuthUser | None:
    """Return the authenticated user if a valid token is present, else None.

    Use this for endpoints that work for both anonymous and authenticated users
    (e.g. chat during the transition period before auth is mandatory).
    """
    if credentials is None:
        return None

    if not settings.supabase_jwt_secret:
        return None

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return AuthUser(
            id=payload["sub"],
            email=payload.get("email", ""),
            role=payload.get("role", "authenticated"),
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        return None
