"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { submitEvaluation } from "@/lib/api";

interface EvaluationDialogProps {
  sessionId: string;
  open: boolean;
  onComplete: () => void;
}

type DialogState = "rating" | "submitting" | "done";

export default function EvaluationDialog({
  sessionId,
  open,
  onComplete,
}: EvaluationDialogProps) {
  const [state, setState] = useState<DialogState>("rating");
  const [hoveredStar, setHoveredStar] = useState(0);
  const [selectedRating, setSelectedRating] = useState(0);
  const [comment, setComment] = useState("");

  useEffect(() => {
    if (open) {
      setState("rating");
      setHoveredStar(0);
      setSelectedRating(0);
      setComment("");
    }
  }, [open]);

  const handleSubmit = useCallback(async () => {
    if (selectedRating === 0) return;
    setState("submitting");
    try {
      await submitEvaluation(sessionId, selectedRating, comment.trim());
      setState("done");
      setTimeout(() => onComplete(), 1200);
    } catch {
      // Best-effort -- still end session
      setState("done");
      setTimeout(() => onComplete(), 1200);
    }
  }, [sessionId, selectedRating, comment, onComplete]);

  const handleSkip = useCallback(() => {
    onComplete();
  }, [onComplete]);

  if (!open) return null;

  const displayRating = hoveredStar || selectedRating;

  const ratingLabels = ["", "Poor", "Fair", "Good", "Very Good", "Excellent"];

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="eval-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/40 backdrop-blur-sm"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 8 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
            className="
              w-full max-w-md mx-4 p-6 rounded-2xl
              bg-parchment-50 border border-parchment-200
              shadow-xl
            "
          >
            {state === "done" ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center py-4"
              >
                <div className="text-3xl mb-3">&#10003;</div>
                <p className="text-body-md text-ink-700 font-display font-medium">
                  Thank you for your feedback!
                </p>
              </motion.div>
            ) : (
              <>
                <h2 className="font-display text-display-sm font-semibold text-ink-900 mb-1">
                  How was your experience?
                </h2>
                <p className="text-body-sm text-ink-500 font-body mb-5">
                  Your feedback helps us improve the research assistant.
                </p>

                {/* Star rating */}
                <div className="flex flex-col items-center mb-5">
                  <div className="flex gap-1.5 mb-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onMouseEnter={() => setHoveredStar(star)}
                        onMouseLeave={() => setHoveredStar(0)}
                        onClick={() => setSelectedRating(star)}
                        disabled={state === "submitting"}
                        className="
                          p-0.5 transition-transform duration-150
                          hover:scale-110 cursor-pointer
                          disabled:cursor-not-allowed
                        "
                        aria-label={`Rate ${star} star${star > 1 ? "s" : ""}`}
                      >
                        <svg
                          width="32"
                          height="32"
                          viewBox="0 0 24 24"
                          fill={star <= displayRating ? "#D97706" : "none"}
                          stroke={star <= displayRating ? "#D97706" : "#9CA3AF"}
                          strokeWidth="1.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                        </svg>
                      </button>
                    ))}
                  </div>
                  <p className="text-caption text-ink-500 font-body h-4">
                    {displayRating > 0 ? ratingLabels[displayRating] : ""}
                  </p>
                </div>

                {/* Comment box */}
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Any additional feedback? (optional)"
                  disabled={state === "submitting"}
                  maxLength={2000}
                  rows={3}
                  className="
                    w-full px-3 py-2.5 rounded-xl
                    border border-parchment-300
                    bg-white text-ink-800 text-body-sm font-body
                    placeholder:text-ink-400
                    focus:outline-none focus:ring-2 focus:ring-gold-400/50 focus:border-gold-400
                    resize-none
                    disabled:opacity-50
                    mb-5
                  "
                />

                <div className="flex flex-col gap-2.5">
                  <button
                    onClick={handleSubmit}
                    disabled={selectedRating === 0 || state === "submitting"}
                    className="
                      w-full px-4 py-2.5 rounded-xl
                      bg-ink-900 text-parchment-100
                      font-display text-body-sm font-medium
                      hover:bg-ink-800
                      transition-colors duration-200
                      cursor-pointer
                      disabled:opacity-40 disabled:cursor-not-allowed
                    "
                  >
                    {state === "submitting" ? "Submitting..." : "Submit Feedback"}
                  </button>
                  <button
                    onClick={handleSkip}
                    disabled={state === "submitting"}
                    className="
                      w-full px-4 py-2 rounded-xl
                      text-ink-400 font-display text-caption
                      hover:text-ink-600
                      transition-colors duration-200
                      cursor-pointer
                      disabled:cursor-not-allowed
                    "
                  >
                    Skip
                  </button>
                </div>
              </>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
