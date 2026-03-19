"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import CodeBlock from "@/components/CodeBlock";
import EndSessionDialog from "@/components/EndSessionDialog";
import EvaluationDialog from "@/components/EvaluationDialog";
import ExpertisePicker, {
  type ExpertiseLevel,
} from "@/components/ExpertisePicker";
import FileUpload from "@/components/FileUpload";
import FloatingParticles from "@/components/FloatingParticles";
import UserMenu from "@/components/UserMenu";
import { QueryBadge, QueryWarningBanner, dispatchUsageRefresh } from "@/components/QueryCounter";
import MessageBubble from "@/components/MessageBubble";
import PhaseIndicator from "@/components/PhaseIndicator";
import TypingIndicator from "@/components/TypingIndicator";
import {
  streamChat,
  uid,
  getSessionMessages,
  type ChatMessage,
  type FileUploadResult,
} from "@/lib/api";
import { useSearchParams } from "next/navigation";
import {
  presenceVariants,
  welcomeVariants,
  userMessageVariants,
  assistantMessageVariants,
  sendButtonVariants,
} from "@/lib/motion.config";

type Phase = "orchestrator" | "research_gap" | "methodology" | "biostatistics";

const WELCOME_HEADING = "ProtoCol";
const WELCOME_QUOTE =
  "\u201CThe goal of research is not to confirm what we already know, but to discover what we do not.\u201D";

const STARTER_PROMPTS = [
  "Find research gaps in AI-assisted colonoscopy screening",
  "Design a cohort study for statin use and dementia risk",
  "Calculate sample size for a two-arm RCT",
];

function isNetworkError(err: unknown): boolean {
  if (err instanceof TypeError && /fetch|network/i.test(err.message)) {
    return true;
  }
  if (err instanceof DOMException && err.name === "AbortError") {
    return false;
  }
  return false;
}

