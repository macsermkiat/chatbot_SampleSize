import { fetchWithRetry } from "./retry";
import { createClient } from "./supabase/client";

const API_BASE = "/api";

/**
 * Get the current Supabase session access token, or null if unauthenticated.
 */
async function getAccessToken(): Promise<string | null> {
  try {
    const supabase = createClient();
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  } catch {
    return null;
  }
}

/**
 * Build headers with auth token if available.
 */
async function authHeaders(
  extra?: Record<string, string>,
): Promise<Record<string, string>> {
  const headers: Record<string, string> = { ...extra };
  const token = await getAccessToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  node?: string;
  phase?: string;
  confidence?: "high" | "medium" | "low";
  timestamp: number;
}

export interface ChatEventData {
  node?: string;
  content?: string;
  phase?: string;
  confidence?: "high" | "medium" | "low";
  status?: string;
  error?: string;
  code?: string;
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

  const headers = await authHeaders({ "Content-Type": "application/json" });
  const response = await fetchWithRetry(`${API_BASE}/chat`, {
    method: "POST",
    headers,
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

  const headers = await authHeaders();
  const response = await fetchWithRetry(`${API_BASE}/upload`, {
    method: "POST",
    headers,
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
  const headers = await authHeaders();
  const response = await fetchWithRetry(`${API_BASE}/sessions/${sessionId}/end`, {
    method: "POST",
    headers,
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
  const headers = await authHeaders();
  const response = await fetchWithRetry(`${API_BASE}/sessions/${sessionId}/summary`, {
    headers,
  });
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
    "Generated by: ProtoCol",
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
  const headers = await authHeaders({ "Content-Type": "application/json" });
  const response = await fetchWithRetry(`${API_BASE}/sessions/${sessionId}/evaluate`, {
    method: "POST",
    headers,
    body: JSON.stringify({ rating, comment }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to submit evaluation" }));
    throw new Error(err.detail || "Failed to submit evaluation");
  }
  return response.json();
}

/**
 * Export session as a formatted protocol document (DOCX or PDF).
 */
export async function exportProtocol(
  sessionId: string,
  format: "docx" | "pdf" = "docx",
): Promise<void> {
  const headers = await authHeaders();
  const response = await fetchWithRetry(
    `${API_BASE}/sessions/${sessionId}/export?format=${format}`,
    { headers },
  );

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Export failed" }));
    throw new Error(err.detail || "Export failed");
  }

  const blob = await response.blob();
  const ext = format === "pdf" ? "pdf" : "docx";
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `protocol-${sessionId.slice(0, 8)}.${ext}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Get the current user's subscription info.
 */
export async function getSubscription(): Promise<{
  tier: string;
  status?: string;
  urls?: { customer_portal?: string; update_payment_method?: string };
}> {
  const headers = await authHeaders();
  const response = await fetchWithRetry(`${API_BASE}/billing/subscription`, {
    headers,
  });
  if (!response.ok) {
    return { tier: "free" };
  }
  return response.json();
}

/**
 * Get the current user's query usage for this billing period.
 */
export async function getUsage(): Promise<{
  tier: string;
  query_count: number;
  query_limit: number | null;
  is_allowed: boolean;
  project_count: number;
  project_limit: number | null;
  can_create_project: boolean;
}> {
  const headers = await authHeaders();
  const response = await fetchWithRetry(`${API_BASE}/billing/usage`, {
    headers,
  });
  if (!response.ok) {
    return {
      tier: "free",
      query_count: 0,
      query_limit: 5,
      is_allowed: true,
      project_count: 0,
      project_limit: 1,
      can_create_project: true,
    };
  }
  return response.json();
}

/**
 * Create a LemonSqueezy checkout session.
 */
export async function createCheckout(
  variantId: string,
): Promise<{ checkout_url: string }> {
  const headers = await authHeaders({ "Content-Type": "application/json" });
  const response = await fetchWithRetry(`${API_BASE}/billing/checkout`, {
    method: "POST",
    headers,
    body: JSON.stringify({ variant_id: variantId }),
  });
  if (!response.ok) {
    const err = await response
      .json()
      .catch(() => ({ detail: "Checkout failed" }));
    throw new Error(err.detail || "Checkout failed");
  }
  return response.json();
}

/**
 * Upgrade subscription to a higher tier variant (immediate with proration).
 */
export async function upgradeSubscription(
  targetVariantId: string,
): Promise<{ tier: string; variant_id: string }> {
  const headers = await authHeaders({ "Content-Type": "application/json" });
  const response = await fetchWithRetry(
    `${API_BASE}/billing/subscription/upgrade`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({ target_variant_id: targetVariantId }),
    },
  );
  if (!response.ok) {
    const err = await response
      .json()
      .catch(() => ({ detail: "Upgrade failed" }));
    throw new Error(err.detail || "Upgrade failed");
  }
  return response.json();
}

/**
 * Cancel subscription at end of current billing period.
 */
export async function cancelSubscription(): Promise<{
  ends_at: string | null;
}> {
  const headers = await authHeaders();
  const response = await fetchWithRetry(
    `${API_BASE}/billing/subscription/cancel`,
    { method: "POST", headers },
  );
  if (!response.ok) {
    const err = await response
      .json()
      .catch(() => ({ detail: "Cancellation failed" }));
    throw new Error(err.detail || "Cancellation failed");
  }
  return response.json();
}

// --- User Profile ---

export interface UserProfile {
  user_id: string;
  full_name: string | null;
  role: string | null;
  institution: string | null;
  research_area: string | null;
  onboarding_completed: boolean;
}

export interface ProfileUpdate {
  full_name?: string | null;
  role?: string | null;
  institution?: string | null;
  research_area?: string | null;
}

/**
 * Get the current user's profile.
 */
export async function getProfile(): Promise<UserProfile> {
  const headers = await authHeaders();
  const response = await fetchWithRetry(`${API_BASE}/profile`, { headers });
  if (!response.ok) {
    throw new Error("Failed to load profile");
  }
  return response.json();
}

/**
 * Update the current user's profile fields.
 */
export async function updateProfile(data: ProfileUpdate): Promise<UserProfile> {
  const headers = await authHeaders({ "Content-Type": "application/json" });
  const response = await fetchWithRetry(`${API_BASE}/profile`, {
    method: "PATCH",
    headers,
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to update profile" }));
    throw new Error(err.detail || "Failed to update profile");
  }
  return response.json();
}

/**
 * Complete onboarding with profile data.
 */
export async function completeOnboarding(data: ProfileUpdate): Promise<UserProfile> {
  const headers = await authHeaders({ "Content-Type": "application/json" });
  const response = await fetchWithRetry(`${API_BASE}/profile/complete-onboarding`, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to complete onboarding" }));
    throw new Error(err.detail || "Failed to complete onboarding");
  }
  return response.json();
}

// --- Saved Projects ---

export interface ProjectListItem {
  session_id: string;
  name: string | null;
  description: string | null;
  current_phase: string;
  created_at: string;
  updated_at: string | null;
  ended_at: string | null;
}

export interface ProjectListResponse {
  items: ProjectListItem[];
  total: number;
}

export interface ProjectUpdateResponse {
  session_id: string;
  name: string;
  description: string | null;
  updated_at: string;
}

export interface MessageItem {
  role: string;
  content: string;
  node: string | null;
  phase: string | null;
  created_at: string;
}

/**
 * List the current user's research projects (sessions).
 */
export async function getProjects(
  q?: string,
  limit?: number,
  offset?: number,
): Promise<ProjectListResponse> {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (limit !== undefined) params.set("limit", String(limit));
  if (offset !== undefined) params.set("offset", String(offset));

  const qs = params.toString();
  const url = `${API_BASE}/projects${qs ? `?${qs}` : ""}`;
  const headers = await authHeaders();
  const response = await fetchWithRetry(url, { headers });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to load projects" }));
    throw new Error(err.detail || "Failed to load projects");
  }
  return response.json();
}

/**
 * Update a project's name and/or description.
 */
export async function updateProject(
  sessionId: string,
  name: string,
  description?: string | null,
): Promise<ProjectUpdateResponse> {
  const headers = await authHeaders({ "Content-Type": "application/json" });
  const response = await fetchWithRetry(`${API_BASE}/projects/${sessionId}`, {
    method: "PATCH",
    headers,
    body: JSON.stringify({ name, description: description ?? null }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to update project" }));
    throw new Error(err.detail || "Failed to update project");
  }
  return response.json();
}

/**
 * Soft-delete a project (session).
 */
export async function deleteProject(sessionId: string): Promise<void> {
  const headers = await authHeaders();
  const response = await fetchWithRetry(`${API_BASE}/projects/${sessionId}`, {
    method: "DELETE",
    headers,
  });
  if (!response.ok && response.status !== 204) {
    const err = await response.json().catch(() => ({ detail: "Failed to delete project" }));
    throw new Error(err.detail || "Failed to delete project");
  }
}

/**
 * Get message history for a session (for resuming).
 */
export async function getSessionMessages(
  sessionId: string,
): Promise<MessageItem[]> {
  const headers = await authHeaders();
  const response = await fetchWithRetry(
    `${API_BASE}/sessions/${sessionId}/messages`,
    { headers },
  );
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Failed to load messages" }));
    throw new Error(err.detail || "Failed to load messages");
  }
  const data = await response.json();
  return data.messages;
}

/**
 * Generate a client-side unique ID.
 */
export function uid(): string {
  return crypto.randomUUID();
}
