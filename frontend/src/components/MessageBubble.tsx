"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "@/lib/api";

interface MessageBubbleProps {
  message: ChatMessage;
  isLatest?: boolean;
}

const NODE_LABELS: Record<string, string> = {
  orchestrator: "Research Orchestrator",
  gap_search: "Literature Search",
  gap_summarize: "Evidence Appraisal",
  gap_secretary: "Gap Analysis Summary",
  methodology: "Methodology Consultant",
  methodology_secretary: "Methodology Summary",
  biostatistics: "Biostatistics Advisor",
  coding: "Code Generation",
  biostats_secretary: "Biostatistics Summary",
  biostats_routing: "Phase Router",
};

export default function MessageBubble({ message, isLatest }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`
        flex w-full
        ${isUser ? "justify-end" : "justify-start"}
        ${isLatest ? "animate-fade-in-up" : ""}
      `}
    >
      <div
        className={`
          max-w-[85%] sm:max-w-[75%]
          ${isUser ? "ml-8" : "mr-8"}
        `}
      >
        {/* Agent label */}
        {!isUser && message.node && (
          <div className="flex items-center gap-2 mb-1.5 ml-0.5">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-gold-500" />
            <span className="text-caption font-display text-ink-500 font-medium">
              {NODE_LABELS[message.node] || message.node}
            </span>
          </div>
        )}

        {/* Message body */}
        <div
          className={`
            relative px-5 py-3.5 rounded-2xl
            ${
              isUser
                ? "bg-ink-900 text-parchment-100 rounded-br-md"
                : "bg-parchment-50 border border-parchment-200 text-ink-800 rounded-bl-md shadow-sm"
            }
          `}
        >
          {isUser ? (
            <p className="text-body-md leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
          ) : (
            <div className="prose-research text-body-md">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <div
          className={`
            mt-1 text-caption text-ink-400
            ${isUser ? "text-right mr-1" : "ml-1"}
          `}
        >
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
      </div>
    </div>
  );
}