export default function HomeClient() {
  const searchParams = useSearchParams();
  const rawResumeId = searchParams.get("session");
  const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  const resumeSessionId = rawResumeId && UUID_RE.test(rawResumeId) ? rawResumeId : null;

  const [sessionId] = useState(() => {
    // Explicit resume from URL (?session=<id>) -- reuse that session
    if (resumeSessionId) return resumeSessionId;
    // Fresh page load -- always start a new session to avoid stale
    // LangGraph checkpoint state routing to the wrong phase.
    // Users can resume old sessions via "My Projects" -> Resume.
    return uid();
  });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [phase, setPhase] = useState<Phase>("orchestrator");
  const [streaming, setStreaming] = useState(false);
  const [statusLabel, setStatusLabel] = useState("Thinking...");
  const [codeBlocks, setCodeBlocks] = useState<
    { language: string; script: string }[]
  >([]);
  const [expertiseLevel, setExpertiseLevel] = useState<ExpertiseLevel | null>(
    null,
  );
  // Track whether the level has been sent to the backend at least once
  const expertiseSentRef = useRef(false);
  // Store uploaded file data until the user sends their next message
  const pendingFileRef = useRef<FileUploadResult | null>(null);
  // AbortController for cancelling in-flight streams
  const abortRef = useRef<AbortController | null>(null);
  // Ref-based guard against race conditions (state updates are async)
  const isStreamingRef = useRef(false);
  // Dedup guard: track the message ID currently being streamed
  const activeMessageIdRef = useRef<string | null>(null);

  const [endDialogOpen, setEndDialogOpen] = useState(false);
  const [evalDialogOpen, setEvalDialogOpen] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSessionEnded = useCallback(() => {
    setEndDialogOpen(false);
    // Show evaluation dialog after session ends
    setEvalDialogOpen(true);
  }, []);

  const handleEvaluationComplete = useCallback(() => {
    setEvalDialogOpen(false);
    // Reload to reset all state (fresh session ID generated on mount)
    window.location.reload();
  }, []);

  // Load existing messages when resuming a session
  useEffect(() => {
    if (!resumeSessionId) return;
    let cancelled = false;
    getSessionMessages(resumeSessionId)
      .then((msgs) => {
        if (cancelled) return;
        const loaded: ChatMessage[] = msgs.map((m) => ({
          id: uid(),
          role: m.role as "user" | "assistant" | "system",
          content: m.content,
          node: m.node ?? undefined,
          phase: m.phase ?? undefined,
          timestamp: new Date(m.created_at).getTime(),
        }));
        if (loaded.length > 0) {
          setMessages(loaded);
          // Restore the phase from the last message that has one
          const lastPhase = [...loaded].reverse().find((m) => m.phase)?.phase as Phase | undefined;
          if (lastPhase) {
            setPhase(lastPhase);
          }
        }
      })
      .catch(() => {
        // Silently fail -- user can still send new messages
      });
    return () => {
      cancelled = true;
    };
  }, [resumeSessionId]);

  // Warm up the backend on page load (fire-and-forget)
  useEffect(() => {
    fetch("/keep-alive").catch(() => {});
  }, []);

  // Cleanup AbortController on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  // Auto-scroll on new messages
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, [messages, streaming]);

  // Auto-resize textarea
  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setInput(e.target.value);
      const ta = e.target;
      ta.style.height = "auto";
      ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
    },
    [],
  );

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isStreamingRef.current) return;
      isStreamingRef.current = true;

      // Generate a unique ID for this send to prevent duplicate retries
      const messageId = uid();
      activeMessageIdRef.current = messageId;

      // Add user message
      const userMsg: ChatMessage = {
        id: uid(),
        role: "user",
        content: trimmed,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setStreaming(true);
      setStatusLabel("Thinking...");

      // Create AbortController for this stream
      const controller = new AbortController();
      abortRef.current = controller;

      // Reset textarea height
      if (inputRef.current) {
        inputRef.current.style.height = "auto";
      }

      // Send expertise_level on first message or when it changes
      const shouldSendLevel = !expertiseSentRef.current && expertiseLevel;
      if (shouldSendLevel) {
        expertiseSentRef.current = true;
      }

      // Attach pending uploaded file (if any) to this message
      const pendingFile = pendingFileRef.current;
      if (pendingFile) {
        pendingFileRef.current = null;
      }

      const MAX_STREAM_RETRIES = 1;
      let attempt = 0;
      let streamCompleted = false;

      while (attempt <= MAX_STREAM_RETRIES && !streamCompleted) {
        if (controller.signal.aborted) break;
        // Guard: if a newer sendMessage call has started, bail out
        if (activeMessageIdRef.current !== messageId) break;
        try {
          for await (const { event, data } of streamChat(
            trimmed,
            sessionId,
            shouldSendLevel ? expertiseLevel : undefined,
            pendingFile
              ? [{ filename: pendingFile.filename, mime_type: pendingFile.mime_type, extracted_text: pendingFile.extracted_text }]
              : undefined,
            controller.signal,
          )) {
            if (controller.signal.aborted) break;
            if (activeMessageIdRef.current !== messageId) break;
            switch (event) {
              case "message": {
                if (data.content) {
                  const assistantMsg: ChatMessage = {
                    id: uid(),
                    role: "assistant",
                    content: data.content,
                    node: data.node,
                    phase: data.phase,
                    confidence: data.confidence,
                    timestamp: Date.now(),
                  };
                  setMessages((prev) => [...prev, assistantMsg]);
                }
                break;
              }
              case "progress": {
                if (data.status) {
                  setStatusLabel(data.status);
                }
                break;
              }
              case "phase_change": {
                if (data.phase) {
                  setPhase(data.phase as Phase);
                }
                break;
              }
              case "code": {
                if (data.script && data.language) {
                  setCodeBlocks((prev) => [
                    ...prev,
                    { language: data.language!, script: data.script! },
                  ]);
                }
                break;
              }
              case "done": {
                streamCompleted = true;
                break;
              }
              case "error": {
                streamCompleted = true;
                const isLimitError = data.code === "LIMIT_REACHED" || data.code === "PROJECT_LIMIT_REACHED";
                const errMsg: ChatMessage = {
                  id: uid(),
                  role: "assistant",
                  content: isLimitError
                    ? data.error || "Limit reached."
                    : `Something went wrong: ${data.error || "Unknown error"}. Please try again.`,
                  timestamp: Date.now(),
                };
                setMessages((prev) => [...prev, errMsg]);
                break;
              }
            }
          }
          // If the stream ended without a "done" event, treat as incomplete
          if (!streamCompleted && !controller.signal.aborted && attempt < MAX_STREAM_RETRIES) {
            attempt++;
            setStatusLabel("Reconnecting...");
            await new Promise((r) => setTimeout(r, 2000));
            continue;
          }
          break;
        } catch (err) {
          if (controller.signal.aborted) break;
          attempt++;
          if (attempt <= MAX_STREAM_RETRIES) {
            setStatusLabel("Reconnecting...");
            await new Promise((r) => setTimeout(r, 2000));
            continue;
          }
          const errorContent = isNetworkError(err)
            ? "I couldn't reach the server. Please check your connection and try again."
            : `Something went wrong: ${err instanceof Error ? err.message : "Unknown error"}. Please try again.`;
          const errMsg: ChatMessage = {
            id: uid(),
            role: "assistant",
            content: errorContent,
            timestamp: Date.now(),
          };
          setMessages((prev) => [...prev, errMsg]);
        }
      }

      abortRef.current = null;
      activeMessageIdRef.current = null;
      isStreamingRef.current = false;
      setStreaming(false);
      inputRef.current?.focus();

      // Refresh query counter after each completed query
      dispatchUsageRefresh();
    },
    [sessionId, expertiseLevel],
  );

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    activeMessageIdRef.current = null;
    isStreamingRef.current = false;
    setStreaming(false);
  }, []);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      sendMessage(input);
    },
    [input, sendMessage],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage(input);
      }
    },
    [input, sendMessage],
  );

  const handleFileProcessed = useCallback(
    (result: FileUploadResult) => {
      pendingFileRef.current = result;

      let noticeText = `Uploaded **${result.filename}** (${result.char_count.toLocaleString()} characters extracted`;
      if (result.has_tables) {
        noticeText += ", includes tables";
      }
      noticeText += "). Type your question about this file.";

      if (result.warning) {
        noticeText += `\n\n**Note:** ${result.warning}`;
      }

      const notice: ChatMessage = {
        id: uid(),
        role: "system",
        content: noticeText,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, notice]);
      inputRef.current?.focus();
    },
    [],
  );

  const handleFileError = useCallback((message: string) => {
    const errMsg: ChatMessage = {
      id: uid(),
      role: "system",
      content: `Upload failed: ${message}`,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, errMsg]);
  }, []);

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-dvh">
      {/* Header */}
      <header className="flex-none border-b border-parchment-200 bg-parchment-100/80 backdrop-blur-sm z-10">
        <div className="max-w-chat mx-auto px-4 sm:px-6 py-3 sm:py-4 flex flex-col gap-3 sm:gap-4 short-landscape:py-1.5 short-landscape:gap-1">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h1 className="font-display text-display-md font-semibold text-ink-900 tracking-tight">
                {WELCOME_HEADING}
              </h1>
              <span className="block w-2 h-2 rounded-full bg-gold-500 animate-pulse-warm flex-none" />
            </div>
            <div className="flex items-center gap-2 sm:gap-3">
              <QueryBadge />
              <Link
                href="/benchmark"
                className="
                  hidden sm:inline-block
                  text-caption font-display px-2.5 py-1 rounded-full
                  border border-gold-300 bg-gold-50
                  text-gold-700 hover:bg-gold-100
                  transition-all duration-200
                "
              >
                vs GPT-5
              </Link>
              {expertiseLevel && (
                <button
                  onClick={() =>
                    setExpertiseLevel((prev) => {
                      const next = prev === "simple" ? "advanced" : "simple";
                      expertiseSentRef.current = false;
                      return next;
                    })
                  }
                  className="
                    text-caption font-display px-2.5 py-1 rounded-full
                    border border-parchment-300 hover:border-gold-400
                    text-ink-600 hover:text-ink-800
                    transition-all duration-200
                    cursor-pointer
                  "
                  title="Click to switch expertise level"
                >
                  {expertiseLevel === "simple" ? "Simple" : "Advanced"}
                </button>
              )}
              {!isEmpty && !streaming && (
                <button
                  onClick={() => setEndDialogOpen(true)}
                  aria-label="End session"
                  className="
                    text-caption font-display font-medium rounded-full
                    border border-red-200 bg-red-50
                    text-red-600 hover:text-white hover:bg-red-500 hover:border-red-500
                    transition-all duration-200
                    cursor-pointer
                    px-2 py-1 sm:px-3 sm:py-1.5
                  "
                >
                  <span className="hidden sm:inline">End Session</span>
                  <svg className="w-4 h-4 sm:hidden" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                    <path d="M4 4l8 8M12 4l-8 8" />
                  </svg>
                </button>
              )}
              <UserMenu />
            </div>
          </div>
          <div className="short-landscape:hidden">
            <PhaseIndicator currentPhase={phase} />
          </div>
        </div>
      </header>

      <QueryWarningBanner />

      {/* Messages area */}
      <main ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="max-w-chat mx-auto px-4 sm:px-6">
          <AnimatePresence mode="wait" initial={false}>
            {isEmpty ? (
              /* Empty state -- scholarly welcome with animations */
              <motion.div
                key="welcome"
                variants={presenceVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                className="flex flex-col items-center justify-center min-h-[60vh] py-16 relative"
              >
                <FloatingParticles count={14} />

                {/* Decorative mark */}
                <motion.div
                  className="relative mb-10"
                  variants={welcomeVariants.logo}
                >
                  <svg
                    className="w-16 h-16 text-ink-800"
                    viewBox="0 0 64 64"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1"
                  >
                    <line x1="32" y1="58" x2="32" y2="30" strokeWidth="2" />
                    <ellipse
                      cx="32"
                      cy="22"
                      rx="18"
                      ry="16"
                      strokeWidth="1.2"
                    />
                    <ellipse
                      cx="26"
                      cy="18"
                      rx="10"
                      ry="9"
                      strokeWidth="0.8"
                    />
                    <ellipse
                      cx="38"
                      cy="20"
                      rx="12"
                      ry="10"
                      strokeWidth="0.8"
                    />
                    <line x1="18" y1="58" x2="46" y2="58" strokeWidth="1.5" />
                  </svg>
                  {/* Warm glow */}
                  <div
                    className="
                      absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/3
                      w-20 h-20 rounded-full
                      bg-[radial-gradient(circle,oklch(0.88_0.14_85/0.35)_0%,transparent_70%)]
                      pointer-events-none
                    "
                  />
                </motion.div>

                <motion.div
                  className="divider w-full max-w-xs mb-8"
                  variants={welcomeVariants.divider}
                  style={{ originX: "50%" }}
                >
                  ProtoCol
                </motion.div>

                <motion.p
                  className="text-body-lg text-ink-600 text-center max-w-md leading-relaxed mb-2 font-body"
                  variants={welcomeVariants.text}
                >
                  I guide medical researchers through gap analysis, study
                  methodology design, and biostatistical analysis.
                </motion.p>

                <motion.p
                  className="text-body-sm text-ink-400 italic text-center max-w-sm mb-10 font-body"
                  variants={welcomeVariants.quote}
                >
                  {WELCOME_QUOTE}
                </motion.p>

                {/* Expertise picker or Starter prompts */}
                {!expertiseLevel ? (
                  <ExpertisePicker onSelect={setExpertiseLevel} />
                ) : (
                  <motion.div
                    className="flex flex-col gap-2.5 w-full max-w-md"
                    variants={welcomeVariants.promptContainer}
                    initial="initial"
                    animate="animate"
                  >
                    <span className="text-caption text-ink-400 font-display text-center tracking-wider uppercase mb-1">
                      Try asking
                    </span>
                    {STARTER_PROMPTS.map((prompt) => (
                      <motion.button
                        key={prompt}
                        variants={welcomeVariants.promptItem}
                        whileHover={{
                          scale: 1.015,
                          borderColor: "#e6ad36",
                          transition: { duration: 0.15 },
                        }}
                        whileTap={{ scale: 0.975 }}
                        onClick={() => sendMessage(prompt)}
                        className="
                          text-left px-4 py-3 rounded-xl
                          bg-parchment-50 border border-parchment-200
                          text-body-sm text-ink-700
                          hover:bg-gold-50
                          transition-colors duration-200
                        "
                      >
                        {prompt}
                      </motion.button>
                    ))}
                  </motion.div>
                )}
              </motion.div>
            ) : (
              /* Conversation */
              <motion.div
                key="conversation"
                variants={presenceVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                className="flex flex-col gap-5 py-6"
              >
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    variants={
                      msg.role === "user"
                        ? userMessageVariants
                        : assistantMessageVariants
                    }
                    initial="initial"
                    animate="animate"
                  >
                    <MessageBubble message={msg} />
                  </motion.div>
                ))}

                {/* Code blocks */}
                {codeBlocks.map((block, i) => (
                  <motion.div
                    key={`code-${i}`}
                    variants={assistantMessageVariants}
                    initial="initial"
                    animate="animate"
                  >
                    <CodeBlock
                      language={block.language}
                      script={block.script}
                    />
                  </motion.div>
                ))}

                {/* Typing indicator */}
                <AnimatePresence>
                  {streaming && (
                    <motion.div
                      key="typing"
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -4 }}
                      transition={{ duration: 0.2 }}
                    >
                      <TypingIndicator label={statusLabel} />
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Bottom spacer for scroll */}
                <div className="h-4" />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Input area */}
      <footer className="flex-none border-t border-parchment-200 bg-parchment-100/80 backdrop-blur-sm pb-[env(safe-area-inset-bottom)]">
        <form
          onSubmit={handleSubmit}
          className="max-w-chat mx-auto px-4 sm:px-6 py-3 sm:py-4 short-landscape:py-1.5"
        >
          <div
            className="
              flex items-end gap-3
              bg-parchment-50 border border-parchment-200
              rounded-2xl px-4 py-3
              focus-within:border-gold-400
              focus-within:shadow-[0_0_0_3px_oklch(0.85_0.12_85/0.15)]
              transition-all duration-200
            "
          >
            <FileUpload
              onFileProcessed={handleFileProcessed}
              onError={handleFileError}
              disabled={streaming}
            />

            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Describe your research question..."
              disabled={streaming}
              rows={1}
              maxLength={10000}
              aria-label="Research question input"
              className="
                flex-1 bg-transparent resize-none
                text-body-md text-ink-800
                placeholder:text-ink-400
                focus:outline-none
                disabled:opacity-50
                font-body
                max-h-40 short-landscape:max-h-20
              "
            />

            {streaming ? (
              <motion.button
                type="button"
                onClick={handleStop}
                variants={sendButtonVariants}
                animate="sending"
                whileTap={{ scale: 0.88 }}
                className="
                  flex items-center justify-center
                  w-9 h-9 rounded-xl
                  bg-ink-900 text-parchment-100
                  hover:bg-red-700
                  transition-colors duration-200
                  flex-none
                  cursor-pointer
                "
                aria-label="Stop generating"
              >
                <motion.span
                  key="stop"
                  initial={{ opacity: 0, rotate: -90 }}
                  animate={{ opacity: 1, rotate: 0 }}
                  exit={{ opacity: 0, rotate: 90 }}
                  transition={{ duration: 0.15 }}
                  className="flex items-center justify-center"
                >
                  <svg
                    className="w-3.5 h-3.5"
                    viewBox="0 0 14 14"
                    fill="currentColor"
                  >
                    <rect x="3" y="3" width="8" height="8" rx="1.5" />
                  </svg>
                </motion.span>
              </motion.button>
            ) : (
            <motion.button
              type="submit"
              disabled={!input.trim()}
              variants={sendButtonVariants}
              animate={input.trim() ? "ready" : "idle"}
              whileTap={{ scale: 0.88 }}
              className="
                flex items-center justify-center
                w-9 h-9 rounded-xl
                bg-ink-900 text-parchment-100
                hover:bg-ink-800
                disabled:bg-parchment-300 disabled:text-ink-400
                transition-colors duration-200
                flex-none
              "
              aria-label="Send message"
            >

              <svg
                className="w-4 h-4"
                viewBox="0 0 16 16"
                fill="currentColor"
              >
                <path d="M1.724 1.053a.5.5 0 01.55-.042l12.5 7a.5.5 0 010 .878l-12.5 7A.5.5 0 011 15.5V.5a.5.5 0 01.724-.447zM2.5 2.31v4.94L7.1 8 2.5 8.75v4.94L13.85 8 2.5 2.31z" />
              </svg>
            </motion.button>
            )}
          </div>

          <p className="text-center mt-2.5 text-caption text-ink-400 font-display short-landscape:hidden">
            Research planning assistant -- not for clinical advice
          </p>
        </form>
      </footer>

      <EndSessionDialog
        sessionId={sessionId}
        open={endDialogOpen}
        onClose={() => setEndDialogOpen(false)}
        onSessionEnded={handleSessionEnded}
      />
      <EvaluationDialog
        sessionId={sessionId}
        open={evalDialogOpen}
        onComplete={handleEvaluationComplete}
      />
    </div>
  );
}
