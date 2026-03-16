"use client";

type ConfidenceLevel = "high" | "medium" | "low";

interface ConfidenceBadgeProps {
  level: ConfidenceLevel;
}

const BADGE_CONFIG: Record<
  ConfidenceLevel,
  { label: string; className: string; title: string }
> = {
  high: {
    label: "High Confidence",
    className:
      "bg-green-50 text-green-700 border-green-200",
    title:
      "Standard scenario with well-established methods. Cross-check with validated software before protocol submission.",
  },
  medium: {
    label: "Medium Confidence",
    className:
      "bg-yellow-50 text-yellow-700 border-yellow-200",
    title:
      "Moderately complex scenario or some assumptions need verification. Review with a biostatistician.",
  },
  low: {
    label: "Low Confidence",
    className:
      "bg-red-50 text-red-700 border-red-200",
    title:
      "Novel or unusual design with limited validation data. Strongly recommend verification with a qualified biostatistician.",
  },
};

export default function ConfidenceBadge({ level }: ConfidenceBadgeProps) {
  const config = BADGE_CONFIG[level];
  if (!config) return null;

  return (
    <span
      className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full border ${config.className}`}
      title={config.title}
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
      {config.label}
    </span>
  );
}
