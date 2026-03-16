"""LemonSqueezy billing service — checkout creation, subscription queries, usage metering."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.config import settings
from app.db import get_pool

_logger = logging.getLogger(__name__)

_LS_API = "https://api.lemonsqueezy.com/v1"


def _ls_headers() -> dict[str, str]:
    return {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "Authorization": f"Bearer {settings.lemonsqueezy_api_key}",
    }


# ---------------------------------------------------------------------------
# Tier mapping — populate variant IDs from LemonSqueezy dashboard
# ---------------------------------------------------------------------------

# Map LemonSqueezy variant IDs to tier names.
# Update these after creating products in the LemonSqueezy dashboard.
VARIANT_TIER_MAP: dict[str, str] = {
    # "123456": "researcher",
    # "123457": "researcher_annual",
    # "123458": "pro",
    # "123459": "pro_annual",
    # "123460": "institutional",
}

TIER_LIMITS: dict[str, int | None] = {
    "free": 5,
    "researcher": 50,
    "researcher_annual": 50,
    "pro": None,  # unlimited
    "pro_annual": None,
    "institutional": None,
}


def get_tier_for_variant(variant_id: str) -> str:
    return VARIANT_TIER_MAP.get(str(variant_id), "free")


def get_limit_for_tier(tier: str) -> int | None:
    return TIER_LIMITS.get(tier, 5)


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------


async def create_checkout(variant_id: str, user_id: str, user_email: str) -> str:
    """Create a LemonSqueezy checkout and return the checkout URL."""
    body: dict[str, Any] = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_options": {
                    "embed": True,
                    "media": False,
                    "desc": True,
                },
                "checkout_data": {
                    "email": user_email,
                    "custom": {"user_id": user_id},
                },
            },
            "relationships": {
                "store": {
                    "data": {
                        "type": "stores",
                        "id": settings.lemonsqueezy_store_id,
                    },
                },
                "variant": {
                    "data": {
                        "type": "variants",
                        "id": variant_id,
                    },
                },
            },
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{_LS_API}/checkouts", json=body, headers=_ls_headers())

    if resp.status_code != 200:
        _logger.error("LemonSqueezy checkout creation failed: %s %s", resp.status_code, resp.text)
        raise RuntimeError("Failed to create checkout")

    return resp.json()["data"]["attributes"]["url"]


# ---------------------------------------------------------------------------
# Subscription queries
# ---------------------------------------------------------------------------


async def get_user_subscription(user_id: str) -> dict[str, Any] | None:
    """Get the active subscription for a user, or None if free tier."""
    pool = await get_pool()
    async with pool.acquire(timeout=5) as conn:
        row = await conn.fetchrow(
            """
            SELECT ls_subscription_id, variant_id, status, renews_at, ends_at, is_paused
            FROM subscriptions
            WHERE user_id = $1 AND status IN ('active', 'on_trial')
            ORDER BY created_at DESC LIMIT 1
            """,
            user_id,
        )

    if row is None:
        return None

    return dict(row)


async def get_subscription_portal_urls(ls_subscription_id: str) -> dict[str, str]:
    """Fetch customer portal URLs from LemonSqueezy API."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{_LS_API}/subscriptions/{ls_subscription_id}",
            headers=_ls_headers(),
        )

    if resp.status_code != 200:
        return {}

    urls = resp.json()["data"]["attributes"].get("urls", {})
    return {
        "customer_portal": urls.get("customer_portal", ""),
        "update_payment_method": urls.get("update_payment_method", ""),
    }


# ---------------------------------------------------------------------------
# Usage metering
# ---------------------------------------------------------------------------


async def get_current_usage(user_id: str) -> dict[str, Any]:
    """Get query usage for the current billing period."""
    pool = await get_pool()
    async with pool.acquire(timeout=5) as conn:
        sub = await conn.fetchrow(
            """
            SELECT variant_id, renews_at, created_at
            FROM subscriptions
            WHERE user_id = $1 AND status IN ('active', 'on_trial')
            ORDER BY created_at DESC LIMIT 1
            """,
            user_id,
        )

        tier = "free"
        if sub is not None:
            tier = get_tier_for_variant(str(sub["variant_id"]))

        now = datetime.now()
        if sub is not None and sub["renews_at"] is not None:
            period_end = sub["renews_at"]
            period_start = period_end - timedelta(days=30)
        else:
            period_start = now - timedelta(days=30)
            period_end = now

        count = await conn.fetchval(
            """
            SELECT COALESCE(query_count, 0)
            FROM usage_tracking
            WHERE user_id = $1 AND period_start >= $2
            ORDER BY period_start DESC LIMIT 1
            """,
            user_id,
            period_start,
        ) or 0

    limit = get_limit_for_tier(tier)

    return {
        "tier": tier,
        "query_count": count,
        "query_limit": limit,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat() if isinstance(period_end, datetime) else str(period_end),
        "is_allowed": limit is None or count < limit,
    }


async def increment_usage(user_id: str) -> bool:
    """Atomically increment query count and enforce the limit.

    Returns True if the query is allowed, False if the limit is reached.
    Uses a single atomic SQL statement to prevent race conditions.
    """
    usage = await get_current_usage(user_id)
    if not usage["is_allowed"]:
        return False

    limit = usage["query_limit"]
    pool = await get_pool()
    async with pool.acquire(timeout=5) as conn:
        period_start = datetime.fromisoformat(usage["period_start"])
        period_end = datetime.fromisoformat(usage["period_end"])

        if limit is not None:
            # Atomic increment with limit guard -- prevents concurrent bypass
            result = await conn.fetchval(
                """
                INSERT INTO usage_tracking (user_id, period_start, period_end, query_count)
                VALUES ($1, $2, $3, 1)
                ON CONFLICT (user_id, period_start) DO UPDATE SET
                    query_count = usage_tracking.query_count + 1
                WHERE usage_tracking.query_count < $4
                RETURNING query_count
                """,
                user_id,
                period_start,
                period_end,
                limit,
            )
            return result is not None
        else:
            # Unlimited tier -- just increment
            await conn.execute(
                """
                INSERT INTO usage_tracking (user_id, period_start, period_end, query_count)
                VALUES ($1, $2, $3, 1)
                ON CONFLICT (user_id, period_start) DO UPDATE SET
                    query_count = usage_tracking.query_count + 1
                """,
                user_id,
                period_start,
                period_end,
            )
            return True
