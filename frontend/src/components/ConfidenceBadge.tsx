"use client";

import { useTranslation } from "@/lib/i18n";

type ConfidenceLevel = "high" | "medium" | "low";

interface ConfidenceBadgeProps {
  level: ConfidenceLevel;
}

const BADGE_STYLES: Record<ConfidenceLevel, string> = {
  high: "bg-green-50 text-green-700 border-green-200",
  medium: "bg-yellow-50 text-yellow-700 border-yellow-200",
  low: "bg-red-50 text-red-700 border-red-200",
};

export default function ConfidenceBadge({ level }: ConfidenceBadgeProps) {
  const { t } = useTranslation("confidence");
  const className = BADGE_STYLES[level];
  if (!className) return null;

  return (
    <span
      className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full border ${className}`}
      title={t(`${level}_title`)}
    >
      <svg
        className="w-3 h-3"
        viewBox="0 0 12 12"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
      >
        <circle cx="6" cy="6" r="5" />
        <path d="M6 3.5v3" strokeLinecap="round" />
        <circle cx="6" cy="8.5" r="0.5" fill="currentColor" stroke="none" />
      </svg>
      {t(level)}
    </span>
  );
}
