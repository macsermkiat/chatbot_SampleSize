"use client";

interface TypingIndicatorProps {
  label?: string;
}

export default function TypingIndicator({ label }: TypingIndicatorProps) {
  return (
    <div className="flex items-start gap-3">
      <div className="flex flex-col items-start gap-1.5">
        {label && (
          <div className="flex items-center gap-2 ml-0.5">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-gold-400 animate-pulse-warm" />
            <span className="text-caption font-display text-ink-400 font-medium">
              {label}
            </span>
          </div>
        )}
        <div className="px-5 py-3.5 rounded-2xl rounded-bl-md bg-parchment-50 border border-parchment-200 shadow-sm">
          <div className="flex items-center gap-1.5 h-5">
            <span
              className="block w-1.5 h-1.5 rounded-full bg-gold-500 animate-dot-bounce"
              style={{ animationDelay: "0s" }}
            />
            <span
              className="block w-1.5 h-1.5 rounded-full bg-gold-500 animate-dot-bounce"
              style={{ animationDelay: "0.16s" }}
            />
            <span
              className="block w-1.5 h-1.5 rounded-full bg-gold-500 animate-dot-bounce"
              style={{ animationDelay: "0.32s" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
