"use client";

import { useCallback, useState } from "react";

interface CodeBlockProps {
  language: string;
  script: string;
}

export default function CodeBlock({ language, script }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(script);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API may be unavailable over HTTP or when unfocused
    }
  }, [script]);

  const langLabel = language.toUpperCase();

  return (
    <div className="rounded-lg overflow-hidden border border-parchment-200 shadow-sm">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-ink-800">
        <span className="text-caption font-mono text-parchment-400 tracking-wider">
          {langLabel}
        </span>
        <button
          onClick={handleCopy}
          className="
            text-caption font-mono text-parchment-400
            hover:text-parchment-200 transition-colors
            flex items-center gap-1.5
          "
        >
          {copied ? (
            <>
              <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
                <path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z" />
              </svg>
              Copied
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
                <path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 010 1.5h-1.5a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-1.5a.75.75 0 011.5 0v1.5A1.75 1.75 0 019.25 16h-7.5A1.75 1.75 0 010 14.25v-7.5z" />
                <path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0114.25 11h-7.5A1.75 1.75 0 015 9.25v-7.5zm1.75-.25a.25.25 0 00-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 00.25-.25v-7.5a.25.25 0 00-.25-.25h-7.5z" />
              </svg>
              Copy
            </>
          )}
        </button>
      </div>

      {/* Code body */}
      <pre className="px-4 py-4 bg-ink-900 text-parchment-200 text-body-sm font-mono overflow-x-auto leading-relaxed">
        <code>{script}</code>
      </pre>
    </div>
  );
}
