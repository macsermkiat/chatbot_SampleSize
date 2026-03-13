"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("App error boundary caught:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-parchment-100 flex items-center justify-center px-6">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <svg
            className="w-16 h-16 text-ink-400 mx-auto mb-6"
            viewBox="0 0 64 64"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <circle cx="32" cy="32" r="28" />
            <line x1="32" y1="20" x2="32" y2="36" strokeWidth="2.5" strokeLinecap="round" />
            <circle cx="32" cy="44" r="2" fill="currentColor" stroke="none" />
          </svg>
          <h1 className="font-display text-display-lg font-bold text-ink-900 mb-3">
            Something went wrong
          </h1>
          <p className="text-body-md text-ink-600 font-body leading-relaxed">
            An unexpected error occurred. Please try again, or refresh the page
            if the problem persists.
          </p>
        </div>
        <button
          onClick={reset}
          className="
            inline-flex items-center gap-2 px-6 py-3 rounded-xl
            bg-ink-900 text-parchment-100 font-display font-semibold text-body-md
            hover:bg-ink-800 transition-colors duration-200
            cursor-pointer
          "
        >
          Try again
        </button>
      </div>
    </div>
  );
}
