"use client";

import { useEffect, useCallback } from "react";

interface ShortcutConfig {
  key: string;
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  alt?: boolean;
  callback: () => void;
  description: string;
  enabled?: boolean;
}

interface UseKeyboardShortcutsOptions {
  shortcuts: ShortcutConfig[];
  enabled?: boolean;
}

/**
 * Custom hook for handling keyboard shortcuts
 * Supports modifier keys (Ctrl, Meta/Cmd, Shift, Alt)
 */
export function useKeyboardShortcuts({
  shortcuts,
  enabled = true,
}: UseKeyboardShortcutsOptions) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      const target = event.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable
      ) {
        return;
      }

      for (const shortcut of shortcuts) {
        if (shortcut.enabled === false) continue;

        const keyMatches = event.key.toLowerCase() === shortcut.key.toLowerCase();
        const ctrlMatches = shortcut.ctrl ? event.ctrlKey || event.metaKey : !event.ctrlKey && !event.metaKey;
        const shiftMatches = shortcut.shift ? event.shiftKey : !event.shiftKey;
        const altMatches = shortcut.alt ? event.altKey : !event.altKey;

        // For meta specifically (Cmd on Mac)
        const metaMatches = shortcut.meta ? event.metaKey : true;

        if (keyMatches && ctrlMatches && shiftMatches && altMatches && metaMatches) {
          event.preventDefault();
          shortcut.callback();
          return;
        }
      }
    },
    [shortcuts]
  );

  useEffect(() => {
    if (!enabled) return;

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [enabled, handleKeyDown]);
}

/**
 * Get keyboard shortcut display string
 * Returns platform-appropriate modifier keys (⌘ on Mac, Ctrl on others)
 */
export function getShortcutDisplay(shortcut: ShortcutConfig): string {
  const isMac = typeof window !== "undefined" && navigator.platform.toUpperCase().indexOf("MAC") >= 0;
  const parts: string[] = [];

  if (shortcut.ctrl || shortcut.meta) {
    parts.push(isMac ? "⌘" : "Ctrl");
  }
  if (shortcut.shift) {
    parts.push(isMac ? "⇧" : "Shift");
  }
  if (shortcut.alt) {
    parts.push(isMac ? "⌥" : "Alt");
  }

  // Capitalize single character keys
  const key = shortcut.key.length === 1 ? shortcut.key.toUpperCase() : shortcut.key;
  parts.push(key);

  return parts.join(isMac ? "" : "+");
}

/**
 * Common shortcut definitions
 */
export const SHORTCUTS = {
  ADD_PAYMENT: { key: "n", ctrl: true, description: "Add new payment" },
  SEARCH: { key: "k", ctrl: true, description: "Search" },
  VIEW_LIST: { key: "1", ctrl: true, description: "View payments list" },
  VIEW_CALENDAR: { key: "2", ctrl: true, description: "View calendar" },
  VIEW_CARDS: { key: "3", ctrl: true, description: "View cards" },
  VIEW_AGENT: { key: "4", ctrl: true, description: "Open AI assistant" },
  TOGGLE_THEME: { key: "d", ctrl: true, description: "Toggle dark mode" },
  HELP: { key: "?", shift: true, description: "Show keyboard shortcuts" },
} as const;
