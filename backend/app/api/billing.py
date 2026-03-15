"""Billing API — checkout, subscription management, usage, and LemonSqueezy webhooks."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth import AuthUser, get_current_user
from app.config import settings
from app.db import get_pool
from app.services.billing import (
    create_checkout,
    get_current_usage,
    get_subscription_portal_urls,
    get_tier_for_variant,
    get_user_subscription,
)

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["billing"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class CheckoutRequest(BaseModel):
    variant_id: str = Field(..., min_length=1)


class CheckoutResponse(BaseModel):
    checkout_url: str


class SubscriptionResponse(BaseModel):
    tier: str
    status: str | None = None
    variant_id: str | None = None
    renews_at: str | None = None
    ends_at: str | None = None
    urls: dict[str, str] = Field(default_factory=dict)


class UsageResponse(BaseModel):
    tier: str
    query_count: int
    query_limit: int | None
    period_start: str
    period_end: str
    is_allowed: bool


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------


@router.post("/billing/checkout", response_model=CheckoutResponse)
async def api_create_checkout(
    body: CheckoutRequest,
    user: AuthUser = Depends(get_current_user),
):
    """Create a LemonSqueezy checkout session for the authenticated user."""
    try:
        url = await create_checkout(body.variant_id, user.id, user.email)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return CheckoutResponse(checkout_url=url)


# ---------------------------------------------------------------------------
# Subscription info
# ---------------------------------------------------------------------------


@router.get("/billing/subscription", response_model=SubscriptionResponse)
async def api_get_subscription(user: AuthUser = Depends(get_current_user)):
    """Get the authenticated user's current subscription and portal URLs."""
    sub = await get_user_subscription(user.id)

    if sub is None:
        return SubscriptionResponse(tier="free")

    urls = await get_subscription_portal_urls(sub["ls_subscription_id"])

    return SubscriptionResponse(
        tier=get_tier_for_variant(str(sub["variant_id"])),
        status=sub["status"],
        variant_id=str(sub["variant_id"]),
        renews_at=sub["renews_at"].isoformat() if sub["renews_at"] else None,
        ends_at=sub["ends_at"].isoformat() if sub["ends_at"] else None,
        urls=urls,
    )


# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------


@router.get("/billing/usage", response_model=UsageResponse)
async def api_get_usage(user: AuthUser = Depends(get_current_user)):
    """Get the authenticated user's query usage for the current billing period."""
    usage = await get_current_usage(user.id)
    return UsageResponse(**usage)


# ---------------------------------------------------------------------------
# LemonSqueezy Webhooks (no auth — verified by signature)
# ---------------------------------------------------------------------------


