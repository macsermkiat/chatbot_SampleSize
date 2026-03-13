import { test, expect } from "@playwright/test";
import {
  mockChatSSE,
  mockKeepAlive,
  HAPPY_RESPONSE,
  PHASE_CHANGE_RESPONSE,
  CODE_RESPONSE,
  ERROR_RESPONSE,
} from "../fixtures/sse-mock";

test.describe("Home Page", () => {
  test.beforeEach(async ({ page }) => {
    await mockKeepAlive(page);
  });

  test("renders welcome state with heading and expertise picker", async ({ page }) => {
    await page.goto("/");

    await expect(page.locator("h1")).toContainText("Research Assistant");
    await expect(page.getByText("How should I explain things?")).toBeVisible();
    await expect(page.getByText("Getting Started")).toBeVisible();
    await expect(page.getByText("Advanced")).toBeVisible();
  });

  test("shows starter prompts after selecting expertise level", async ({ page }) => {
    await page.goto("/");

    await page.getByText("Getting Started").click();

    await expect(page.getByText("Try asking")).toBeVisible();
    await expect(
      page.getByText("Find research gaps in AI-assisted colonoscopy screening"),
    ).toBeVisible();
    await expect(
      page.getByText("Design a cohort study for statin use and dementia risk"),
    ).toBeVisible();
    await expect(
      page.getByText("Calculate sample size for a two-arm RCT"),
    ).toBeVisible();
  });

  test("sends message via starter prompt and displays response", async ({ page }) => {
    await mockChatSSE(page, HAPPY_RESPONSE);
    await page.goto("/");

    // Select expertise
    await page.getByText("Advanced").click();

    // Click a starter prompt
    await page
      .getByText("Find research gaps in AI-assisted colonoscopy screening")
      .click();

    // User message should appear
    await expect(
      page.getByText("Find research gaps in AI-assisted colonoscopy screening").last(),
    ).toBeVisible();

    // Assistant response should appear
    await expect(
      page.getByText("Based on my analysis", { exact: false }),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("sends message via text input and Enter key", async ({ page }) => {
    await mockChatSSE(page, HAPPY_RESPONSE);
    await page.goto("/");

    // Select expertise
    await page.getByText("Getting Started").click();

    // Type in textarea
    const textarea = page.getByPlaceholder("Describe your research question...");
    await textarea.fill("What is the best study design for my RCT?");
    await textarea.press("Enter");

    // User message appears
    await expect(
      page.getByText("What is the best study design for my RCT?"),
    ).toBeVisible();

    // Assistant response appears
    await expect(
      page.getByText("Based on my analysis", { exact: false }),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("displays typing indicator while streaming", async ({ page }) => {
    // Use a delayed route to observe the typing indicator
    await page.route("**/api/chat", async (route) => {
      // Delay 2s before responding to see the indicator
      await new Promise((r) => setTimeout(r, 1500));

      const body = [
        "event: progress\ndata: " + JSON.stringify({ status: "Thinking..." }) + "\n\n",
        "event: message\ndata: " + JSON.stringify({ content: "Done.", node: "orchestrator", phase: "orchestrator" }) + "\n\n",
        "event: done\ndata: {}\n\n",
      ].join("");

      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body,
      });
    });

    await page.goto("/");
    await page.getByText("Advanced").click();

    const textarea = page.getByPlaceholder("Describe your research question...");
    await textarea.fill("Test message");
    await textarea.press("Enter");

    // Typing indicator should be visible while streaming
    await expect(page.getByText("Thinking...")).toBeVisible({ timeout: 5_000 });

    // After response completes, assistant message should appear
    await expect(page.getByText("Done.")).toBeVisible({ timeout: 10_000 });
  });

  test("handles phase change events", async ({ page }) => {
    await mockChatSSE(page, PHASE_CHANGE_RESPONSE);
    await page.goto("/");

    await page.getByText("Getting Started").click();
    await page
      .getByText("Find research gaps in AI-assisted colonoscopy screening")
      .click();

    // Message from the new phase should appear
    await expect(
      page.getByText("I found several relevant studies", { exact: false }),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("handles code block events", async ({ page }) => {
    await mockChatSSE(page, CODE_RESPONSE);
    await page.goto("/");

    await page.getByText("Advanced").click();
    await page
      .getByText("Calculate sample size for a two-arm RCT")
      .click();

    // Code content should be visible
    await expect(
      page.getByText("from scipy import stats", { exact: false }),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("shows error message on SSE error event", async ({ page }) => {
    await mockChatSSE(page, ERROR_RESPONSE);
    await page.goto("/");

    await page.getByText("Getting Started").click();
    await page
      .getByText("Design a cohort study for statin use and dementia risk")
      .click();

    await expect(
      page.getByText("Something went wrong", { exact: false }),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("shows network error when server is unreachable", async ({ page }) => {
    await page.route("**/api/chat", (route) => route.abort("connectionrefused"));
    await page.goto("/");

    await page.getByText("Advanced").click();

    const textarea = page.getByPlaceholder("Describe your research question...");
    await textarea.fill("Test network error");
    await textarea.press("Enter");

    // Should show error message (either network error or generic)
    await expect(
      page.getByText(/couldn't reach the server|went wrong/i),
    ).toBeVisible({ timeout: 15_000 });
  });

  test("expertise toggle changes displayed level", async ({ page }) => {
    await mockChatSSE(page, HAPPY_RESPONSE);
    await page.goto("/");

    // Select simple first
    await page.getByText("Getting Started").click();

    // Header should show "Simple"
    await expect(page.getByTitle("Click to switch expertise level")).toContainText("Simple");

    // Click to toggle
    await page.getByTitle("Click to switch expertise level").click();
    await expect(page.getByTitle("Click to switch expertise level")).toContainText("Advanced");
  });

  test("has link to benchmark page", async ({ page }) => {
    await page.goto("/");

    const benchmarkLink = page.getByRole("link", { name: /vs GPT-5/i });
    await expect(benchmarkLink).toBeVisible();
    await expect(benchmarkLink).toHaveAttribute("href", "/benchmark");
  });

  test("disables input while streaming", async ({ page }) => {
    // Use a very slow response
    await page.route("**/api/chat", async (route) => {
      await new Promise((r) => setTimeout(r, 3000));
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: "event: done\ndata: {}\n\n",
      });
    });

    await page.goto("/");
    await page.getByText("Advanced").click();

    const textarea = page.getByPlaceholder("Describe your research question...");
    await textarea.fill("Test");
    await textarea.press("Enter");

    // Textarea should be disabled during streaming
    await expect(textarea).toBeDisabled({ timeout: 2_000 });
  });
});
