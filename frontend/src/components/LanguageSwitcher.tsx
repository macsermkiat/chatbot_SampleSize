"use client";

import { useLocale } from "@/lib/i18n";

interface LanguageSwitcherProps {
  className?: string;
}

export default function LanguageSwitcher({ className }: LanguageSwitcherProps) {
  const { locale, setLocale } = useLocale();

  return (
    <button
      onClick={() => setLocale(locale === "en" ? "th" : "en")}
      aria-label={
        locale === "en" ? "Switch to Thai" : "Switch to English"
      }
      className={`
        text-caption font-display px-2 py-0.5 rounded-full
        border border-parchment-300 hover:border-gold-400
        text-ink-600 hover:text-ink-800
        transition-all duration-200
        cursor-pointer
        ${className ?? ""}
      `}
    >
      {locale === "en" ? "TH" : "EN"}
    </button>
  );
}
