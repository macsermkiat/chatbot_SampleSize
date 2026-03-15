"use client";

import { useState } from "react";
import { exportProtocol } from "@/lib/api";

interface ExportButtonProps {
  sessionId: string;
}

export default function ExportButton({ sessionId }: ExportButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleExport(format: "docx" | "pdf") {
    setLoading(true);
    setError(null);
    try {
      await exportProtocol(sessionId, format);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-parchment-700">
        Export Research Protocol
      </p>
      <div className="flex gap-2">
        <button
          onClick={() => handleExport("docx")}
          disabled={loading}
          className="flex-1 px-3 py-2 text-sm bg-parchment-100 border border-parchment-300 rounded-lg hover:bg-parchment-200 transition-colors disabled:opacity-50"
        >
          {loading ? "Generating..." : "Download DOCX"}
        </button>
        <button
          onClick={() => handleExport("pdf")}
          disabled={loading}
          className="flex-1 px-3 py-2 text-sm bg-parchment-100 border border-parchment-300 rounded-lg hover:bg-parchment-200 transition-colors disabled:opacity-50"
        >
          {loading ? "Generating..." : "Download PDF"}
        </button>
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
