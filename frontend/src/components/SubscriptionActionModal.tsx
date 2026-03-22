"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { upgradeSubscription, cancelSubscription } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";

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

function formatDate(iso: string | null, fallback: string): string {
  if (!iso) return fallback;
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
  const { t } = useTranslation("subscription_modal");
  const [state, setState] = useState<ModalState>("confirm");
  const [errorMessage, setErrorMessage] = useState("");
  const [resultRenewsAt, setResultRenewsAt] = useState<string | null>(null);

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

  const endOfBilling = t("end_of_billing");
  const dateStr = formatDate(resultRenewsAt ?? renewsAt, endOfBilling);

  const tierDisplayName = t(`tier_${toTier}`) !== `subscription_modal.tier_${toTier}`
    ? t(`tier_${toTier}`)
    : capitalize(toTier);

  // Mode-specific content
  const title =
    mode === "cancel"
      ? t("cancel_title")
      : mode === "upgrade"
        ? `${t("upgrade_title")} ${tierDisplayName}`
        : `${t("downgrade_title")} ${tierDisplayName}`;

  const description =
    mode === "cancel"
      ? `${t("cancel_desc_prefix")} ${formatDate(renewsAt, endOfBilling)}. ${t("cancel_desc_suffix")}`
      : mode === "upgrade"
        ? t("upgrade_desc")
        : t("downgrade_desc");

  const confirmLabel =
    mode === "cancel"
      ? t("cancel_confirm")
      : mode === "upgrade"
        ? t("upgrade_confirm")
        : t("downgrade_confirm");

  const confirmStyle =
    mode === "cancel"
      ? "bg-red-600 text-parchment-100 hover:bg-red-700"
      : mode === "upgrade"
        ? "bg-ink-900 text-parchment-100 hover:bg-ink-800"
        : "bg-parchment-100 text-ink-800 hover:bg-parchment-200 border border-parchment-300";

  const submittingText =
    mode === "upgrade" ? t("upgrading") : t("cancelling");

  const doneMessage =
    mode === "upgrade"
      ? t("upgrade_done")
      : mode === "cancel"
        ? `${t("cancel_done")} ${dateStr}.`
        : "";

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
                  {title}
                </h2>
                <p className="text-body-md text-ink-600 font-body mb-6">
                  {description}
                </p>
                <div className="flex flex-col gap-2.5">
                  <button
                    onClick={handleConfirm}
                    className={`
                      w-full px-4 py-2.5 rounded-xl
                      font-display text-body-sm font-medium
                      transition-colors duration-200
                      cursor-pointer
                      ${confirmStyle}
                    `}
                  >
                    {confirmLabel}
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
                    {t("keep_current")}
                  </button>
                </div>
              </>
            )}

            {state === "submitting" && (
              <div className="flex flex-col items-center py-4">
                <div className="w-6 h-6 border-2 border-ink-300 border-t-ink-800 rounded-full animate-spin mb-4" />
                <p className="text-body-md text-ink-600 font-body">
                  {submittingText}
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
                    {t("done")}
                  </h2>
                </div>
                <p className="text-body-md text-ink-600 font-body mb-6">
                  {doneMessage}
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
                  {t("close")}
                </button>
              </>
            )}

            {state === "error" && (
              <>
                <h2 className="font-display text-display-sm font-semibold text-ink-900 mb-2">
                  {t("error_title")}
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
                    {t("cancel_btn")}
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
