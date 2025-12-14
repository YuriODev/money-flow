import { test, expect } from "@playwright/test";

/**
 * Authentication E2E Tests
 *
 * NOTE: These tests are currently skipped because the frontend login UI
 * has not been implemented yet. The backend auth (JWT, etc.) is complete,
 * but the frontend pages (/login, /register) need to be built.
 *
 * TODO: Unskip these tests once Sprint 2.x implements the auth UI.
 */

test.describe("Authentication Flow", () => {
  // Skip all auth tests until login UI is implemented
  test.skip(true, "Auth UI not implemented yet - see Sprint 2.x");

  test.use({ storageState: { cookies: [], origins: [] } });

  test("should show login page for unauthenticated users", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(
      page.getByRole("button", { name: /sign in|log in|login/i })
    ).toBeVisible();
  });

  test("should show validation errors for empty form", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: /sign in|log in|login/i }).click();
    await expect(page.getByText(/email.*required|enter.*email/i)).toBeVisible();
  });

  test("should show error for invalid credentials", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("invalid@example.com");
    await page.getByLabel(/password/i).fill("wrongpassword");
    await page.getByRole("button", { name: /sign in|log in|login/i }).click();
    await expect(
      page.getByText(/invalid.*credentials|incorrect.*password|login failed/i)
    ).toBeVisible({ timeout: 10000 });
  });

  test("should successfully login with valid credentials", async ({ page }) => {
    const testEmail = process.env.E2E_TEST_EMAIL || "test@example.com";
    const testPassword = process.env.E2E_TEST_PASSWORD || "TestPassword123!";

    await page.goto("/login");
    await page.getByLabel(/email/i).fill(testEmail);
    await page.getByLabel(/password/i).fill(testPassword);
    await page.getByRole("button", { name: /sign in|log in|login/i }).click();
    await expect(page).toHaveURL("/", { timeout: 15000 });
    await expect(
      page.getByRole("heading", {
        name: /money flow|subscriptions|dashboard/i,
      })
    ).toBeVisible({ timeout: 10000 });
  });

  test("should persist authentication across page refreshes", async ({
    page,
  }) => {
    const testEmail = process.env.E2E_TEST_EMAIL || "test@example.com";
    const testPassword = process.env.E2E_TEST_PASSWORD || "TestPassword123!";

    await page.goto("/login");
    await page.getByLabel(/email/i).fill(testEmail);
    await page.getByLabel(/password/i).fill(testPassword);
    await page.getByRole("button", { name: /sign in|log in|login/i }).click();
    await expect(page).toHaveURL("/", { timeout: 15000 });

    await page.reload();
    await expect(page).toHaveURL("/");
    await expect(
      page.getByRole("heading", {
        name: /money flow|subscriptions|dashboard/i,
      })
    ).toBeVisible({ timeout: 10000 });
  });

  test("should logout successfully", async ({ page }) => {
    const testEmail = process.env.E2E_TEST_EMAIL || "test@example.com";
    const testPassword = process.env.E2E_TEST_PASSWORD || "TestPassword123!";

    await page.goto("/login");
    await page.getByLabel(/email/i).fill(testEmail);
    await page.getByLabel(/password/i).fill(testPassword);
    await page.getByRole("button", { name: /sign in|log in|login/i }).click();
    await expect(page).toHaveURL("/", { timeout: 15000 });

    const logoutButton = page.getByRole("button", { name: /logout|sign out/i });
    if (await logoutButton.isVisible()) {
      await logoutButton.click();
    } else {
      const userMenu = page.getByRole("button", { name: /menu|profile|user/i });
      if (await userMenu.isVisible()) {
        await userMenu.click();
        await page
          .getByRole("menuitem", { name: /logout|sign out/i })
          .click();
      }
    }
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
  });
});

test.describe("Registration Flow", () => {
  // Skip all registration tests until register UI is implemented
  test.skip(true, "Auth UI not implemented yet - see Sprint 2.x");

  test.use({ storageState: { cookies: [], origins: [] } });

  test("should show registration form", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i).first()).toBeVisible();
    await expect(
      page.getByRole("button", { name: /sign up|register|create account/i })
    ).toBeVisible();
  });

  test("should navigate between login and register", async ({ page }) => {
    await page.goto("/login");
    await page
      .getByRole("link", { name: /sign up|register|create account/i })
      .click();
    await expect(page).toHaveURL(/\/register/);
    await page.getByRole("link", { name: /sign in|log in|login/i }).click();
    await expect(page).toHaveURL(/\/login/);
  });

  test("should show validation errors for weak password", async ({ page }) => {
    await page.goto("/register");
    await page.getByLabel(/email/i).fill("newuser@example.com");
    await page.getByLabel(/password/i).first().fill("weak");
    await page
      .getByRole("button", { name: /sign up|register|create account/i })
      .click();
    await expect(
      page.getByText(/password.*must|at least.*characters|stronger.*password/i)
    ).toBeVisible();
  });
});

test.describe("Protected Routes", () => {
  // Skip protected route tests until auth is implemented in frontend
  test.skip(true, "Auth UI not implemented yet - see Sprint 2.x");

  test.use({ storageState: { cookies: [], origins: [] } });

  test("should redirect unauthenticated users from dashboard to login", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/login/);
  });

  test("should redirect unauthenticated users from settings to login", async ({
    page,
  }) => {
    await page.goto("/settings");
    await expect(page).toHaveURL(/\/login/);
  });
});
