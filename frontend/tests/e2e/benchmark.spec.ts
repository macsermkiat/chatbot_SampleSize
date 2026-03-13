import { test, expect } from "@playwright/test";

test.describe("Benchmark Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/benchmark");
  });

  test("renders heading and key content", async ({ page }) => {
    await expect(page.locator("h1")).toContainText("Outperforming GPT-5");
    await expect(page.getByText("Research Assistant", { exact: false }).first()).toBeVisible();
  });

  test("displays win/loss/tie data", async ({ page }) => {
    // The page should show the win-loss breakdown
    await expect(page.getByText("13").first()).toBeVisible();
    await expect(page.getByText(/wins/i).first()).toBeVisible();
  });

  test("has navigation back to home", async ({ page }) => {
    const homeLink = page.getByRole("link", { name: "Back to App" });
    await expect(homeLink).toBeVisible();
  });

  test("renders dimension score tables", async ({ page }) => {
    // Check for specific dimension names from the data using cells
    await expect(page.getByRole("cell", { name: /Statistical Test Selection/i }).first()).toBeVisible();
    await expect(page.getByRole("cell", { name: /Sample Size Calculation/i }).first()).toBeVisible();
    await expect(page.getByRole("cell", { name: /Code Correctness/i }).first()).toBeVisible();
  });

  test("shows domain sections", async ({ page }) => {
    await expect(page.getByText("Biostatistics", { exact: false }).first()).toBeVisible();
    await expect(page.getByText("Methodology", { exact: false }).first()).toBeVisible();
  });

  test("shows expandable remarks", async ({ page }) => {
    // Look for remark toggle buttons (the ones with expandable explanations)
    const remarkButtons = page.locator("button").filter({ hasText: /why/i });
    if (await remarkButtons.count() > 0) {
      await remarkButtons.first().click();
      // After clicking, remark text should be visible
      await expect(
        page.getByText("clarif", { exact: false }),
      ).toBeVisible({ timeout: 5_000 });
    }
  });

  test("page has correct SEO metadata", async ({ page }) => {
    const title = await page.title();
    expect(title).toContain("Benchmark");

    const description = page.locator('meta[name="description"]');
    await expect(description).toHaveAttribute("content", /.+/);
  });
});
