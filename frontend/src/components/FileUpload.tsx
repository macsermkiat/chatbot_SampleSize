"use client";

import { useCallback, useRef, useState } from "react";
import { uploadFile, type FileUploadResult } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";

interface FileUploadProps {
  onFileProcessed: (result: FileUploadResult) => void;
  onError?: (message: string) => void;
  disabled?: boolean;
}

const ACCEPTED = ".pdf,.docx,.txt,.png,.jpg,.jpeg,.gif,.webp";
const MAX_FILE_SIZE_MB = 20;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

export default function FileUpload({
  onFileProcessed,
  onError,
  disabled,
}: FileUploadProps) {
  const { t } = useTranslation("file_upload");
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const processFile = useCallback(
    async (file: File) => {
      if (file.size > MAX_FILE_SIZE_BYTES) {
        onError?.(t("size_error").replace("{size}", String(MAX_FILE_SIZE_MB)));
        return;
      }

      const controller = new AbortController();
      abortRef.current = controller;
      setUploading(true);
      try {
        const result = await uploadFile(file, controller.signal);
        if (!controller.signal.aborted) {
          onFileProcessed(result);
        }
      } catch (err) {
        if (controller.signal.aborted) return;
        const message =
          err instanceof Error ? err.message : "Upload failed. Please try again.";
        onError?.(message);
      } finally {
        abortRef.current = null;
        setUploading(false);
      }
    },
    [onFileProcessed, onError, t],
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) processFile(file);
      e.target.value = "";
    },
    [processFile],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) processFile(file);
    },
    [processFile],
  );

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        onChange={handleChange}
        className="sr-only"
        aria-label={t("label")}
      />

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        disabled={disabled || uploading}
        className={`
          group relative flex items-center justify-center
          w-9 h-9 rounded-xl
          transition-all duration-200
          ${
            dragOver
              ? "bg-gold-100 border-gold-400 scale-105"
              : "bg-parchment-50 border-parchment-300 hover:border-gold-400 hover:bg-gold-50"
          }
          border
          disabled:opacity-40 disabled:cursor-not-allowed
        `}
        title={t("title")}
      >
        {uploading ? (
          <svg
            className="w-4 h-4 text-gold-600 animate-spin"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeDasharray="32"
              strokeLinecap="round"
            />
          </svg>
        ) : (
          <svg
            className="w-4 h-4 text-ink-500 group-hover:text-gold-700 transition-colors"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M3 13.5v2A1.5 1.5 0 004.5 17h11a1.5 1.5 0 001.5-1.5v-2" />
            <path d="M10 3v10M6.5 6.5L10 3l3.5 3.5" />
          </svg>
        )}
      </button>
    </>
  );
}
