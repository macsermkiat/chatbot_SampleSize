"""Supabase JWT authentication for FastAPI.

Supports both HS256 (legacy) and ES256 (P-256) JWT signing.
When SUPABASE_URL is configured and the JWT uses ES256, the public key
is fetched from the Supabase JWKS endpoint automatically.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import settings

_logger = logging.getLogger(__name__)

_security = HTTPBearer(auto_error=False)

# JWKS client (cached; fetches public keys from Supabase GoTrue)
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient | None:
    """Return a cached PyJWKClient for the Supabase JWKS endpoint."""
    global _jwks_client
    if _jwks_client is not None:
        return _jwks_client

    if not settings.supabase_url:
        return None

    jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    _jwks_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)
    _logger.info("JWKS client configured: %s", jwks_url)
    return _jwks_client


def _decode_jwt(token: str) -> dict:
    """Decode and validate a Supabase JWT, auto-detecting HS256 vs ES256."""
    # Peek at the token header to determine the algorithm
    try:
        header = jwt.get_unverified_header(token)
    except jwt.DecodeError as exc:
        raise jwt.InvalidTokenError(f"Malformed JWT header: {exc}") from exc

    alg = header.get("alg", "HS256")

    if alg == "ES256":
        jwks = _get_jwks_client()
        if jwks is None:
            raise jwt.InvalidTokenError(
                "ES256 JWT received but SUPABASE_URL is not configured for JWKS lookup"
            )
        signing_key = jwks.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )

    # HS256 fallback (legacy Supabase projects)
    if not settings.supabase_jwt_secret:
        raise jwt.InvalidTokenError("HS256 JWT received but SUPABASE_JWT_SECRET is not configured")

    return jwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=["HS256"],
        audience="authenticated",
    )


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

    if not settings.supabase_jwt_secret and not settings.supabase_url:
        _logger.error("Neither SUPABASE_JWT_SECRET nor SUPABASE_URL is configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable.",
        )

    try:
        payload = _decode_jwt(credentials.credentials)
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

    if not settings.supabase_jwt_secret and not settings.supabase_url:
        return None

    try:
        payload = _decode_jwt(credentials.credentials)
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
