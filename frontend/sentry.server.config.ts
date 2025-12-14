// This file configures the initialization of Sentry on the server.
// The config you add here will be used whenever the server handles a request.
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

  // Environment
  environment: process.env.NODE_ENV,

  // Debug mode for development
  debug: process.env.NODE_ENV === "development",

  // Filter out common non-actionable errors
  ignoreErrors: [
    // Network errors
    "ECONNREFUSED",
    "ENOTFOUND",
    "ETIMEDOUT",
    // User cancelled actions
    "AbortError",
    "The operation was aborted",
  ],

  // Before sending, filter sensitive data
  beforeSend(event) {
    // Don't send events without DSN
    if (!process.env.NEXT_PUBLIC_SENTRY_DSN) {
      return null;
    }

    // Scrub sensitive headers
    if (event.request?.headers) {
      const sensitiveHeaders = [
        "authorization",
        "cookie",
        "x-api-key",
        "x-auth-token",
      ];
      for (const header of sensitiveHeaders) {
        if (event.request.headers[header]) {
          event.request.headers[header] = "[REDACTED]";
        }
      }
    }

    return event;
  },
});
