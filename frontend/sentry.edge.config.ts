// This file configures the initialization of Sentry for edge features (middleware, edge routes, etc).
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,

  // Only enable in production or when explicitly set
  enabled:
    process.env.NODE_ENV === "production" ||
    !!process.env.NEXT_PUBLIC_SENTRY_DSN,

  // Performance Monitoring - lower sample rate for edge
  tracesSampleRate: process.env.NODE_ENV === "production" ? 0.05 : 0.5,

  // Environment
  environment: process.env.NODE_ENV,

  // Debug mode for development
  debug: process.env.NODE_ENV === "development",
});
