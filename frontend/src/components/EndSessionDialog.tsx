"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { downloadSummary, endSession } from "@/lib/api";

interface EndSessionDialogProps {
  sessionId: string;
  open: boolean;
  onClose: () => void;
  onSessionEnded: () => void;
}

type DialogState = "confirm" | "generating" | "error";

export default function EndSessionDialog({
  sessionId,
  open,
  onClose,
  onSessionEnded,
}: EndSessionDialogProps) {
  const [state, setState] = useState<DialogState>("confirm");
  const [errorMessage, setErrorMessage] = useState("");

  const handleDownloadAndEnd = useCallback(async () => {
    setState("generating");
    try {
      await downloadSummary(sessionId);
      await endSession(sessionId).catch(() => {
        // Session end is best-effort -- summary already downloaded
      });
      onSessionEnded();
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "Failed to generate summary",
      );
      setState("error");
    }
  }, [sessionId, onSessionEnded]);

  const handleEndWithoutSummary = useCallback(async () => {
    setState("generating");
    try {
      await endSession(sessionId).catch(() => {
        // Best-effort
      });
      onSessionEnded();
    } catch {
      onSessionEnded();
    }
  }, [sessionId, onSessionEnded]);

  const handleClose = useCallback(() => {
    setState("confirm");
    setErrorMessage("");
    onClose();
  }, [onClose]);

  // Dismiss on Escape key
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && state === "confirm") handleClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, state, handleClose]);

  if (!open) return null;

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/40 backdrop-blur-sm"
          onClick={state === "confirm" ? handleClose : undefined}
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
            {state === "confirm" && (
              <>
                <h2 className="font-display text-display-sm font-semibold text-ink-900 mb-2">
                  End Conversation
                </h2>
                <p className="text-body-md text-ink-600 font-body mb-6">
                  Would you like to download a summary of this consultation?
                  The summary can be shared with a biostatistician or
                  epidemiologist for review before your consultation.
                </p>
                <div className="flex flex-col gap-2.5">
                  <button
                    onClick={handleDownloadAndEnd}
                    className="
                      w-full px-4 py-2.5 rounded-xl
                      bg-ink-900 text-parchment-100
                      font-display text-body-sm font-medium
                      hover:bg-ink-800
                      transition-colors duration-200
                      cursor-pointer
                    "
                  >
                    Download Summary & End
                  </button>
                  <button
                    onClick={handleEndWithoutSummary}
                    className="
                      w-full px-4 py-2.5 rounded-xl
                      border border-parchment-300
                      text-ink-600 font-display text-body-sm
                      hover:bg-parchment-100 hover:border-parchment-400
                      transition-colors duration-200
                      cursor-pointer
                    "
                  >
                    End Without Summary
                  </button>
                  <button
                    onClick={handleClose}
                    className="
                      w-full px-4 py-2 rounded-xl
                      text-ink-400 font-display text-caption
                      hover:text-ink-600
                      transition-colors duration-200
                      cursor-pointer
                    "
                  >
                    Cancel
                  </button>
                </div>
              </>
            )}

            {state === "generating" && (
              <div className="flex flex-col items-center py-4">
                <div className="w-6 h-6 border-2 border-ink-300 border-t-ink-800 rounded-full animate-spin mb-4" />
                <p className="text-body-md text-ink-600 font-body">
                  Generating summary...
                </p>
              </div>
            )}

            {state === "error" && (
              <>
                <h2 className="font-display text-display-sm font-semibold text-ink-900 mb-2">
                  Summary Failed
                </h2>
                <p className="text-body-md text-ink-600 font-body mb-4">
                  {errorMessage}
                </p>
                <div className="flex flex-col gap-2.5">
                  <button
                    onClick={handleDownloadAndEnd}
                    className="
                      w-full px-4 py-2.5 rounded-xl
                      bg-ink-900 text-parchment-100
                      font-display text-body-sm font-medium
                      hover:bg-ink-800
                      transition-colors duration-200
                      cursor-pointer
                    "
                  >
                    Try Again
                  </button>
                  <button
                    onClick={handleEndWithoutSummary}
                    className="
                      w-full px-4 py-2.5 rounded-xl
                      border border-parchment-300
                      text-ink-600 font-display text-body-sm
                      hover:bg-parchment-100
                      transition-colors duration-200
                      cursor-pointer
                    "
                  >
                    End Without Summary
                  </button>
                  <button
                    onClick={handleClose}
                    className="
                      w-full px-4 py-2 rounded-xl
                      text-ink-400 font-display text-caption
                      hover:text-ink-600
                      transition-colors duration-200
                      cursor-pointer
                    "
                  >
                    Cancel
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
