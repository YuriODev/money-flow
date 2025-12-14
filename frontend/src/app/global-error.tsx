"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

interface GlobalErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    // Log error to Sentry
    Sentry.captureException(error);
  }, [error]);

  return (
    <html>
      <body>
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "linear-gradient(to bottom right, #111827, #1f2937)",
            fontFamily: "system-ui, -apple-system, sans-serif",
          }}
        >
          <div
            style={{
              padding: "2rem",
              maxWidth: "28rem",
              width: "100%",
              textAlign: "center",
              background: "rgba(255, 255, 255, 0.1)",
              backdropFilter: "blur(10px)",
              borderRadius: "1rem",
              border: "1px solid rgba(255, 255, 255, 0.2)",
            }}
          >
            <div style={{ fontSize: "4rem", marginBottom: "1rem" }}>💥</div>
            <h2
              style={{
                fontSize: "1.5rem",
                fontWeight: "bold",
                color: "white",
                marginBottom: "1rem",
              }}
            >
              Critical Error
            </h2>
            <p
              style={{
                color: "#9ca3af",
                marginBottom: "1.5rem",
              }}
            >
              A critical error occurred. Our team has been notified and is
              working on a fix.
            </p>
            {error.digest && (
              <p
                style={{
                  fontSize: "0.75rem",
                  color: "#6b7280",
                  marginBottom: "1rem",
                }}
              >
                Error ID: {error.digest}
              </p>
            )}
            <button
              onClick={reset}
              style={{
                padding: "0.75rem 1.5rem",
                background: "linear-gradient(to right, #3b82f6, #8b5cf6)",
                color: "white",
                borderRadius: "0.5rem",
                fontWeight: "500",
                border: "none",
                cursor: "pointer",
              }}
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
