"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { Locale, TranslationDict } from "./types";
import en from "../../../messages/en.json";
import th from "../../../messages/th.json";

const STORAGE_KEY = "locale";
const DEFAULT_LOCALE: Locale = "en";

const MESSAGES: Record<Locale, TranslationDict> = {
  en: en as unknown as TranslationDict,
  th: th as unknown as TranslationDict,
};

interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (namespace: string, key: string) => string;
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

function readStoredLocale(): Locale {
  if (typeof window === "undefined") return DEFAULT_LOCALE;
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "en" || stored === "th") return stored;
  } catch {
    // Private browsing may block localStorage
  }
  return DEFAULT_LOCALE;
}

function persistLocale(locale: Locale) {
  try {
    localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    // Private browsing fallback
  }
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(DEFAULT_LOCALE);

  // Read from localStorage after hydration (avoids SSR mismatch)
  useEffect(() => {
    const stored = readStoredLocale();
    if (stored !== DEFAULT_LOCALE) {
      setLocaleState(stored);
    }
  }, []);

  // Keep <html lang> in sync
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  function setLocale(next: Locale) {
    setLocaleState(next);
    persistLocale(next);
  }

  function t(namespace: string, key: string): string {
    return (
      MESSAGES[locale]?.[namespace]?.[key] ??
      MESSAGES[DEFAULT_LOCALE]?.[namespace]?.[key] ??
      `${namespace}.${key}`
    );
  }

  return (
    <LocaleContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale(): LocaleContextValue {
  const ctx = useContext(LocaleContext);
  if (!ctx) throw new Error("useLocale must be used inside LocaleProvider");
  return ctx;
}
