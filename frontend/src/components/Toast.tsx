"use client";

import { Toaster, toast as sonnerToast } from "sonner";
import { CheckCircle2, XCircle, AlertCircle, Info, Loader2 } from "lucide-react";
import { useTheme } from "@/lib/theme-context";

// Custom toast functions with consistent styling
export const toast = {
  success: (message: string, description?: string) => {
    sonnerToast.success(message, {
      description,
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-500" />,
    });
  },
  error: (message: string, description?: string) => {
    sonnerToast.error(message, {
      description,
      icon: <XCircle className="w-5 h-5 text-red-500" />,
    });
  },
  warning: (message: string, description?: string) => {
    sonnerToast.warning(message, {
      description,
      icon: <AlertCircle className="w-5 h-5 text-amber-500" />,
    });
  },
  info: (message: string, description?: string) => {
    sonnerToast.info(message, {
      description,
      icon: <Info className="w-5 h-5 text-blue-500" />,
    });
  },
  loading: (message: string) => {
    return sonnerToast.loading(message, {
      icon: <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />,
    });
  },
  dismiss: (toastId?: string | number) => {
    sonnerToast.dismiss(toastId);
  },
  promise: <T,>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: Error) => string);
    }
  ) => {
    return sonnerToast.promise(promise, {
      loading: messages.loading,
      success: messages.success,
      error: messages.error,
    });
  },
};

// Toaster component to be added to the app layout
export function ToastProvider() {
  const { theme } = useTheme();

  return (
    <Toaster
      position="bottom-right"
      expand={false}
      richColors
      closeButton
      theme={theme}
      toastOptions={{
        duration: 4000,
        className: theme === "dark"
          ? "!bg-gray-800 !border !border-gray-700 !shadow-lg !rounded-xl !text-gray-100"
          : "!bg-white !border !border-gray-100 !shadow-lg !rounded-xl",
        style: {
          padding: "16px",
        },
      }}
    />
  );
}
