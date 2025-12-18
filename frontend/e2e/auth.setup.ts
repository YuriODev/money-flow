import { test as setup, expect } from "@playwright/test";

const authFile = "e2e/.auth/user.json";

/**
 * Authentication setup that runs before all tests.
 *
 * Logs in with test credentials and saves the auth state
 * so subsequent tests can reuse the authenticated session.
 */
setup("authenticate", async ({ page }) => {
  const testEmail = process.env.E2E_TEST_EMAIL || "test@example.com";
  const testPassword = process.env.E2E_TEST_PASSWORD || "TestPassword123!";

  // Navigate to login page
  await page.goto("/login");
  await page.waitForLoadState("networkidle");

  // Fill in login form
  await page.getByLabel(/email/i).fill(testEmail);
  await page.getByLabel(/password/i).fill(testPassword);

  // Click login button
  await page.getByRole("button", { name: /sign in|log in|login/i }).click();

  // Wait for redirect to dashboard
  await expect(page).toHaveURL("/", { timeout: 15000 });

  // Verify we're logged in by checking for dashboard content
  await expect(page.getByText(/Money Flow/i).first()).toBeVisible({
    timeout: 10000,
  });

  // Save the authenticated state
  await page.context().storageState({ path: authFile });
});
