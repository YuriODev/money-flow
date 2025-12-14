// This file configures the initialization of Sentry on the client.
// The config you add here will be used whenever a users loads a page in their browser.
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,

  // Only enable in production or when explicitly set
  enabled:
    process.env.NODE_ENV === "production" ||
    !!process.env.NEXT_PUBLIC_SENTRY_DSN,

  // Performance Monitoring
  tracesSampleRate: process.env.NODE_ENV === "production" ? 0.1 : 1.0,

  // Session Replay - only in production
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,

  // Environment
  environment: process.env.NODE_ENV,

  // Debug mode for development
  debug: process.env.NODE_ENV === "development",

  // Filter out common non-actionable errors
  ignoreErrors: [
    // Network errors that users can't control
    "Failed to fetch",
    "NetworkError",
    "Network request failed",
    "Load failed",
    // Browser extension errors
    "chrome-extension://",
    "moz-extension://",
    // User cancelled actions
    "AbortError",
    "The operation was aborted",
    // React hydration warnings (usually not actionable)
    "Hydration failed",
    "Text content does not match",
  ],

  // Before sending, filter sensitive data
  beforeSend(event) {
    // Don't send events in development without DSN
    if (!process.env.NEXT_PUBLIC_SENTRY_DSN) {
      return null;
    }

    // Filter out PII from breadcrumbs
    if (event.breadcrumbs) {
      event.breadcrumbs = event.breadcrumbs.map((breadcrumb) => {
        if (breadcrumb.data?.url) {
          // Remove auth tokens from URLs
          breadcrumb.data.url = breadcrumb.data.url.replace(
            /token=[^&]+/g,
            "token=[REDACTED]"
          );
        }
        return breadcrumb;
      });
    }

    return event;
  },

  // Integrations
  integrations: [
    Sentry.replayIntegration({
      // Mask all text content by default
      maskAllText: true,
      // Block all media (images, videos)
      blockAllMedia: true,
    }),
  ],
});
