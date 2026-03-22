"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { endSession } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import ExportButton from "./ExportButton";

interface EndSessionDialogProps {
  sessionId: string;
  open: boolean;
  onClose: () => void;
  onSessionEnded: () => void;
}

type DialogState = "confirm" | "ending" | "error";

export default function EndSessionDialog({
  sessionId,
  open,
  onClose,
  onSessionEnded,
}: EndSessionDialogProps) {
  const { t } = useTranslation("end_session");
  const [state, setState] = useState<DialogState>("confirm");
  const [errorMessage, setErrorMessage] = useState("");

  const handleEndSession = useCallback(async () => {
    setState("ending");
    try {
      await endSession(sessionId).catch(() => {
        // Best-effort -- session may already be ended
      });
      onSessionEnded();
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "Failed to end session",
      );
      setState("error");
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
                  {t("title")}
                </h2>
                <p className="text-body-md text-ink-600 font-body mb-4">
                  {t("body")}
                </p>

                {/* Protocol export (DOCX/PDF) */}
                <ExportButton sessionId={sessionId} />

                <div className="border-t border-parchment-200 my-4" />

                <div className="flex flex-col gap-2.5">
                  <button
                    onClick={handleEndSession}
                    className="
                      w-full px-4 py-2.5 rounded-xl
                      bg-red-600 text-parchment-100
                      font-display text-body-sm font-medium
                      hover:bg-red-700
                      transition-colors duration-200
                      cursor-pointer
                    "
                  >
                    {t("confirm")}
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
                    {t("cancel")}
                  </button>
                </div>
              </>
            )}

            {state === "ending" && (
              <div className="flex flex-col items-center py-4">
                <div className="w-6 h-6 border-2 border-ink-300 border-t-ink-800 rounded-full animate-spin mb-4" />
                <p className="text-body-md text-ink-600 font-body">
                  {t("ending")}
                </p>
              </div>
            )}

            {state === "error" && (
              <>
                <h2 className="font-display text-display-sm font-semibold text-ink-900 mb-2">
                  {t("error")}
                </h2>
                <p className="text-body-md text-ink-600 font-body mb-4">
                  {errorMessage}
                </p>
                <div className="flex flex-col gap-2.5">
                  <button
                    onClick={handleEndSession}
                    className="
                      w-full px-4 py-2.5 rounded-xl
                      bg-ink-900 text-parchment-100
                      font-display text-body-sm font-medium
                      hover:bg-ink-800
                      transition-colors duration-200
                      cursor-pointer
                    "
                  >
                    {t("try_again")}
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
                    {t("cancel")}
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
