"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { getUsage } from "@/lib/api";

interface UsageData {
  tier: string;
  query_count: number;
  query_limit: number | null;
  is_allowed: boolean;
  period_end?: string;
}

const TIER_UPGRADE: Record<string, { next: string; label: string }> = {
  free: { next: "Researcher", label: "50 queries/month" },
  researcher: { next: "Pro", label: "unlimited queries" },
  researcher_annual: { next: "Pro", label: "unlimited queries" },
};

/**
 * Custom event name for triggering a usage data refresh.
 * Dispatched by HomeClient after each completed query.
 */
const REFRESH_EVENT = "protocol:refresh-usage";

/** Dispatch a refresh event to update all usage-aware components. */
export function dispatchUsageRefresh(): void {
  window.dispatchEvent(new Event(REFRESH_EVENT));
}

function useQueryUsage() {
  const [usage, setUsage] = useState<UsageData | null>(null);
  const mountedRef = useRef(true);

  const fetchUsage = useCallback(async () => {
    try {
      const data = await getUsage();
      if (mountedRef.current) setUsage(data);
    } catch {
      // Silently fail
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    fetchUsage();
    return () => {
      mountedRef.current = false;
    };
  }, [fetchUsage]);

  // Listen for refresh events
  useEffect(() => {
    const handler = () => {
      fetchUsage();
    };
    window.addEventListener(REFRESH_EVENT, handler);
    return () => window.removeEventListener(REFRESH_EVENT, handler);
  }, [fetchUsage]);

  // Periodic refresh every 60s
  useEffect(() => {
    const interval = setInterval(fetchUsage, 60_000);
    return () => clearInterval(interval);
  }, [fetchUsage]);

  return { usage, refresh: fetchUsage };
}

/**
 * Subtle inline counter for the header: "12 remaining"
 * Returns null for unlimited tiers or when not loaded.
 */
export function QueryBadge() {
  const { usage } = useQueryUsage();

  if (!usage || usage.query_limit === null) return null;

  const remaining = Math.max(0, usage.query_limit - usage.query_count);

  return (
    <span
      className="text-caption text-ink-400 font-display tabular-nums"
      title={`${remaining} of ${usage.query_limit} queries remaining this month`}
    >
      {remaining} remaining
    </span>
  );
}

/**
 * Warning banner shown between header and content.
 * Appears at 80% usage, last query, and exhaustion.
 * Dismissible for soft/last-query warnings; always visible when exhausted.
 */
export function QueryWarningBanner() {
  const { usage } = useQueryUsage();
  const [dismissed, setDismissed] = useState(false);

  if (!usage || usage.query_limit === null) return null;

  const remaining = Math.max(0, usage.query_limit - usage.query_count);
  const percent = Math.round((usage.query_count / usage.query_limit) * 100);
  const isWarning = percent >= 80 && remaining > 1;
  const isLastQuery = remaining === 1;
  const isExhausted = remaining === 0;
  const upgradeInfo = TIER_UPGRADE[usage.tier];

  const resetDate = usage.period_end
    ? new Date(usage.period_end).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      })
    : null;

  // Exhausted -- always visible, prominent
  if (isExhausted) {
    return (
      <div className="flex-none border-b border-parchment-200 bg-parchment-50/80 px-4 sm:px-6 py-2.5">
        <div className="max-w-chat mx-auto flex items-center justify-between gap-3">
          <p className="text-body-sm text-ink-600 font-body">
            <span className="font-medium text-ink-800">0 queries remaining</span>
            {resetDate && (
              <span className="text-ink-400"> -- resets {resetDate}</span>
            )}
          </p>
          {upgradeInfo ? (
            <Link
              href="/pricing"
              className="
                text-caption font-display font-medium px-3 py-1 rounded-full
                bg-ink-900 text-parchment-100
                hover:bg-ink-800 transition-colors whitespace-nowrap
              "
            >
              Upgrade to {upgradeInfo.next}
            </Link>
          ) : (
            resetDate && (
              <span className="text-caption text-ink-400 font-display whitespace-nowrap">
                Resets {resetDate}
              </span>
            )
          )}
        </div>
      </div>
    );
  }

  // Last query -- clear warning, dismissible
  if (isLastQuery && !dismissed) {
    return (
      <div className="flex-none border-b border-gold-200 bg-gold-50/60 px-4 sm:px-6 py-2">
        <div className="max-w-chat mx-auto flex items-center justify-between gap-3">
          <p className="text-body-sm text-ink-600 font-body">
            <span className="font-medium text-ink-800">
              This is your last query for the month.
            </span>
            {resetDate && (
              <span className="text-ink-400"> Resets {resetDate}.</span>
            )}
          </p>
          <button
            onClick={() => setDismissed(true)}
            className="text-ink-400 hover:text-ink-600 transition-colors flex-none"
            aria-label="Dismiss"
          >
            <svg className="w-3.5 h-3.5" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 3l8 8M11 3l-8 8" />
            </svg>
          </button>
        </div>
      </div>
    );
  }

  // 80% soft warning -- subtle, dismissible
  if (isWarning && !dismissed) {
    return (
      <div className="flex-none border-b border-parchment-200 bg-parchment-50/60 px-4 sm:px-6 py-1.5">
        <div className="max-w-chat mx-auto flex items-center justify-between gap-3">
          <p className="text-caption text-ink-500 font-body">
            {remaining} queries remaining this month
          </p>
          <button
            onClick={() => setDismissed(true)}
            className="text-ink-300 hover:text-ink-500 transition-colors flex-none"
            aria-label="Dismiss"
          >
            <svg className="w-3 h-3" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 3l8 8M11 3l-8 8" />
            </svg>
          </button>
        </div>
      </div>
    );
  }

  return null;
}

// Default export for backwards compat
export default QueryBadge;
