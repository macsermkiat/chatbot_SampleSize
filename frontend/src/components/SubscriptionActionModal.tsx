"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { upgradeSubscription, cancelSubscription } from "@/lib/api";

type SubscriptionAction = "upgrade" | "downgrade" | "cancel";
type ModalState = "confirm" | "submitting" | "done" | "error";

interface SubscriptionActionModalProps {
  open: boolean;
  mode: SubscriptionAction;
  fromTier: string;
  toTier: string;
  targetVariantId: string;
  renewsAt: string | null;
  customerPortalUrl: string;
  onClose: () => void;
  onComplete: (action: SubscriptionAction) => void;
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function formatDate(iso: string | null): string {
  if (!iso) return "end of billing period";
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

const MODAL_CONFIG: Record<
  SubscriptionAction,
  {
    title: (toTier: string) => string;
    description: (fromTier: string, toTier: string, renewsAt: string | null) => string;
    confirmLabel: string;
    confirmStyle: string;
    doneMessage: (toTier: string, renewsAt: string | null) => string;
  }
> = {
  upgrade: {
    title: (toTier) => `Upgrade to ${capitalize(toTier)}`,
    description: () =>
      "Your plan will change immediately. You'll be charged the prorated difference for the remaining days in your current billing period.",
    confirmLabel: "Confirm Upgrade",
    confirmStyle:
      "bg-ink-900 text-parchment-100 hover:bg-ink-800",
    doneMessage: (toTier) =>
      `Successfully upgraded to ${capitalize(toTier)}! Your new plan is active now.`,
  },
  downgrade: {
    title: (toTier) => `Downgrade to ${capitalize(toTier)}`,
    description: () =>
      "You'll be redirected to the customer portal to complete the downgrade. The change takes effect at your next billing date.",
    confirmLabel: "Go to Customer Portal",
    confirmStyle:
      "bg-parchment-100 text-ink-800 hover:bg-parchment-200 border border-parchment-300",
    doneMessage: () => "",
  },
  cancel: {
    title: () => "Cancel Subscription",
    description: (fromTier, _toTier, renewsAt) =>
      `Your ${capitalize(fromTier)} plan will remain active until ${formatDate(renewsAt)}. After that, you'll revert to the Free plan.`,
    confirmLabel: "Cancel Subscription",
    confirmStyle:
      "bg-red-600 text-parchment-100 hover:bg-red-700",
    doneMessage: (_toTier, renewsAt) =>
      `Subscription cancelled. You'll keep your current plan until ${formatDate(renewsAt)}.`,
  },
};

export default function SubscriptionActionModal({
  open,
  mode,
  fromTier,
  toTier,
  targetVariantId,
  renewsAt,
  customerPortalUrl,
  onClose,
  onComplete,
}: SubscriptionActionModalProps) {
  const [state, setState] = useState<ModalState>("confirm");
  const [errorMessage, setErrorMessage] = useState("");
  const [resultRenewsAt, setResultRenewsAt] = useState<string | null>(null);

  const config = MODAL_CONFIG[mode];

  const handleClose = useCallback(() => {
    setState("confirm");
    setErrorMessage("");
    onClose();
  }, [onClose]);

  const handleConfirm = useCallback(async () => {
    if (state === "submitting") return;

    if (mode === "downgrade") {
      if (customerPortalUrl) {
        window.open(customerPortalUrl, "_blank");
      }
      handleClose();
      return;
    }

    setState("submitting");
    try {
      if (mode === "upgrade") {
        await upgradeSubscription(targetVariantId);
      } else {
        const result = await cancelSubscription();
        setResultRenewsAt(result.ends_at);
      }
      setState("done");
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "Operation failed",
      );
      setState("error");
    }
  }, [mode, state, targetVariantId, customerPortalUrl, handleClose]);

  const handleDone = useCallback(() => {
    setState("confirm");
    setErrorMessage("");
    onComplete(mode);
  }, [mode, onComplete]);

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
                  {config.title(toTier)}
                </h2>
                <p className="text-body-md text-ink-600 font-body mb-6">
                  {config.description(fromTier, toTier, renewsAt)}
                </p>
                <div className="flex flex-col gap-2.5">
                  <button
                    onClick={handleConfirm}
                    className={`
                      w-full px-4 py-2.5 rounded-xl
                      font-display text-body-sm font-medium
                      transition-colors duration-200
                      cursor-pointer
                      ${config.confirmStyle}
                    `}
                  >
                    {config.confirmLabel}
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
                    Keep Current Plan
                  </button>
                </div>
              </>
            )}

            {state === "submitting" && (
              <div className="flex flex-col items-center py-4">
                <div className="w-6 h-6 border-2 border-ink-300 border-t-ink-800 rounded-full animate-spin mb-4" />
                <p className="text-body-md text-ink-600 font-body">
                  {mode === "upgrade"
                    ? "Upgrading your plan..."
                    : "Cancelling subscription..."}
                </p>
              </div>
            )}

            {state === "done" && (
              <>
                <div className="flex items-center gap-2 mb-2">
                  <svg
                    className="w-5 h-5 text-green-700"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <h2 className="font-display text-display-sm font-semibold text-ink-900">
                    Done
                  </h2>
                </div>
                <p className="text-body-md text-ink-600 font-body mb-6">
                  {config.doneMessage(toTier, resultRenewsAt ?? renewsAt)}
                </p>
                <button
                  onClick={handleDone}
                  className="
                    w-full px-4 py-2.5 rounded-xl
                    bg-ink-900 text-parchment-100
                    font-display text-body-sm font-medium
                    hover:bg-ink-800
                    transition-colors duration-200
                    cursor-pointer
                  "
                >
                  Close
                </button>
              </>
            )}

            {state === "error" && (
              <>
                <h2 className="font-display text-display-sm font-semibold text-ink-900 mb-2">
                  Something went wrong
                </h2>
                <p className="text-body-md text-ink-600 font-body mb-4">
                  {errorMessage}
                </p>
                <div className="flex flex-col gap-2.5">
                  <button
                    onClick={handleConfirm}
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
