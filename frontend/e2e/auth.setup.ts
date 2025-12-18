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

  // Fill in login form (labels are "Email address" and "Password")
  await page.getByLabel("Email address").fill(testEmail);
  await page.getByLabel("Password").fill(testPassword);

  // Click login button (button text is "Sign in")
  await page.getByRole("button", { name: "Sign in" }).click();

  // Wait for redirect to dashboard
  await expect(page).toHaveURL("/", { timeout: 15000 });

  // Verify we're logged in by checking for dashboard content
  await expect(page.getByText(/Money Flow/i).first()).toBeVisible({
    timeout: 10000,
  });

  // Save the authenticated state
  await page.context().storageState({ path: authFile });
});
