"use client";

import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "@/lib/api";

interface MessageBubbleProps {
  message: ChatMessage;
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

/**
 * Custom react-markdown components to fix rendering issues:
 * - Hide empty code blocks
 * - Style <hr> elegantly
 * - Prevent text overflow in <pre>
 */
const markdownComponents: Partial<Components> = {
  pre({ children, ...props }) {
    // Skip rendering if children are empty or whitespace-only
    const content = extractTextContent(children);
    if (!content.trim()) return null;
    return <pre {...props}>{children}</pre>;
  },
  code({ children, className, ...props }) {
    const content = String(children ?? "").replace(/\n$/, "");
    if (!content.trim()) return null;
    return (
      <code className={className} {...props}>
        {content}
      </code>
    );
  },
  hr() {
    return (
      <hr className="my-4 border-none h-px bg-gradient-to-r from-transparent via-parchment-400 to-transparent" />
    );
  },
};

/** Recursively extract text from React children. */
function extractTextContent(node: React.ReactNode): string {
  if (node == null) return "";
  if (typeof node === "string") return node;
  if (typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(extractTextContent).join("");
  if (typeof node === "object" && "props" in node) {
    const el = node as React.ReactElement<{ children?: React.ReactNode }>;
    return extractTextContent(el.props.children);
  }
  return "";
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex w-full justify-center">
        <div className="px-4 py-2 rounded-xl bg-parchment-100 border border-parchment-300 text-caption text-ink-500 font-display max-w-[85%]">
          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]} components={markdownComponents}>
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`
        flex w-full
        ${isUser ? "justify-end" : "justify-start"}
      `}
    >
      <div
        className={`
          max-w-[85%] sm:max-w-[75%] min-w-0
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
            relative px-5 py-3.5 rounded-2xl overflow-hidden
            ${
              isUser
                ? "bg-ink-900 text-parchment-100 rounded-br-md"
                : "bg-parchment-50 border border-parchment-200 text-ink-800 rounded-bl-md shadow-sm"
            }
          `}
        >
          {isUser ? (
            <p className="text-body-md leading-relaxed whitespace-pre-wrap break-words">
              {message.content}
            </p>
          ) : (
            <div className="prose-research text-body-md">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeSanitize]}
                components={markdownComponents}
              >
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
          {new Date(message.timestamp).toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </div>
      </div>
    </div>
  );
}
