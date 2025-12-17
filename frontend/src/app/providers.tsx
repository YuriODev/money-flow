"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { CurrencyProvider } from "@/lib/currency-context";
import { AuthProvider } from "@/lib/auth-context";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ToastProvider } from "@/components/Toast";
import { ThemeProvider } from "@/lib/theme-context";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <ProtectedRoute>
            <CurrencyProvider>
              <ErrorBoundary>{children}</ErrorBoundary>
              <ToastProvider />
            </CurrencyProvider>
          </ProtectedRoute>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
