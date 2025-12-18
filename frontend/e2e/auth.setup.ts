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

  console.log(`Attempting login with email: ${testEmail}`);

  // Navigate to login page
  await page.goto("/login");
  await page.waitForLoadState("networkidle");

  // Fill in login form (labels are "Email address" and "Password")
  await page.getByLabel("Email address").fill(testEmail);
  await page.getByLabel("Password").fill(testPassword);

  // Listen for any API response to debug
  page.on("response", (response) => {
    if (response.url().includes("/api/")) {
      console.log(`API Response: ${response.url()} - ${response.status()}`);
    }
  });

  // Click login button
  await page.getByRole("button", { name: "Sign in" }).click();

  // Wait for navigation or error message
  try {
    await expect(page).toHaveURL("/", { timeout: 15000 });
  } catch {
    // Check if there's an error message on the page
    const errorMessage = await page
      .locator('[class*="error"], [class*="red"], [role="alert"]')
      .first()
      .textContent()
      .catch(() => null);
    if (errorMessage) {
      console.error(`Login error message: ${errorMessage}`);
    }

    // Take a screenshot for debugging
    await page.screenshot({ path: "e2e/test-results/login-failure.png" });

    // Re-throw to fail the test with more context
    throw new Error(
      `Login failed. Error message: ${errorMessage || "Unknown error"}. Check login-failure.png for details.`
    );
  }

  // Verify we're logged in by checking for dashboard content
  await expect(page.getByText(/Money Flow/i).first()).toBeVisible({
    timeout: 10000,
  });

  // Save the authenticated state
  await page.context().storageState({ path: authFile });
  console.log("Authentication successful, state saved.");
});
