import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/browser",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 2,
  use: {
    baseURL: "http://127.0.0.1:4330/copilot-pro-dev-samples/",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 1000 } } },
    { name: "mobile", use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" } },
  ],
  webServer: {
    command: "npm run preview -- --base /copilot-pro-dev-samples --host 127.0.0.1 --port 4330",
    url: "http://127.0.0.1:4330/copilot-pro-dev-samples/",
    reuseExistingServer: false,
  },
});
