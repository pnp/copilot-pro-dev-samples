import { expect, test } from "@playwright/test";

test.beforeEach(async ({ context }) => {
  await context.route(/^https?:\/\/(?!127\.0\.0\.1:4330)/, (route) => route.abort());
});

test("navigation matches the community gallery and reaches all top pages", async ({ page, isMobile }) => {
  await page.goto("./");
  const navigation = page.getByRole("navigation", { name: isMobile ? "Mobile navigation" : "Primary navigation", exact: true });
  if (isMobile) await page.getByLabel("Open navigation", { exact: true }).click();
  await expect(navigation.getByRole("link").first()).toHaveText("Community");
  await expect(navigation.getByRole("link").first()).toHaveAttribute("href", "https://aka.ms/community/home");
  await expect(navigation.getByRole("link").first().locator("svg")).toHaveCount(1);
  const links = [
    ["Getting started", "From sample to working agent"],
    ["Contributors", "Contributors"],
    ["Contributing", "Share what you build"],
    ["What's new", "What's new"],
  ];
  for (const [label, heading] of links) {
    if (isMobile && !(await page.locator(".mobile-nav[open]").count())) {
      await page.getByLabel("Open navigation", { exact: true }).click();
    }
    await navigation.getByRole("link", { name: label, exact: true }).click();
    await expect(page.getByRole("heading", { name: heading, level: 1, exact: true })).toBeVisible();
    if (isMobile) await page.getByLabel("Open navigation", { exact: true }).click();
    await expect(navigation.getByRole("link", { name: label, exact: true })).toHaveAttribute("aria-current", "page");
  }
});

test("theme is keyboard accessible and persists across navigation and reload", async ({ page }) => {
  await page.goto("./");
  const toggle = page.getByRole("switch");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await toggle.focus();
  await toggle.press("Space");
  await expect(toggle).toHaveAttribute("aria-checked", "true");
  await expect(toggle).toHaveAccessibleName("Switch to light mode");
  await page.goto("getting-started/");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.getByRole("switch")).toHaveAttribute("aria-checked", "true");
  await page.getByRole("switch").click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});

test("themes still work when local storage is unavailable", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", { get() { throw new Error("Storage blocked"); } });
  });
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("./");
  await page.getByRole("switch").click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  expect(errors).toEqual([]);
});

test("catalog search, type filtering, empty state and shared URLs work", async ({ page }) => {
  await page.goto("samples/");
  const cards = page.locator("#samples-grid [data-sample-card]");
  const count = await cards.count();
  expect(count).toBeGreaterThan(0);
  await page.getByLabel("Search samples", { exact: true }).fill("ristorante");
  await expect(page.locator("#samples-grid [data-sample-card]:visible").first()).toBeVisible();
  expect(await page.locator("#samples-grid [data-sample-card]:visible").count()).toBeLessThan(count);
  await page.reload();
  await expect(page.getByLabel("Search samples", { exact: true })).toHaveValue("ristorante");
  await page.getByRole("button", { name: "Clear filters", exact: true }).first().click();
  await page.getByLabel("Sample type", { exact: true }).selectOption("Copilot Studio");
  for (const card of await page.locator("#samples-grid [data-sample-card]:visible").all()) {
    await expect(card).toHaveAttribute("data-type", "Copilot Studio");
  }
  await page.getByLabel("Search samples", { exact: true }).fill("no-such-sample-012345");
  await expect(page.getByRole("heading", { name: "No samples found" })).toBeVisible();
  await page.locator("#empty-clear").click();
  await expect(page.locator("#samples-grid [data-sample-card]:visible")).toHaveCount(count);
});

test("sample pages preserve source/download links and avoid duplicate tracker requests", async ({ page }) => {
  await page.goto("samples/");
  await page.locator("#samples-grid h3 a").first().click();
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.getByRole("link", { name: "Open source folder" })).toHaveAttribute("href", /github\.com\/pnp\/copilot-pro-dev-samples\/tree\/main\/samples\//);
  await expect(page.getByRole("link", { name: "Download sample", exact: true })).toHaveAttribute("href", /download-partial/);
  const trackers = page.locator('img[src*="m365-visitor-stats.azurewebsites.net"]');
  await expect(trackers).toHaveCount(1);
  const samplePath = new URL(page.url()).pathname.replace("/copilot-pro-dev-samples/", "").replace(/\/$/, "");
  await expect(trackers).toHaveAttribute("src", `https://m365-visitor-stats.azurewebsites.net/copilot-pro-dev-samples/${samplePath}`);
});

