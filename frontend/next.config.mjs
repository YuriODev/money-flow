import { withSentryConfig } from "@sentry/nextjs";

// Get backend URL at build time - for standalone mode this is baked in
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000';

console.log(`[next.config.mjs] BACKEND_URL: ${BACKEND_URL}`);

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,

  async rewrites() {
    // Rewrites are evaluated at build time in standalone mode
    // The destination must be a full URL, not just the base
    return [
      {
        source: '/api/:path*',
        destination: `${BACKEND_URL}/api/:path*`,
      },
    ];
  },

  // Environment variables to expose to the browser
  env: {
    API_VERSION: 'v1',
  },
};

// Sentry configuration options
const sentryWebpackPluginOptions = {
  // Organization and project from Sentry dashboard
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,

  // Auth token for uploading source maps
  authToken: process.env.SENTRY_AUTH_TOKEN,

  // Suppresses source map uploading logs during build
  silent: !process.env.CI,

  // Upload source maps only in production
  disableServerWebpackPlugin: process.env.NODE_ENV !== "production",
  disableClientWebpackPlugin: process.env.NODE_ENV !== "production",

  // Routes browser requests to Sentry through a Next.js rewrite
  tunnelRoute: "/monitoring",

  // Hides source maps from generated client bundles
  hideSourceMaps: true,

  // Automatically tree-shake Sentry logger statements
  disableLogger: true,

  // Enables automatic instrumentation of Vercel Cron Monitors
  automaticVercelMonitors: false,
};

// Only wrap with Sentry if DSN is configured
const config = process.env.NEXT_PUBLIC_SENTRY_DSN
  ? withSentryConfig(nextConfig, sentryWebpackPluginOptions)
  : nextConfig;

export default config;
