import { type Page, type Route } from "@playwright/test";

export interface SSEEvent {
  event?: string;
  data: Record<string, unknown>;
}

/**
 * Build an SSE response body from a sequence of events.
 */
function buildSSEBody(events: readonly SSEEvent[]): string {
  return events
    .map((e) => {
      const lines: string[] = [];
      if (e.event) lines.push(`event: ${e.event}`);
      lines.push(`data: ${JSON.stringify(e.data)}`);
      lines.push("");
      return lines.join("\n");
    })
    .join("\n");
}

/**
 * Intercept POST /api/chat and return a mocked SSE stream.
 * Optionally validates the request body before responding.
 */
export async function mockChatSSE(
  page: Page,
  events: readonly SSEEvent[],
  options?: {
    validateBody?: (body: Record<string, unknown>) => void;
    status?: number;
  },
): Promise<void> {
  await page.route("**/api/chat", async (route: Route) => {
    const request = route.request();
    if (request.method() !== "POST") {
      return route.fallback();
    }

    if (options?.validateBody) {
      const body = JSON.parse(request.postData() || "{}");
      options.validateBody(body);
    }

    const body = buildSSEBody(events);

    await route.fulfill({
      status: options?.status ?? 200,
      contentType: "text/event-stream",
      body,
    });
  });
}

/**
 * Standard "happy path" SSE events that simulate a single assistant response.
 */
export const HAPPY_RESPONSE: readonly SSEEvent[] = [
  {
    event: "progress",
    data: { status: "Analyzing your question..." },
  },
  {
    event: "message",
    data: {
      content: "Based on my analysis, here are the key research gaps in AI-assisted colonoscopy screening.",
      node: "orchestrator",
      phase: "orchestrator",
    },
  },
  {
    event: "done",
    data: {},
  },
];

/**
 * SSE events that include a phase change.
 */
export const PHASE_CHANGE_RESPONSE: readonly SSEEvent[] = [
  {
    event: "progress",
    data: { status: "Searching literature..." },
  },
  {
    event: "phase_change",
    data: { phase: "research_gap" },
  },
  {
    event: "message",
    data: {
      content: "I found several relevant studies on this topic.",
      node: "gap_search",
      phase: "research_gap",
    },
  },
  {
    event: "done",
    data: {},
  },
];

/**
 * SSE events that include a code block.
 */
export const CODE_RESPONSE: readonly SSEEvent[] = [
  {
    event: "message",
    data: {
      content: "Here is the sample size calculation:",
      node: "biostats_agent",
      phase: "biostatistics",
    },
  },
  {
    event: "code",
    data: {
      language: "python",
      script: "from scipy import stats\nn = stats.norm.ppf(0.975)**2 * 0.5 * 0.5 / 0.05**2\nprint(f'Required n = {n:.0f}')",
    },
  },
  {
    event: "done",
    data: {},
  },
];

/**
 * SSE events returning an error.
 */
export const ERROR_RESPONSE: readonly SSEEvent[] = [
  {
    event: "error",
    data: { error: "An internal error occurred. Please try again." },
  },
];

/**
 * Mock the keep-alive endpoint.
 */
export async function mockKeepAlive(page: Page): Promise<void> {
  await page.route("**/keep-alive", async (route: Route) => {
    await route.fulfill({ status: 200, body: JSON.stringify({ status: "ok" }) });
  });
}

/**
 * Mock the sessions endpoint.
 */
export async function mockSessions(page: Page): Promise<void> {
  await page.route("**/api/sessions", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        session_id: "test-session-id",
        created_at: new Date().toISOString(),
        current_phase: "orchestrator",
      }),
    });
  });
}

/**
 * Mock the end session endpoint.
 */
export async function mockEndSession(page: Page): Promise<void> {
  await page.route("**/api/sessions/*/end", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        session_id: "test-session-id",
        ended_at: new Date().toISOString(),
      }),
    });
  });
}

/**
 * Mock the session summary endpoint.
 */
export async function mockSessionSummary(
  page: Page,
  summaryText: string = "This consultation covered sample size calculation for a two-arm RCT. The researcher needs approximately 200 participants per arm.",
): Promise<void> {
  await page.route("**/api/sessions/*/summary", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        session_id: "test-session-id",
        summary_text: summaryText,
        generated_at: new Date().toISOString(),
      }),
    });
  });
}
