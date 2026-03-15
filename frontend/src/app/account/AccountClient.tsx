"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { getSubscription, getUsage } from "@/lib/api";
import type { User } from "@supabase/supabase-js";

interface SubscriptionInfo {
  tier: string;
  status?: string;
  renews_at?: string;
  ends_at?: string;
  urls?: { customer_portal?: string; update_payment_method?: string };
}

interface UsageInfo {
  tier: string;
  query_count: number;
  query_limit: number | null;
  period_start?: string;
  period_end?: string;
  is_allowed: boolean;
}

const TIER_LABELS: Record<string, string> = {
  free: "Free",
  researcher: "Researcher",
  pro: "Pro",
  institutional: "Institutional",
};

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  active: { label: "Active", className: "bg-green-100 text-green-700" },
  past_due: { label: "Past Due", className: "bg-yellow-100 text-yellow-700" },
  cancelled: { label: "Cancelled", className: "bg-red-100 text-red-700" },
  paused: { label: "Paused", className: "bg-parchment-200 text-parchment-700" },
};

export default function AccountClient() {
  const [user, setUser] = useState<User | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [usage, setUsage] = useState<UsageInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const supabase = createClient();
      const { data } = await supabase.auth.getUser();

      if (!data.user) {
        window.location.href = "/login";
        return;
      }

      setUser(data.user);

      const [sub, usg] = await Promise.all([
        getSubscription().catch(() => ({ tier: "free" } as SubscriptionInfo)),
        getUsage().catch(
          () =>
            ({
              tier: "free",
              query_count: 0,
              query_limit: 5,
              is_allowed: true,
            }) as UsageInfo,
        ),
      ]);

      setSubscription(sub);
      setUsage(usg);
      setLoading(false);
    }

    load();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-parchment-100 flex items-center justify-center">
        <p className="text-parchment-500 font-display">Loading...</p>
      </div>
    );
  }

  const tierLabel = TIER_LABELS[subscription?.tier ?? "free"] ?? subscription?.tier ?? "Free";
  const statusInfo = STATUS_LABELS[subscription?.status ?? ""] ?? null;
  const usagePercent =
    usage?.query_limit && usage.query_limit > 0
      ? Math.min(100, Math.round((usage.query_count / usage.query_limit) * 100))
      : null;

  return (
    <div className="min-h-screen bg-parchment-100 py-16 px-4">
      <div className="max-w-2xl mx-auto space-y-8">
        {/* Back link */}
        <Link
          href="/"
          className="text-parchment-600 text-sm hover:text-parchment-800 inline-block"
        >
          &larr; Back to app
        </Link>

        <h1 className="font-display text-3xl font-semibold text-ink-900">
          Account & Billing
        </h1>

        {/* Profile */}
        <section className="bg-white/80 backdrop-blur-sm border border-parchment-200 rounded-xl p-6">
          <h2 className="font-display text-lg font-semibold text-ink-800 mb-3">
            Profile
          </h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-parchment-500">Email</dt>
              <dd className="text-ink-800 font-medium">{user?.email}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-parchment-500">User ID</dt>
              <dd className="text-ink-600 font-mono text-xs">
                {user?.id.slice(0, 12)}...
              </dd>
            </div>
          </dl>
        </section>

        {/* Subscription */}
        <section className="bg-white/80 backdrop-blur-sm border border-parchment-200 rounded-xl p-6">
          <h2 className="font-display text-lg font-semibold text-ink-800 mb-3">
            Subscription
          </h2>
          <div className="flex items-center gap-3 mb-4">
            <span className="text-xl font-semibold text-ink-900">
              {tierLabel}
            </span>
            {statusInfo && (
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusInfo.className}`}
              >
                {statusInfo.label}
              </span>
            )}
          </div>

          {subscription?.renews_at && (
            <p className="text-sm text-parchment-600 mb-2">
              Renews:{" "}
              {new Date(subscription.renews_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          )}

          {subscription?.ends_at && (
            <p className="text-sm text-red-600 mb-2">
              Ends:{" "}
              {new Date(subscription.ends_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          )}

          <div className="flex gap-3 mt-4">
            {subscription?.tier === "free" ? (
              <Link
                href="/pricing"
                className="px-4 py-2 bg-parchment-800 text-white text-sm rounded-lg hover:bg-parchment-900 transition-colors"
              >
                Upgrade Plan
              </Link>
            ) : (
              <>
                {subscription?.urls?.customer_portal && (
                  <a
                    href={subscription.urls.customer_portal}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-parchment-800 text-white text-sm rounded-lg hover:bg-parchment-900 transition-colors"
                  >
                    Manage Subscription
                  </a>
                )}
                {subscription?.urls?.update_payment_method && (
                  <a
                    href={subscription.urls.update_payment_method}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 border border-parchment-300 text-parchment-700 text-sm rounded-lg hover:bg-parchment-50 transition-colors"
                  >
                    Update Payment
                  </a>
                )}
              </>
            )}
          </div>
        </section>

        {/* Usage */}
        <section className="bg-white/80 backdrop-blur-sm border border-parchment-200 rounded-xl p-6">
          <h2 className="font-display text-lg font-semibold text-ink-800 mb-3">
            Usage This Period
          </h2>
          <div className="flex items-baseline gap-2 mb-3">
            <span className="text-2xl font-semibold text-ink-900">
              {usage?.query_count ?? 0}
            </span>
            <span className="text-parchment-500 text-sm">
              / {usage?.query_limit ?? "unlimited"} queries
            </span>
          </div>

          {usagePercent !== null && (
            <div className="w-full bg-parchment-200 rounded-full h-2 mb-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  usagePercent >= 90
                    ? "bg-red-500"
                    : usagePercent >= 70
                      ? "bg-yellow-500"
                      : "bg-green-500"
                }`}
                style={{ width: `${usagePercent}%` }}
              />
            </div>
          )}

          {usage?.period_end && (
            <p className="text-xs text-parchment-500">
              Resets:{" "}
              {new Date(usage.period_end).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          )}

          {!usage?.is_allowed && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">
                You have reached your query limit.{" "}
                <Link
                  href="/pricing"
                  className="font-medium underline hover:text-red-800"
                >
                  Upgrade your plan
                </Link>{" "}
                for more queries.
              </p>
            </div>
          )}
        </section>

        {/* Sign Out */}
        <section className="text-center">
          <button
            onClick={async () => {
              const supabase = createClient();
              await supabase.auth.signOut();
              window.location.href = "/login";
            }}
            className="text-sm text-red-600 hover:text-red-700 font-medium"
          >
            Sign Out
          </button>
        </section>
      </div>
    </div>
  );
}
