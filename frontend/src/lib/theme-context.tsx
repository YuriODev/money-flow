"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";

// ThemePreference is what the user chooses (can include "system")
type ThemePreference = "light" | "dark" | "system";
// ResolvedTheme is the actual theme applied (only light or dark)
type ResolvedTheme = "light" | "dark";

interface ThemeContextType {
  theme: ResolvedTheme; // The actual applied theme
  themePreference: ThemePreference; // What the user selected
  setTheme: (theme: ResolvedTheme | ThemePreference) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const STORAGE_KEY = "money-flow-theme";

// Helper to get system preference
const getSystemTheme = (): ResolvedTheme => {
  if (typeof window !== "undefined" && window.matchMedia) {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  return "light";
};

// Helper to resolve theme preference to actual theme
const resolveTheme = (preference: ThemePreference): ResolvedTheme => {
  if (preference === "system") {
    return getSystemTheme();
  }
  return preference;
};

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // Track both the preference and the resolved theme
  const [themePreference, setThemePreference] = useState<ThemePreference>("light");
  const [theme, setThemeState] = useState<ResolvedTheme>("light");
  const [mounted, setMounted] = useState(false);

  // Initialize theme from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as ThemePreference | null;
    if (stored === "light" || stored === "dark" || stored === "system") {
      setThemePreference(stored);
      const resolved = resolveTheme(stored);
      setThemeState(resolved);
      applyTheme(resolved);
    } else {
      // No stored preference - default to system
      setThemePreference("system");
      const resolved = getSystemTheme();
      setThemeState(resolved);
      applyTheme(resolved);
    }
    setMounted(true);
  }, []);

  // Listen for system preference changes when using "system" theme
  useEffect(() => {
    if (!mounted || themePreference !== "system") return;

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const handleChange = (e: MediaQueryListEvent) => {
      const newTheme = e.matches ? "dark" : "light";
      setThemeState(newTheme);
      applyTheme(newTheme);
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [mounted, themePreference]);

  // Apply theme to document
  const applyTheme = (newTheme: ResolvedTheme) => {
    if (newTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  // Update DOM when theme changes
  useEffect(() => {
    if (mounted) {
      applyTheme(theme);
    }
  }, [theme, mounted]);

  const setTheme = useCallback((newTheme: ResolvedTheme | ThemePreference) => {
    // Store the preference
    setThemePreference(newTheme as ThemePreference);
    localStorage.setItem(STORAGE_KEY, newTheme);

    // Resolve and apply the actual theme
    const resolved = resolveTheme(newTheme as ThemePreference);
    setThemeState(resolved);
    applyTheme(resolved);
  }, []);

  const toggleTheme = useCallback(() => {
    // Toggle between light and dark (not system)
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
  }, [theme, setTheme]);

  // Prevent hydration mismatch
  if (!mounted) {
    return (
      <ThemeContext.Provider
        value={{
          theme: "light",
          themePreference: "system",
          setTheme: () => {},
          toggleTheme: () => {},
        }}
      >
        {children}
      </ThemeContext.Provider>
    );
  }

  return (
    <ThemeContext.Provider value={{ theme, themePreference, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
