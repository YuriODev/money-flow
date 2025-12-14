import { test as base, expect } from "@playwright/test";

/**
 * Extended test fixtures for Money Flow E2E tests.
 * Provides common utilities and page object helpers.
 */

// Extended test fixture - basic version for UI testing
// API fixtures are available but not required for basic UI tests
export const test = base;

export { expect } from "@playwright/test";
