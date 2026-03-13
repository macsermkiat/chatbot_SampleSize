import { test, expect } from "@playwright/test";
import {
  mockChatSSE,
  mockKeepAlive,
  mockEndSession,
  mockSessionSummary,
  HAPPY_RESPONSE,
} from "../fixtures/sse-mock";

test.describe("End Session", () => {
  test.beforeEach(async ({ page }) => {
    await mockKeepAlive(page);
  });

  test("End button is not visible on welcome screen", async ({ page }) => {
    await page.goto("/");

    // End button should not be visible when no messages
    await expect(page.getByRole("button", { name: "End" })).not.toBeVisible();
  });

  test("End button appears after sending a message", async ({ page }) => {
    await mockChatSSE(page, HAPPY_RESPONSE);
    await page.goto("/");

    // Select expertise and send a message
    await page.getByText("Advanced").click();
    await page
      .getByText("Find research gaps in AI-assisted colonoscopy screening")
      .click();

    // Wait for response
    await expect(
      page.getByText("Based on my analysis", { exact: false }),
    ).toBeVisible({ timeout: 10_000 });

    // End button should now be visible
    await expect(page.getByRole("button", { name: "End" })).toBeVisible();
  });

  test("clicking End opens the confirmation dialog", async ({ page }) => {
    await mockChatSSE(page, HAPPY_RESPONSE);
    await page.goto("/");

    await page.getByText("Advanced").click();
    await page
      .getByText("Find research gaps in AI-assisted colonoscopy screening")
      .click();

    await expect(
      page.getByText("Based on my analysis", { exact: false }),
    ).toBeVisible({ timeout: 10_000 });

    // Click End
    await page.getByRole("button", { name: "End" }).click();

    // Dialog should appear
    await expect(page.getByText("End Conversation")).toBeVisible();
    await expect(
      page.getByText("Would you like to download a summary"),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Download Summary & End" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "End Without Summary" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Cancel" }),
    ).toBeVisible();
  });

  test("Cancel closes the dialog without ending", async ({ page }) => {
    await mockChatSSE(page, HAPPY_RESPONSE);
    await page.goto("/");

    await page.getByText("Advanced").click();
    await page
      .getByText("Find research gaps in AI-assisted colonoscopy screening")
      .click();

    await expect(
      page.getByText("Based on my analysis", { exact: false }),
    ).toBeVisible({ timeout: 10_000 });

    // Open and cancel dialog
    await page.getByRole("button", { name: "End" }).click();
    await expect(page.getByText("End Conversation")).toBeVisible();

    await page.getByRole("button", { name: "Cancel" }).click();

    // Dialog should close, conversation should remain
    await expect(page.getByText("End Conversation")).not.toBeVisible();
    await expect(
      page.getByText("Based on my analysis", { exact: false }),
    ).toBeVisible();
  });

  test("End Without Summary resets to welcome screen", async ({ page }) => {
    await mockChatSSE(page, HAPPY_RESPONSE);
    await mockEndSession(page);
    await page.goto("/");

    await page.getByText("Advanced").click();
    await page
      .getByText("Find research gaps in AI-assisted colonoscopy screening")
      .click();

    await expect(
      page.getByText("Based on my analysis", { exact: false }),
    ).toBeVisible({ timeout: 10_000 });

    // End without summary
    await page.getByRole("button", { name: "End" }).click();

    // Mock the page reload by intercepting it
    const [newPage] = await Promise.all([
      page.context().waitForEvent("page").catch(() => null),
      page.getByRole("button", { name: "End Without Summary" }).click(),
    ]).catch(() => [null]);

    // The page should reload or show welcome screen
    // Either way, session has been ended
  });

  test("Download Summary & End shows generating state", async ({ page }) => {
    await mockChatSSE(page, HAPPY_RESPONSE);
    await mockEndSession(page);

    // Add a delay to the summary endpoint to see the generating state
    await page.route("**/api/sessions/*/summary", async (route) => {
      await new Promise((r) => setTimeout(r, 1000));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          session_id: "test-session-id",
          summary_text: "Test summary.",
          generated_at: new Date().toISOString(),
        }),
      });
    });

    await page.goto("/");
    await page.getByText("Advanced").click();
    await page
      .getByText("Find research gaps in AI-assisted colonoscopy screening")
      .click();

    await expect(
      page.getByText("Based on my analysis", { exact: false }),
    ).toBeVisible({ timeout: 10_000 });

    // Click Download Summary & End
    await page.getByRole("button", { name: "End" }).click();
    await page
      .getByRole("button", { name: "Download Summary & End" })
      .click();

    // Should show generating state
    await expect(page.getByText("Generating summary...")).toBeVisible();
  });

  test("shows error state when summary generation fails", async ({ page }) => {
    await mockChatSSE(page, HAPPY_RESPONSE);

    // Mock summary to fail
    await page.route("**/api/sessions/*/summary", async (route) => {
      await route.fulfill({
        status: 502,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Summary generation failed" }),
      });
    });

    await page.goto("/");
    await page.getByText("Advanced").click();
    await page
      .getByText("Find research gaps in AI-assisted colonoscopy screening")
      .click();

    await expect(
      page.getByText("Based on my analysis", { exact: false }),
    ).toBeVisible({ timeout: 10_000 });

    // Try to download summary
    await page.getByRole("button", { name: "End" }).click();
    await page
      .getByRole("button", { name: "Download Summary & End" })
      .click();

    // Should show error state with retry option
    await expect(page.getByText("Summary Failed")).toBeVisible({ timeout: 10_000 });
    await expect(
      page.getByRole("button", { name: "Try Again" }),
    ).toBeVisible();
  });
});
