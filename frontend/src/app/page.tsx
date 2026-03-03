"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import CodeBlock from "@/components/CodeBlock";
import ExpertisePicker, {
  type ExpertiseLevel,
} from "@/components/ExpertisePicker";
import FileUpload from "@/components/FileUpload";
import FloatingParticles from "@/components/FloatingParticles";
import MessageBubble from "@/components/MessageBubble";
import PhaseIndicator from "@/components/PhaseIndicator";
import TypingIndicator from "@/components/TypingIndicator";
import {
  streamChat,
  uid,
  type ChatMessage,
  type FileUploadResult,
} from "@/lib/api";
import {
  presenceVariants,
  welcomeVariants,
  userMessageVariants,
  assistantMessageVariants,
  sendButtonVariants,
} from "@/lib/motion.config";

type Phase = "orchestrator" | "research_gap" | "methodology" | "biostatistics";

const WELCOME_HEADING = "Research Assistant";
const WELCOME_QUOTE =
  "\u201CThe goal of research is not to confirm what we already know, but to discover what we do not.\u201D";

const STARTER_PROMPTS = [
  "Find research gaps in AI-assisted colonoscopy screening",
  "Design a cohort study for statin use and dementia risk",
  "Calculate sample size for a two-arm RCT",
];

export default function Home() {
  const [sessionId] = useState(() => uid());
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [phase, setPhase] = useState<Phase>("orchestrator");
  const [streaming, setStreaming] = useState(false);
  const [codeBlocks, setCodeBlocks] = useState<
    { language: string; script: string }[]
  >([]);
  const [expertiseLevel, setExpertiseLevel] = useState<ExpertiseLevel | null>(
    null,
  );
  // Track whether the level has been sent to the backend at least once
  const expertiseSentRef = useRef(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

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
      if (!trimmed || streaming) return;

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

      // Reset textarea height
      if (inputRef.current) {
        inputRef.current.style.height = "auto";
      }

      // Send expertise_level on first message or when it changes
      const shouldSendLevel = !expertiseSentRef.current && expertiseLevel;
      if (shouldSendLevel) {
        expertiseSentRef.current = true;
      }

      try {
        for await (const { event, data } of streamChat(
          trimmed,
          sessionId,
          shouldSendLevel ? expertiseLevel : undefined,
        )) {
          switch (event) {
            case "message": {
              if (data.content) {
                const assistantMsg: ChatMessage = {
                  id: uid(),
                  role: "assistant",
                  content: data.content,
                  node: data.node,
                  phase: data.phase,
                  timestamp: Date.now(),
                };
                setMessages((prev) => [...prev, assistantMsg]);
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
            case "error": {
              const errMsg: ChatMessage = {
                id: uid(),
                role: "assistant",
                content: `Something went wrong: ${data.error || "Unknown error"}. Please try again.`,
                timestamp: Date.now(),
              };
              setMessages((prev) => [...prev, errMsg]);
              break;
            }
          }
        }
      } catch (err) {
        const errMsg: ChatMessage = {
          id: uid(),
          role: "assistant",
          content:
            "I couldn't reach the server. Please try again in a moment.",
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, errMsg]);
      } finally {
        setStreaming(false);
        inputRef.current?.focus();
      }
    },
    [sessionId, streaming, expertiseLevel],
  );

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
      const notice = `Uploaded **${result.filename}** (${result.char_count.toLocaleString()} characters extracted)`;
      sendMessage(notice);
    },
    [sendMessage],
  );

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="flex-none border-b border-parchment-200 bg-parchment-100/80 backdrop-blur-sm z-10">
        <div className="max-w-chat mx-auto px-6 py-4 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h1 className="font-display text-display-md font-semibold text-ink-900 tracking-tight">
              {WELCOME_HEADING}
            </h1>
            <div className="flex items-center gap-3">
              {expertiseLevel && (
                <button
                  onClick={() =>
                    setExpertiseLevel((prev) => {
                      const next = prev === "simple" ? "advanced" : "simple";
                      expertiseSentRef.current = false; // resend on next message
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
              <span className="block w-2 h-2 rounded-full bg-gold-500 animate-pulse-warm" />
              <span className="text-caption text-ink-500 font-display">
                Active
              </span>
            </div>
          </div>
          <PhaseIndicator currentPhase={phase} />
        </div>
      </header>

      {/* Messages area */}
      <main ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="max-w-chat mx-auto px-6">
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
                  Research Assistant
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
                {messages.map((msg, i) => (
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
                      <TypingIndicator label="Thinking..." />
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
      <footer className="flex-none border-t border-parchment-200 bg-parchment-100/80 backdrop-blur-sm">
        <form
          onSubmit={handleSubmit}
          className="max-w-chat mx-auto px-6 py-4"
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
              className="
                flex-1 bg-transparent resize-none
                text-body-md text-ink-800
                placeholder:text-ink-400
                focus:outline-none
                disabled:opacity-50
                font-body
                max-h-40
              "
            />

            <motion.button
              type="submit"
              disabled={!input.trim() || streaming}
              variants={sendButtonVariants}
              animate={
                streaming ? "sending" : input.trim() ? "ready" : "idle"
              }
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
              <AnimatePresence mode="wait" initial={false}>
                {streaming ? (
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
                ) : (
                  <motion.span
                    key="arrow"
                    initial={{ opacity: 0, x: -4 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 4 }}
                    transition={{ duration: 0.15 }}
                    className="flex items-center justify-center"
                  >
                    <svg
                      className="w-4 h-4"
                      viewBox="0 0 16 16"
                      fill="currentColor"
                    >
                      <path d="M1.724 1.053a.5.5 0 01.55-.042l12.5 7a.5.5 0 010 .878l-12.5 7A.5.5 0 011 15.5V.5a.5.5 0 01.724-.447zM2.5 2.31v4.94L7.1 8 2.5 8.75v4.94L13.85 8 2.5 2.31z" />
                    </svg>
                  </motion.span>
                )}
              </AnimatePresence>
            </motion.button>
          </div>

          <p className="text-center mt-2.5 text-caption text-ink-400 font-display">
            Research planning assistant -- not for clinical advice
          </p>
        </form>
      </footer>
    </div>
  );
}
