import { test, expect } from "@playwright/test";

test.describe("SEO", () => {
  test("home page has title and meta description", async ({ page }) => {
    await page.goto("/");

    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title).toContain("Research Assistant");

    const description = page.locator('meta[name="description"]');
    await expect(description).toHaveAttribute("content", /medical research/i);
  });

  test("home page has Open Graph tags", async ({ page }) => {
    await page.goto("/");

    await expect(page.locator('meta[property="og:title"]')).toHaveAttribute(
      "content",
      /.+/,
    );
    await expect(page.locator('meta[property="og:description"]')).toHaveAttribute(
      "content",
      /.+/,
    );
    await expect(page.locator('meta[property="og:type"]')).toHaveAttribute(
      "content",
      "website",
    );
  });

  test("home page has Twitter card tags", async ({ page }) => {
    await page.goto("/");

    await expect(page.locator('meta[name="twitter:card"]')).toHaveAttribute(
      "content",
      "summary",
    );
    await expect(page.locator('meta[name="twitter:title"]')).toHaveAttribute(
      "content",
      /.+/,
    );
  });

  test("benchmark page has page-specific metadata", async ({ page }) => {
    await page.goto("/benchmark");

    const title = await page.title();
    expect(title).toContain("Benchmark");

    await expect(page.locator('meta[property="og:title"]')).toHaveAttribute(
      "content",
      /benchmark/i,
    );
  });

  test("robots.txt is accessible", async ({ page }) => {
    const response = await page.goto("/robots.txt");
    expect(response?.status()).toBe(200);

    const text = await page.locator("body").innerText();
    expect(text).toContain("User-Agent");
    expect(text).toContain("sitemap");
  });

  test("sitemap.xml is accessible", async ({ page }) => {
    const response = await page.goto("/sitemap.xml");
    expect(response?.status()).toBe(200);

    const text = await page.locator("body").innerText();
    expect(text).toContain("http");
  });

  test("html has lang attribute", async ({ page }) => {
    await page.goto("/");

    const lang = await page.locator("html").getAttribute("lang");
    expect(lang).toBe("en");
  });

  test("pages have proper heading hierarchy", async ({ page }) => {
    await page.goto("/");
    const h1Count = await page.locator("h1").count();
    expect(h1Count).toBe(1);

    await page.goto("/benchmark");
    const benchH1Count = await page.locator("h1").count();
    expect(benchH1Count).toBe(1);
  });

  test("does not expose X-Powered-By header", async ({ page }) => {
    const response = await page.goto("/");
    const poweredBy = response?.headers()["x-powered-by"];
    expect(poweredBy).toBeUndefined();
  });
});
