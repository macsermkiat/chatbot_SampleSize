"use client";

import Image from "next/image";
import Link from "next/link";
import { useTranslation } from "@/lib/i18n";

interface FooterProps {
  variant?: "full" | "minimal";
}

export default function Footer({ variant = "full" }: FooterProps) {
  const { t } = useTranslation("footer");

  if (variant === "minimal") {
    return (
      <footer className="border-t border-parchment-200 bg-parchment-100/80">
        <div className="max-w-5xl mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-2">
            <Image
              src="/logo_protocol.png"
              alt="ProtoCol"
              width={20}
              height={20}
              className="h-5 w-auto"
            />
            <span className="font-display text-caption font-semibold text-ink-600">
              ProtoCol
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <Link
              href="/privacy"
              className="text-caption text-ink-400 hover:text-ink-600 transition-colors font-body"
            >
              {t("privacy")}
            </Link>
            <Link
              href="/terms"
              className="text-caption text-ink-400 hover:text-ink-600 transition-colors font-body"
            >
              {t("terms")}
            </Link>
          </div>
        </div>
      </footer>
    );
  }

  return (
    <footer className="border-t border-parchment-200 py-8 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <Link href="/" className="flex items-center gap-2.5">
            <Image
              src="/logo_protocol.png"
              alt="ProtoCol"
              width={24}
              height={24}
              className="h-6 w-auto"
            />
            <div>
              <p className="font-display text-body-sm font-semibold text-ink-800 leading-tight">
                ProtoCol
              </p>
              <p className="text-caption text-ink-400 font-body">
                {t("tagline")}
              </p>
            </div>
          </Link>

          <div className="flex items-center gap-4 sm:gap-5">
            <Link
              href="/privacy"
              className="text-caption text-ink-400 hover:text-ink-600 transition-colors font-body"
            >
              {t("privacy")}
            </Link>
            <Link
              href="/terms"
              className="text-caption text-ink-400 hover:text-ink-600 transition-colors font-body"
            >
              {t("terms")}
            </Link>
            <Link
              href="/refund"
              className="text-caption text-ink-400 hover:text-ink-600 transition-colors font-body"
            >
              {t("refund")}
            </Link>
            <span className="text-parchment-300">|</span>
            <a
              href="mailto:contact@protocol.med"
              className="text-caption text-ink-500 hover:text-ink-700 transition-colors font-body"
            >
              contact@protocol.med
            </a>
          </div>
        </div>

        <p className="mt-5 pt-4 border-t border-parchment-200 text-caption text-ink-400 font-body">
          {t("disclaimer")}
        </p>
      </div>
    </footer>
  );
}
