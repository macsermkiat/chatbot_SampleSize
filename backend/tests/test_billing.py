"""Tests for billing service and API endpoints."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.billing import (
    TIER_LIMITS,
    VARIANT_TIER_MAP,
    get_limit_for_tier,
    get_tier_for_variant,
)

_TEST_SECRET = "test-jwt-secret-256-bit-long-key!"
_WEBHOOK_SECRET = "test-webhook-secret"
VALID_UUID = "550e8400-e29b-41d4-a716-446655440000"


def _make_token(sub: str = VALID_UUID, email: str = "test@example.com") -> str:
    payload = {
        "sub": sub,
        "email": email,
        "role": "authenticated",
        "aud": "authenticated",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return pyjwt.encode(payload, _TEST_SECRET, algorithm="HS256")


def _sign_webhook(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


@pytest.fixture()
def mock_pool():
    pool = MagicMock()
    conn = MagicMock()
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=False)
    pool.acquire.return_value = conn
    return pool, conn


# ---------------------------------------------------------------------------
# Tier mapping unit tests
# ---------------------------------------------------------------------------


class TestTierMapping:
    def test_unknown_variant_returns_free(self):
        assert get_tier_for_variant("unknown-id") == "free"

    def test_free_tier_limit(self):
        assert get_limit_for_tier("free") == 5

    def test_researcher_tier_limit(self):
        assert get_limit_for_tier("researcher") == 50

    def test_pro_tier_unlimited(self):
        assert get_limit_for_tier("pro") is None

    def test_institutional_unlimited(self):
        assert get_limit_for_tier("institutional") is None

    def test_unknown_tier_defaults_to_5(self):
        assert get_limit_for_tier("nonexistent") == 5


# ---------------------------------------------------------------------------
# Billing API endpoint tests
# ---------------------------------------------------------------------------


class TestSubscriptionEndpoint:
    async def test_subscription_requires_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/billing/subscription")
        assert response.status_code == 401

    async def test_subscription_free_user(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)
        token = _make_token()

        with (
            patch("app.auth.settings") as auth_settings,
            patch("app.services.billing.get_pool", AsyncMock(return_value=pool)),
        ):
            auth_settings.supabase_jwt_secret = _TEST_SECRET
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/billing/subscription",
                    headers={"Authorization": f"Bearer {token}"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "free"


class TestUsageEndpoint:
    async def test_usage_requires_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/billing/usage")
        assert response.status_code == 401


class TestCheckoutEndpoint:
    async def test_checkout_requires_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/billing/checkout",
                json={"variant_id": "12345"},
            )
        assert response.status_code == 401

    async def test_checkout_requires_variant_id(self):
        token = _make_token()
        with patch("app.auth.settings") as auth_settings:
            auth_settings.supabase_jwt_secret = _TEST_SECRET
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/billing/checkout",
                    json={},
                    headers={"Authorization": f"Bearer {token}"},
                )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Webhook tests
# ---------------------------------------------------------------------------


class TestLemonSqueezyWebhook:
    async def test_invalid_signature_returns_403(self):
        payload = json.dumps({"data": {}}).encode()
        transport = ASGITransport(app=app)
        with patch("app.api.billing.settings") as billing_settings:
            billing_settings.lemonsqueezy_webhook_secret = _WEBHOOK_SECRET
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/webhooks/lemonsqueezy",
                    content=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Signature": "bad-signature",
                        "X-Event-Name": "subscription_created",
                    },
                )
        assert response.status_code == 403

    async def test_valid_signature_accepted(self, mock_pool):
        pool, conn = mock_pool
        conn.execute = AsyncMock()

        payload_dict = {
            "data": {
                "id": "sub_123",
                "attributes": {
                    "customer_id": "cust_456",
                    "variant_id": "var_789",
                    "status": "active",
                    "user_email": "test@example.com",
                    "renews_at": None,
                    "ends_at": None,
                },
            },
            "meta": {"custom_data": {"user_id": VALID_UUID}},
        }
        payload = json.dumps(payload_dict).encode()
        signature = _sign_webhook(payload, _WEBHOOK_SECRET)

        with (
            patch("app.api.billing.settings") as billing_settings,
            patch("app.api.billing.get_pool", AsyncMock(return_value=pool)),
        ):
            billing_settings.lemonsqueezy_webhook_secret = _WEBHOOK_SECRET
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/webhooks/lemonsqueezy",
                    content=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Signature": signature,
                        "X-Event-Name": "subscription_created",
                    },
                )

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
