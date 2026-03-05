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
    throw new Error(`Chat request failed: ${response.status}`);
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
          // Skip malformed JSON
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
}

/**
 * Upload a file for text extraction.
 */
export async function uploadFile(file: File): Promise<FileUploadResult> {
  const form = new FormData();
  form.append("file", file);

  const response = await fetchWithRetry(`${API_BASE}/upload`, {
    method: "POST",
    body: form,
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
  if (!response.ok) throw new Error("Failed to create session");
  return response.json();
}

/**
 * Generate a client-side unique ID.
 */
export function uid(): string {
  return crypto.randomUUID();
}