def _verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify LemonSqueezy webhook HMAC-SHA256 signature."""
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


@router.post("/webhooks/lemonsqueezy")
async def handle_lemonsqueezy_webhook(request: Request) -> dict[str, str]:
    """Process LemonSqueezy webhook events with signature verification."""
    raw_body = await request.body()
    signature = request.headers.get("X-Signature", "")
    event_name = request.headers.get("X-Event-Name", "")

    if not _verify_signature(raw_body, signature, settings.lemonsqueezy_webhook_secret):
        _logger.warning("Invalid webhook signature for event: %s", event_name)
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload: dict[str, Any] = json.loads(raw_body)

    # Store raw event for reliability
    try:
        pool = await get_pool()
        async with pool.acquire(timeout=5) as conn:
            await conn.execute(
                """
                INSERT INTO webhook_events (event_name, body, processed)
                VALUES ($1, $2, false)
                """,
                event_name,
                json.dumps(payload),
            )
    except Exception:
        _logger.exception("Failed to store webhook event: %s", event_name)

    # Route to handler
    handler = _EVENT_HANDLERS.get(event_name)
    if handler is not None:
        try:
            await handler(payload)
        except Exception:
            _logger.exception("Error processing webhook: %s", event_name)

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Webhook event handlers
# ---------------------------------------------------------------------------


async def _handle_subscription_created(payload: dict[str, Any]) -> None:
    data = payload["data"]
    attrs = data["attributes"]
    custom_data = payload.get("meta", {}).get("custom_data", {})

    user_id = custom_data.get("user_id")
    ls_subscription_id = str(data["id"])
    ls_customer_id = str(attrs["customer_id"])
    variant_id = str(attrs["variant_id"])
    status = attrs["status"]
    email = attrs.get("user_email", "")
    renews_at = attrs.get("renews_at")
    ends_at = attrs.get("ends_at")

    pool = await get_pool()
    async with pool.acquire(timeout=5) as conn:
        await conn.execute(
            """
            INSERT INTO subscriptions
                (user_id, ls_subscription_id, ls_customer_id, variant_id,
                 status, email, renews_at, ends_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (ls_subscription_id) DO UPDATE SET
                status = EXCLUDED.status,
                variant_id = EXCLUDED.variant_id,
                renews_at = EXCLUDED.renews_at,
                ends_at = EXCLUDED.ends_at,
                updated_at = now() AT TIME ZONE 'Asia/Bangkok'
            """,
            user_id,
            ls_subscription_id,
            ls_customer_id,
            variant_id,
            status,
            email,
            renews_at,
            ends_at,
        )

    _logger.info("Subscription created: %s for user %s (tier: %s)", ls_subscription_id, user_id, get_tier_for_variant(variant_id))


async def _handle_subscription_updated(payload: dict[str, Any]) -> None:
    data = payload["data"]
    attrs = data["attributes"]
    ls_subscription_id = str(data["id"])

    pool = await get_pool()
    async with pool.acquire(timeout=5) as conn:
        await conn.execute(
            """
            UPDATE subscriptions SET
                status = $1,
                variant_id = $2,
                renews_at = $3,
                ends_at = $4,
                is_paused = $5,
                updated_at = now() AT TIME ZONE 'Asia/Bangkok'
            WHERE ls_subscription_id = $6
            """,
            attrs["status"],
            str(attrs["variant_id"]),
            attrs.get("renews_at"),
            attrs.get("ends_at"),
            attrs.get("pause") is not None,
            ls_subscription_id,
        )


async def _handle_subscription_cancelled(payload: dict[str, Any]) -> None:
    data = payload["data"]
    attrs = data["attributes"]
    ls_subscription_id = str(data["id"])

    pool = await get_pool()
    async with pool.acquire(timeout=5) as conn:
        await conn.execute(
            """
            UPDATE subscriptions SET
                status = 'cancelled',
                ends_at = $1,
                updated_at = now() AT TIME ZONE 'Asia/Bangkok'
            WHERE ls_subscription_id = $2
            """,
            attrs.get("ends_at"),
            ls_subscription_id,
        )


async def _handle_payment_failed(payload: dict[str, Any]) -> None:
    data = payload["data"]
    ls_subscription_id = str(data["attributes"].get("subscription_id", data.get("id", "")))

    pool = await get_pool()
    async with pool.acquire(timeout=5) as conn:
        await conn.execute(
            """
            UPDATE subscriptions SET
                status = 'past_due',
                updated_at = now() AT TIME ZONE 'Asia/Bangkok'
            WHERE ls_subscription_id = $1
            """,
            ls_subscription_id,
        )


_EVENT_HANDLERS: dict[str, Any] = {
    "subscription_created": _handle_subscription_created,
    "subscription_updated": _handle_subscription_updated,
    "subscription_cancelled": _handle_subscription_cancelled,
    "subscription_resumed": _handle_subscription_updated,
    "subscription_expired": _handle_subscription_cancelled,
    "subscription_paused": _handle_subscription_updated,
    "subscription_unpaused": _handle_subscription_updated,
    "subscription_payment_success": _handle_subscription_updated,
    "subscription_payment_failed": _handle_payment_failed,
    "subscription_payment_recovered": _handle_subscription_updated,
}