test("local backgrounds, badge, font, and colour spectrum match the reference design", async ({ page }) => {
  await page.goto("./");
  const style = await page.locator(".spectrum").evaluate((element) => getComputedStyle(element).backgroundImage);
  expect(style).toContain("rgb(7, 95, 206)");
  expect(style).toContain("rgb(19, 138, 61)");
  expect(style).toContain("rgb(179, 38, 135)");
  expect(style).toContain("rgb(216, 79, 56)");
  const backdrop = await page.locator(".catalog-backdrop").evaluate((element) => getComputedStyle(element).backgroundImage);
  expect(backdrop).toContain("/copilot-pro-dev-samples/images/side-bg-right.webp");
  expect(backdrop).toContain("/copilot-pro-dev-samples/images/side-bg-left.webp");
  const badge = page.locator(".contribution-callout img");
  await badge.scrollIntoViewIfNeeded();
  await expect(badge).toHaveJSProperty("naturalWidth", 500);
  const font = await page.locator("body").evaluate((element) => getComputedStyle(element).fontFamily);
  expect(font).toContain("Parker");
  await page.locator(".contribution-callout").getByRole("link", { name: "Contribute a sample", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Share what you build" })).toBeVisible();
});

test("contributors prominently call out community recognition before the directory", async ({ page }) => {
  await page.goto("contributors/");
  const recognition = page.getByRole("region", { name: "Sharing is caring", exact: true });
  await expect(recognition.getByText("Community recognition", { exact: true })).toBeVisible();
  await expect(recognition.getByRole("link", { name: "Learn about community recognition" })).toHaveAttribute("href", "https://aka.ms/community/recognition");
  const badge = recognition.getByRole("img", { name: "Microsoft 365 and Power Platform Community contributor badge" });
  await badge.scrollIntoViewIfNeeded();
  await expect(badge).toHaveAttribute("src", "/copilot-pro-dev-samples/images/contributor-badge.webp");
  await expect(badge).toHaveJSProperty("naturalWidth", 500);
  const beforeDirectory = await recognition.evaluate((element) => {
    const directory = document.querySelector(".contributor-grid");
    return directory !== null && Boolean(element.compareDocumentPosition(directory) & Node.DOCUMENT_POSITION_FOLLOWING);
  });
  expect(beforeDirectory).toBe(true);
});

for (const { route, selector, accounts, size } of [
  { route: "contributors/", selector: ".contributor-card", accounts: ["ayronjohnson", "YugalPradhan31"], size: 72 },
  { route: "samples/da-CanvasStudent/", selector: ".detail-authors a", accounts: ["ayronjohnson"], size: 36 },
]) {
  test(`profile images use a local placeholder after a 404 on ${route}`, async ({ page }) => {
    await page.route(/^https:\/\/github\.com\/(?:ayronjohnson|YugalPradhan31)\.png$/i, (route) =>
      route.fulfill({ status: 404, contentType: "text/plain", body: "Not Found" }),
    );
    await page.goto(route);
    for (const account of accounts) {
      const profile = page.locator(`a[href="https://github.com/${account}"]`);
      const avatar = selector === ".contributor-card"
        ? page.locator(selector).filter({ has: profile }).locator("img")
        : profile.locator("img");
      await avatar.scrollIntoViewIfNeeded();
      await expect(avatar).toHaveAttribute("src", "/copilot-pro-dev-samples/images/avatar-placeholder.svg");
      await expect(avatar).toHaveJSProperty("naturalWidth", 72);
      await expect(avatar).toHaveAttribute("width", String(size));
      await expect(avatar).toHaveAttribute("height", String(size));
      await expect(profile).toBeVisible();
    }
  });
}

test("available profile images are not replaced", async ({ page }) => {
  const pictureUrl = "https://github.com/ayronjohnson.png";
  await page.route(pictureUrl, (route) => route.fulfill({
    contentType: "image/svg+xml",
    body: '<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72"><circle cx="36" cy="36" r="36" fill="blue"/></svg>',
  }));
  await page.goto("contributors/");
  const avatar = page.locator(".contributor-card").filter({ hasText: "Ayron Johnson" }).locator("img");
  await avatar.scrollIntoViewIfNeeded();
  await expect(avatar).toHaveJSProperty("naturalWidth", 72);
  await expect(avatar).toHaveAttribute("src", pictureUrl);
});

test("profile images stop retrying if the placeholder also fails", async ({ page }) => {
  let placeholderRequests = 0;
  await page.route("**/images/avatar-placeholder.svg", (route) => {
    placeholderRequests++;
    return route.fulfill({ status: 404, contentType: "text/plain", body: "Not Found" });
  });
  await page.goto("contributors/");
  const avatar = page.locator(".contributor-card").filter({ hasText: "Ayron Johnson" }).locator("img");
  await avatar.scrollIntoViewIfNeeded();
  await expect(avatar).toHaveAttribute("src", "/copilot-pro-dev-samples/images/avatar-placeholder.svg");
  await expect.poll(() => avatar.evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth === 0)).toBe(true);
  await expect(avatar).toHaveJSProperty("onerror", null);
  const requestsAfterFailure = placeholderRequests;
  await avatar.dispatchEvent("error");
  expect(placeholderRequests).toBe(requestsAfterFailure);
});

test("What's new shows compact dated updates linking to sample details", async ({ page }) => {
  await page.goto("whats-new/");
  await expect(page.getByRole("heading", { name: "What's new", level: 1, exact: true })).toBeVisible();
  const updates = page.getByRole("region", { name: "Sample updates" });
  const rows = updates.locator(".updates-list > article");
  expect(await rows.count()).toBeGreaterThan(0);
  await expect(updates.locator("[data-sample-card], img")).toHaveCount(0);
  const first = rows.first();
  await expect(first.locator("time")).toHaveAttribute("datetime", /^\d{4}-\d{2}-\d{2}$/);
  await expect(first.locator(".eyebrow")).toHaveText(/^(Added|Updated)$/);
  const sampleLink = first.getByRole("heading", { level: 2 }).getByRole("link");
  const title = await sampleLink.innerText();
  await sampleLink.click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(title);
});

test("contribution resources highlight calls, demos, assets, and Sharing is Caring", async ({ page }) => {
  await page.goto("contributing/");
  const resources = page.getByRole("navigation", { name: "Community contribution resources" });
  const expectedLinks = [
    ["Join the community calls", "https://aka.ms/community/calls"],
    ["Request a demo slot", "https://aka.ms/community/request/demo"],
    ["Get started with Sharing is Caring", "https://pnp.github.io/sharing-is-caring/"],
    ["Screenshot and metadata guidance", "https://github.com/pnp/copilot-pro-dev-samples/blob/main/CONTRIBUTING.md#assets"],
  ];
  for (const [name, href] of expectedLinks) {
    const link = resources.getByRole("link", { name, exact: true });
    await link.scrollIntoViewIfNeeded();
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute("href", href);
  }
  const callout = page.getByRole("complementary", { name: "Contribute to the community" });
  await expect(callout.getByRole("link", { name: "Join community calls" })).toHaveAttribute("href", "https://aka.ms/community/calls");
});

test("top pages, sample detail, and both themes fit narrow and wide viewports", async ({ page }) => {
  const routes = ["./", "samples/", "getting-started/", "contributors/", "contributing/", "whats-new/", "samples/da-BlogPostHelper/"];
  for (const route of routes) {
    await page.goto(route);
    for (const theme of ["light", "dark"]) {
      if (await page.locator("html").getAttribute("data-theme") !== theme) await page.getByRole("switch").click();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      expect(overflow, `${route} overflows in ${theme} mode`).toBe(false);
    }
  }
});

test("the header fits at responsive breakpoints", async ({ page }) => {
  await page.goto("./");
  for (const width of [320, 360, 720, 768, 1024, 1201, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    const overflow = await page.locator(".site-header").evaluate((element) => element.scrollWidth > element.clientWidth);
    expect(overflow, `Header overflows at ${width}px`).toBe(false);
  }
});
