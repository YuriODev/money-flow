import { test as setup } from "@playwright/test";
import path from "path";

const authFile = path.join(__dirname, ".auth/user.json");

/**
 * Authentication setup that runs before all tests.
 *
 * NOTE: Currently the frontend does not have a login page implemented.
 * This setup creates an empty auth state so tests can run.
 * Once the login UI is implemented (Sprint 2.x), this should be updated
 * to perform actual authentication.
 */
setup("authenticate", async ({ page }) => {
  // TODO: Implement actual login when frontend auth UI is ready
  // For now, we create an empty storage state since the app doesn't require auth yet

  // Navigate to the app to establish cookies/storage
  await page.goto("/");

  // Wait for the page to load
  await page.waitForLoadState("networkidle");

  // Save the current state (empty auth for now)
  await page.context().storageState({ path: authFile });
});

/**
 * Future implementation when login page exists:
 *
 * setup("authenticate", async ({ page }) => {
 *   const testEmail = process.env.E2E_TEST_EMAIL || "test@example.com";
 *   const testPassword = process.env.E2E_TEST_PASSWORD || "TestPassword123!";
 *
 *   await page.goto("/login");
 *   await page.getByLabel(/email/i).fill(testEmail);
 *   await page.getByLabel(/password/i).fill(testPassword);
 *   await page.getByRole("button", { name: /sign in|log in|login/i }).click();
 *   await expect(page).toHaveURL("/", { timeout: 15000 });
 *
 *   await page.context().storageState({ path: authFile });
 * });
 */
