"""Tests for billing service and API endpoints."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.billing import (
    PROJECT_LIMITS,
    TIER_LIMITS,
    VARIANT_TIER_MAP,
    get_current_usage,
    get_limit_for_tier,
    get_project_limit_for_tier,
    get_project_usage,
    get_tier_for_variant,
    increment_usage,
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
    """Query limit tier mapping."""

    def test_unknown_variant_returns_free(self):
        assert get_tier_for_variant("unknown-id") == "free"

    def test_free_tier_limit(self):
        assert get_limit_for_tier("free") == 5

    def test_researcher_tier_limit(self):
        assert get_limit_for_tier("researcher") == 50

    def test_researcher_annual_tier_limit(self):
        assert get_limit_for_tier("researcher_annual") == 50

    def test_pro_tier_unlimited(self):
        assert get_limit_for_tier("pro") is None

    def test_pro_annual_unlimited(self):
        assert get_limit_for_tier("pro_annual") is None

    def test_institutional_unlimited(self):
        assert get_limit_for_tier("institutional") is None

    def test_unknown_tier_defaults_to_5(self):
        assert get_limit_for_tier("nonexistent") == 5

    def test_empty_string_tier_defaults_to_5(self):
        assert get_limit_for_tier("") == 5


class TestProjectLimitMapping:
    """Project limit tier mapping."""

    def test_free_tier_project_limit(self):
        assert get_project_limit_for_tier("free") == 1

    def test_researcher_tier_project_limit(self):
        assert get_project_limit_for_tier("researcher") == 3

    def test_researcher_annual_tier_project_limit(self):
        assert get_project_limit_for_tier("researcher_annual") == 3

    def test_pro_tier_project_limit(self):
        assert get_project_limit_for_tier("pro") == 10

    def test_pro_annual_tier_project_limit(self):
        assert get_project_limit_for_tier("pro_annual") == 10

    def test_institutional_unlimited_projects(self):
        assert get_project_limit_for_tier("institutional") is None

    def test_unknown_tier_defaults_to_1(self):
        assert get_project_limit_for_tier("nonexistent") == 1

    def test_empty_string_tier_defaults_to_1(self):
        assert get_project_limit_for_tier("") == 1

    def test_project_limits_dict_completeness(self):
        """Every tier in TIER_LIMITS should also have a PROJECT_LIMITS entry."""
        for tier in TIER_LIMITS:
            assert tier in PROJECT_LIMITS, f"Missing PROJECT_LIMITS entry for tier: {tier}"


# ---------------------------------------------------------------------------
# get_project_usage service tests
# ---------------------------------------------------------------------------


class TestGetProjectUsage:
    """Tests for get_project_usage() -- project count vs tier limit."""

    async def test_free_user_zero_projects(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)  # no subscription
        conn.fetchval = AsyncMock(return_value=0)  # 0 projects

        with patch("app.services.billing.get_pool", AsyncMock(return_value=pool)):
            result = await get_project_usage(VALID_UUID)

        assert result["tier"] == "free"
        assert result["project_count"] == 0
        assert result["project_limit"] == 1
        assert result["can_create_project"] is True

    async def test_free_user_at_limit(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)
        conn.fetchval = AsyncMock(return_value=1)  # 1 project = at limit

        with patch("app.services.billing.get_pool", AsyncMock(return_value=pool)):
            result = await get_project_usage(VALID_UUID)

        assert result["project_count"] == 1
        assert result["project_limit"] == 1
        assert result["can_create_project"] is False

    async def test_free_user_over_limit(self, mock_pool):
        """Edge case: user has more projects than limit (grandfathered in)."""
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)
        conn.fetchval = AsyncMock(return_value=5)

        with patch("app.services.billing.get_pool", AsyncMock(return_value=pool)):
            result = await get_project_usage(VALID_UUID)

        assert result["project_count"] == 5
        assert result["project_limit"] == 1
        assert result["can_create_project"] is False

    async def test_researcher_under_limit(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value={"variant_id": "var_123"})
        conn.fetchval = AsyncMock(return_value=2)

        with (
            patch("app.services.billing.get_pool", AsyncMock(return_value=pool)),
            patch("app.services.billing.get_tier_for_variant", return_value="researcher"),
        ):
            result = await get_project_usage(VALID_UUID)

        assert result["tier"] == "researcher"
        assert result["project_count"] == 2
        assert result["project_limit"] == 3
        assert result["can_create_project"] is True

    async def test_researcher_at_limit(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value={"variant_id": "var_123"})
        conn.fetchval = AsyncMock(return_value=3)

        with (
            patch("app.services.billing.get_pool", AsyncMock(return_value=pool)),
            patch("app.services.billing.get_tier_for_variant", return_value="researcher"),
        ):
            result = await get_project_usage(VALID_UUID)

        assert result["project_count"] == 3
        assert result["project_limit"] == 3
        assert result["can_create_project"] is False

    async def test_pro_under_limit(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value={"variant_id": "var_456"})
        conn.fetchval = AsyncMock(return_value=9)

        with (
            patch("app.services.billing.get_pool", AsyncMock(return_value=pool)),
            patch("app.services.billing.get_tier_for_variant", return_value="pro"),
        ):
            result = await get_project_usage(VALID_UUID)

        assert result["project_count"] == 9
        assert result["project_limit"] == 10
        assert result["can_create_project"] is True

    async def test_pro_at_limit(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value={"variant_id": "var_456"})
        conn.fetchval = AsyncMock(return_value=10)

        with (
            patch("app.services.billing.get_pool", AsyncMock(return_value=pool)),
            patch("app.services.billing.get_tier_for_variant", return_value="pro"),
        ):
            result = await get_project_usage(VALID_UUID)

        assert result["project_count"] == 10
        assert result["project_limit"] == 10
        assert result["can_create_project"] is False

    async def test_institutional_unlimited(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value={"variant_id": "var_789"})
        conn.fetchval = AsyncMock(return_value=100)

        with (
            patch("app.services.billing.get_pool", AsyncMock(return_value=pool)),
            patch("app.services.billing.get_tier_for_variant", return_value="institutional"),
        ):
            result = await get_project_usage(VALID_UUID)

        assert result["project_count"] == 100
        assert result["project_limit"] is None
        assert result["can_create_project"] is True

    async def test_null_count_treated_as_zero(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)
        conn.fetchval = AsyncMock(return_value=None)  # COUNT returns None

        with patch("app.services.billing.get_pool", AsyncMock(return_value=pool)):
            result = await get_project_usage(VALID_UUID)

        assert result["project_count"] == 0
        assert result["can_create_project"] is True


# ---------------------------------------------------------------------------
# get_current_usage service tests
# ---------------------------------------------------------------------------


class TestGetCurrentUsage:
    """Tests for get_current_usage() -- query metering."""

    async def test_free_user_zero_queries(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)
        conn.fetchval = AsyncMock(return_value=0)

        with patch("app.services.billing.get_pool", AsyncMock(return_value=pool)):
            result = await get_current_usage(VALID_UUID)

        assert result["tier"] == "free"
        assert result["query_count"] == 0
        assert result["query_limit"] == 5
        assert result["is_allowed"] is True

    async def test_free_user_at_limit(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)
        conn.fetchval = AsyncMock(return_value=5)

        with patch("app.services.billing.get_pool", AsyncMock(return_value=pool)):
            result = await get_current_usage(VALID_UUID)

        assert result["query_count"] == 5
        assert result["query_limit"] == 5
        assert result["is_allowed"] is False

    async def test_free_user_over_limit(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)
        conn.fetchval = AsyncMock(return_value=10)

        with patch("app.services.billing.get_pool", AsyncMock(return_value=pool)):
            result = await get_current_usage(VALID_UUID)

        assert result["query_count"] == 10
        assert result["is_allowed"] is False

    async def test_unlimited_tier_always_allowed(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value={"variant_id": "var_pro", "renews_at": None, "created_at": datetime.now()})
        conn.fetchval = AsyncMock(return_value=9999)

        with (
            patch("app.services.billing.get_pool", AsyncMock(return_value=pool)),
            patch("app.services.billing.get_tier_for_variant", return_value="pro"),
        ):
            result = await get_current_usage(VALID_UUID)

        assert result["tier"] == "pro"
        assert result["query_limit"] is None
        assert result["is_allowed"] is True

    async def test_period_calculation_with_renews_at(self, mock_pool):
        pool, conn = mock_pool
        renews_at = datetime(2026, 4, 15, 12, 0, 0)
        conn.fetchrow = AsyncMock(return_value={
            "variant_id": "var_res",
            "renews_at": renews_at,
            "created_at": datetime.now(),
        })
        conn.fetchval = AsyncMock(return_value=10)

        with (
            patch("app.services.billing.get_pool", AsyncMock(return_value=pool)),
            patch("app.services.billing.get_tier_for_variant", return_value="researcher"),
        ):
            result = await get_current_usage(VALID_UUID)

        expected_start = (renews_at - timedelta(days=30)).isoformat()
        assert result["period_start"] == expected_start
        assert result["period_end"] == renews_at.isoformat()

    async def test_period_calculation_without_subscription(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)
        conn.fetchval = AsyncMock(return_value=0)

        with patch("app.services.billing.get_pool", AsyncMock(return_value=pool)):
            result = await get_current_usage(VALID_UUID)

        # Should have valid period_start and period_end
        assert "period_start" in result
        assert "period_end" in result

    async def test_null_query_count_treated_as_zero(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)
        conn.fetchval = AsyncMock(return_value=None)

        with patch("app.services.billing.get_pool", AsyncMock(return_value=pool)):
            result = await get_current_usage(VALID_UUID)

        assert result["query_count"] == 0
        assert result["is_allowed"] is True

    async def test_exactly_one_below_limit(self, mock_pool):
        """4/5 queries used -- still allowed."""
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)
        conn.fetchval = AsyncMock(return_value=4)

        with patch("app.services.billing.get_pool", AsyncMock(return_value=pool)):
            result = await get_current_usage(VALID_UUID)

        assert result["query_count"] == 4
        assert result["is_allowed"] is True

    async def test_researcher_at_80_percent(self, mock_pool):
        """40/50 queries -- allowed but nearing limit."""
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value={"variant_id": "var_res", "renews_at": None, "created_at": datetime.now()})
        conn.fetchval = AsyncMock(return_value=40)

        with (
            patch("app.services.billing.get_pool", AsyncMock(return_value=pool)),
            patch("app.services.billing.get_tier_for_variant", return_value="researcher"),
        ):
            result = await get_current_usage(VALID_UUID)

        assert result["query_count"] == 40
        assert result["query_limit"] == 50
        assert result["is_allowed"] is True


# ---------------------------------------------------------------------------
# increment_usage service tests
# ---------------------------------------------------------------------------


class TestIncrementUsage:
    """Tests for increment_usage() -- atomic query count enforcement."""

    async def test_increment_allowed_limited_tier(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)
        conn.fetchval = AsyncMock(side_effect=[0, 1])  # get_current_usage count, then increment result
        conn.execute = AsyncMock()

        with patch("app.services.billing.get_pool", AsyncMock(return_value=pool)):
            result = await increment_usage(VALID_UUID)

        assert result is True

    async def test_increment_blocked_at_limit(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)
        conn.fetchval = AsyncMock(return_value=5)  # at limit

        with patch("app.services.billing.get_pool", AsyncMock(return_value=pool)):
            result = await increment_usage(VALID_UUID)

        assert result is False

    async def test_increment_unlimited_tier(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value={"variant_id": "var_pro", "renews_at": None, "created_at": datetime.now()})
        conn.fetchval = AsyncMock(return_value=0)
        conn.execute = AsyncMock()

        with (
            patch("app.services.billing.get_pool", AsyncMock(return_value=pool)),
            patch("app.services.billing.get_tier_for_variant", return_value="pro"),
        ):
            result = await increment_usage(VALID_UUID)

        assert result is True

    async def test_increment_returns_false_when_race_condition(self, mock_pool):
        """Atomic guard: fetchval returns None when concurrent increment fills the limit."""
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)
        # First call: get_current_usage shows 4/5 (allowed)
        # Second call: atomic increment fails (returns None -- someone else got the last slot)
        conn.fetchval = AsyncMock(side_effect=[4, None])

        with patch("app.services.billing.get_pool", AsyncMock(return_value=pool)):
            result = await increment_usage(VALID_UUID)

        assert result is False


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

    async def test_usage_returns_query_and_project_info(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)  # free tier
        conn.fetchval = AsyncMock(side_effect=[
            0,   # get_current_usage: query count
            None,  # get_project_usage: sub lookup (fetchrow returns None, this is for fetchval)
            2,   # get_project_usage: project count
        ])
        token = _make_token()

        with (
            patch("app.auth.settings") as auth_settings,
            patch("app.services.billing.get_pool", AsyncMock(return_value=pool)),
        ):
            auth_settings.supabase_jwt_secret = _TEST_SECRET
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/billing/usage",
                    headers={"Authorization": f"Bearer {token}"},
                )

        assert response.status_code == 200
        data = response.json()
        # Query usage fields
        assert "tier" in data
        assert "query_count" in data
        assert "query_limit" in data
        assert "is_allowed" in data
        assert "period_start" in data
        assert "period_end" in data
        # Project usage fields
        assert "project_count" in data
        assert "project_limit" in data
        assert "can_create_project" in data

    async def test_usage_free_tier_defaults(self, mock_pool):
        pool, conn = mock_pool
        conn.fetchrow = AsyncMock(return_value=None)
        conn.fetchval = AsyncMock(return_value=0)
        token = _make_token()

        with (
            patch("app.auth.settings") as auth_settings,
            patch("app.services.billing.get_pool", AsyncMock(return_value=pool)),
        ):
            auth_settings.supabase_jwt_secret = _TEST_SECRET
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/billing/usage",
                    headers={"Authorization": f"Bearer {token}"},
                )

        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "free"
        assert data["query_limit"] == 5
        assert data["project_limit"] == 1


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
