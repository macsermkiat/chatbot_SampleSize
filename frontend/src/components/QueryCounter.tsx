"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { getUsage } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";

interface UsageData {
  tier: string;
  query_count: number;
  query_limit: number | null;
  is_allowed: boolean;
  period_end?: string;
}

const TIER_BADGE_STYLES: Record<string, string> = {
  researcher: "bg-gold-100 text-gold-700 border-gold-300",
  pro: "bg-ink-900 text-parchment-100 border-ink-800",
  institutional: "bg-ink-900 text-parchment-100 border-ink-800",
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
 * Subtle inline counter for the header: tier badge + "12 remaining"
 * Shows tier badge for paid plans. Shows remaining count for capped plans.
 */
export function QueryBadge() {
  const { t } = useTranslation("query");
  const { usage } = useQueryUsage();

  if (!usage) return null;

  const badgeStyle = TIER_BADGE_STYLES[usage.tier];
  const remaining =
    usage.query_limit !== null
      ? Math.max(0, usage.query_limit - usage.query_count)
      : null;

  // Capitalize tier name for display
  const tierLabel = usage.tier.charAt(0).toUpperCase() + usage.tier.slice(1);

  return (
    <span className="flex items-center gap-1.5">
      {badgeStyle && (
        <span
          className={`text-caption font-display px-2 py-0.5 rounded-full border ${badgeStyle}`}
        >
          {tierLabel}
        </span>
      )}
      {remaining !== null && (
        <span
          className="text-caption text-ink-400 font-display tabular-nums"
          title={t("remaining_title")
            .replace("{remaining}", String(remaining))
            .replace("{limit}", String(usage.query_limit))}
        >
          {remaining} {t("remaining")}
        </span>
      )}
    </span>
  );
}

/**
 * Warning banner shown between header and content.
 * Appears at 80% usage, last query, and exhaustion.
 * Dismissible for soft/last-query warnings; always visible when exhausted.
 */
export function QueryWarningBanner() {
  const { t } = useTranslation("query");
  const { usage } = useQueryUsage();
  const [dismissed, setDismissed] = useState(false);

  if (!usage || usage.query_limit === null) return null;

  const remaining = Math.max(0, usage.query_limit - usage.query_count);
  const percent = Math.round((usage.query_count / usage.query_limit) * 100);
  const isWarning = percent >= 80 && remaining > 1;
  const isLastQuery = remaining === 1;
  const isExhausted = remaining === 0;

  // Determine next upgrade tier
  const upgradeNext =
    usage.tier === "free"
      ? "Researcher"
      : usage.tier === "researcher"
        ? "Pro"
        : null;

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
            <span className="font-medium text-ink-800">{t("exhausted")}</span>
            {resetDate && (
              <span className="text-ink-400"> -- {t("resets")} {resetDate}</span>
            )}
          </p>
          {upgradeNext ? (
            <Link
              href="/pricing"
              className="
                text-caption font-display font-medium px-3 py-1 rounded-full
                bg-ink-900 text-parchment-100
                hover:bg-ink-800 transition-colors whitespace-nowrap
              "
            >
              {t("upgrade_to")} {upgradeNext}
            </Link>
          ) : (
            resetDate && (
              <span className="text-caption text-ink-400 font-display whitespace-nowrap">
                {t("resets")} {resetDate}
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
              {t("last_query")}
            </span>
            {resetDate && (
              <span className="text-ink-400"> {t("resets")} {resetDate}.</span>
            )}
          </p>
          <button
            onClick={() => setDismissed(true)}
            className="text-ink-400 hover:text-ink-600 transition-colors flex-none"
            aria-label={t("dismiss")}
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
            {remaining} {t("queries_remaining")}
          </p>
          <button
            onClick={() => setDismissed(true)}
            className="text-ink-300 hover:text-ink-500 transition-colors flex-none"
            aria-label={t("dismiss")}
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
