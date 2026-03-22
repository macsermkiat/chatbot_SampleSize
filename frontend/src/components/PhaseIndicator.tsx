"use client";

import { useTranslation } from "@/lib/i18n";

type Phase = "orchestrator" | "research_gap" | "methodology" | "biostatistics";

interface PhaseIndicatorProps {
  currentPhase: Phase;
}

export default function PhaseIndicator({ currentPhase }: PhaseIndicatorProps) {
  const { t } = useTranslation("phase_indicator");

  const PHASES: { key: Phase; label: string; numeral: string }[] = [
    { key: "orchestrator", label: t("triage"), numeral: "I" },
    { key: "research_gap", label: t("gap_analysis"), numeral: "II" },
    { key: "methodology", label: t("methodology"), numeral: "III" },
    { key: "biostatistics", label: t("biostatistics"), numeral: "IV" },
  ];
  const activeIndex = PHASES.findIndex((p) => p.key === currentPhase);
  const activePhase = PHASES[activeIndex];

  return (
    <nav
      aria-label={t("aria_label")}
      className="flex flex-col items-center gap-2"
    >
      {/* Compact mobile label -- visible only below sm */}
      <p className="sm:hidden text-caption font-display text-ink-600">
        <span className="font-semibold text-ink-900">{activePhase?.numeral}</span>
        <span className="mx-1.5 text-parchment-400">/</span>
        <span className="text-ink-400">IV</span>
        <span className="mx-2 text-parchment-300">--</span>
        <span className="font-medium">{activePhase?.label}</span>
      </p>

      {/* Full stepper -- hidden on mobile */}
      <div className="hidden sm:flex items-center justify-center gap-0 select-none">
        {PHASES.map((phase, i) => {
          const isActive = i === activeIndex;
          const isPast = i < activeIndex;

          return (
            <div key={phase.key} className="flex items-center">
              {/* Connecting line */}
              {i > 0 && (
                <div
                  className={`
                    w-10 md:w-12 h-px transition-colors duration-500
                    ${isPast ? "bg-gold-500" : "bg-parchment-300"}
                  `}
                />
              )}

              {/* Phase node */}
              <div className="flex flex-col items-center gap-1.5">
                <div
                  className={`
                    relative flex items-center justify-center
                    w-8 h-8 rounded-full
                    font-display text-caption font-semibold
                    transition-all duration-500
                    ${
                      isActive
                        ? "bg-gold-500 text-parchment-50 shadow-[0_0_16px_oklch(0.75_0.12_85/0.35)]"
                        : isPast
                          ? "bg-gold-200 text-gold-800"
                          : "bg-parchment-200 text-ink-400"
                    }
                  `}
                >
                  {phase.numeral}
                  {isActive && (
                    <span className="absolute inset-0 rounded-full bg-gold-400 animate-pulse-warm" />
                  )}
                </div>
                <span
                  className={`
                    text-caption font-display whitespace-nowrap
                    transition-colors duration-500
                    ${isActive ? "text-ink-900 font-semibold" : isPast ? "text-ink-600" : "text-ink-400"}
                  `}
                >
                  {phase.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </nav>
  );
}
