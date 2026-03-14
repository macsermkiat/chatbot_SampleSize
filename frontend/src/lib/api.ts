import { fetchWithRetry } from "./retry";

const API_BASE = "/api";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  node?: string;
  phase?: string;
  timestamp: number;
}

export interface ChatEventData {
  node?: string;
  content?: string;
  phase?: string;
  status?: string;
  error?: string;
  language?: string;
  script?: string;
  session_id?: string;
}

export interface FileUploadResult {
  filename: string;
  mime_type: string;
  extracted_text: string;
  char_count: number;
  has_tables: boolean;
  extraction_quality: "full" | "partial" | "metadata_only" | "empty";
  warning: string | null;
}

/**
 * Stream chat responses via SSE from POST /api/chat.
 * Yields parsed events as they arrive.
 */
export async function* streamChat(
  message: string,
  sessionId: string,
  expertiseLevel?: "simple" | "advanced",
  uploadedFiles?: { filename: string; mime_type: string; extracted_text: string }[],
  signal?: AbortSignal,
): AsyncGenerator<{ event: string; data: ChatEventData }> {
  const body: Record<string, unknown> = {
    message,
    session_id: sessionId,
  };
  if (expertiseLevel) {
    body.expertise_level = expertiseLevel;
  }
  if (uploadedFiles && uploadedFiles.length > 0) {
    body.uploaded_files = uploadedFiles;
  }

  const response = await fetchWithRetry(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    const msg = detail?.detail || detail?.error || `Server error (${response.status})`;
    throw new Error(msg);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";
  let currentEvent = "message";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        const raw = line.slice(6).trim();
        if (!raw) continue;
        try {
          const data = JSON.parse(raw) as ChatEventData;
          yield { event: currentEvent, data };
          currentEvent = "message"; // reset after yielding
        } catch {
          if (process.env.NODE_ENV !== "production") {
            console.warn("[SSE] Malformed JSON skipped:", raw.slice(0, 200));
          }
        }
      } else if (line.trim() === "") {
        // Blank line = SSE event delimiter, reset event type
        currentEvent = "message";
      }
    }
  }

  // Flush any remaining buffered bytes from the decoder
  const remaining = decoder.decode();
  if (remaining) {
    buffer += remaining;
  }

  // Parse any remaining buffer content (final SSE lines without trailing newline)
  if (buffer.trim()) {
    const finalLines = buffer.split("\n");
    for (const line of finalLines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        const raw = line.slice(6).trim();
        if (!raw) continue;
        try {
          const data = JSON.parse(raw) as ChatEventData;
          yield { event: currentEvent, data };
          currentEvent = "message";
        } catch {
          // Skip malformed final chunk
        }
      }
    }
  }
}

/**
 * Upload a file for text extraction.
 */
export async function uploadFile(file: File, signal?: AbortSignal): Promise<FileUploadResult> {
  const form = new FormData();
  form.append("file", file);

  const response = await fetchWithRetry(`${API_BASE}/upload`, {
    method: "POST",
    body: form,
    signal,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }

  return response.json();
}

/**
 * Create a new session.
 */
export async function createSession(): Promise<{
  session_id: string;
  created_at: string;
  current_phase: string;
}> {
  const response = await fetchWithRetry(`${API_BASE}/sessions`, { method: "POST" });
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(
      `Failed to create session (${response.status}): ${body || response.statusText}`,
    );
  }
  return response.json();
}

/**
 * End a chat session.
 */
export async function endSession(
  sessionId: string,
): Promise<{ session_id: string; ended_at: string }> {
  const response = await fetchWithRetry(`${API_BASE}/sessions/${sessionId}/end`, {
    method: "POST",
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to end session" }));
    throw new Error(err.detail || "Failed to end session");
  }
  return response.json();
}

/**
 * Get a consultation summary for the session.
 */
export async function getSessionSummary(
  sessionId: string,
): Promise<{ session_id: string; summary_text: string; generated_at: string }> {
  const response = await fetchWithRetry(`${API_BASE}/sessions/${sessionId}/summary`);
  if (!response.ok) {
    const err = await response
      .json()
      .catch(() => ({ detail: "Failed to generate summary" }));
    throw new Error(err.detail || "Failed to generate summary");
  }
  return response.json();
}

/**
 * Download session summary as a .txt file.
 */
export async function downloadSummary(sessionId: string): Promise<void> {
  const { summary_text, generated_at } = await getSessionSummary(sessionId);
  const date = new Date(generated_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const fileContent = [
    "Medical Research Consultation Summary",
    `Date: ${date}`,
    `Session: ${sessionId}`,
    "Generated by: SampleSize AI Research Assistant",
    "",
    "---",
    "",
    summary_text,
    "",
    "---",
    "Note: This summary was AI-generated. Please verify all statistical",
    "recommendations with qualified professionals before proceeding.",
  ].join("\n");

  const blob = new Blob([fileContent], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `consultation-summary-${sessionId.slice(0, 8)}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Submit a session evaluation (star rating + optional comment).
 */
export async function submitEvaluation(
  sessionId: string,
  rating: number,
  comment: string,
): Promise<{ session_id: string; rating: number; comment: string; created_at: string }> {
  const response = await fetchWithRetry(`${API_BASE}/sessions/${sessionId}/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rating, comment }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to submit evaluation" }));
    throw new Error(err.detail || "Failed to submit evaluation");
  }
  return response.json();
}

/**
 * Generate a client-side unique ID.
 */
export function uid(): string {
  return crypto.randomUUID();
}
