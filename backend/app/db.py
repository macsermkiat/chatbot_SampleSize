from __future__ import annotations

import logging
from urllib.parse import urlparse

import asyncpg

from app.config import settings

_logger = logging.getLogger(__name__)
_pool: asyncpg.Pool | None = None


def _pool_kwargs() -> dict:
    """Build extra kwargs for asyncpg.create_pool based on the DSN."""
    kwargs: dict = {}
    parsed = urlparse(settings.database_dsn)
    hostname = parsed.hostname or ""

    # Supabase hosts require SSL
    if ".supabase.co" in hostname or ".supabase.com" in hostname:
        kwargs["ssl"] = "require"

    # Transaction-mode pooler (port 6543) needs statement_cache_size=0
    if parsed.port == 6543:
        kwargs["statement_cache_size"] = 0

    # TCP keepalive to prevent Supabase from dropping idle connections
    kwargs["server_settings"] = {
        "tcp_keepalives_idle": "30",
        "tcp_keepalives_interval": "10",
        "tcp_keepalives_count": "3",
    }
    kwargs["command_timeout"] = 60

    return kwargs


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        if not settings.has_database:
            raise RuntimeError("No DATABASE_URL configured")
        extra = _pool_kwargs()
        _logger.info("Creating asyncpg pool (ssl=%s)", extra.get("ssl", "off"))
        _pool = await asyncpg.create_pool(
            dsn=settings.database_dsn,
            min_size=2,
            max_size=10,
            **extra,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def check_db() -> bool:
    """Return True if the database is reachable."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception:
        return False
