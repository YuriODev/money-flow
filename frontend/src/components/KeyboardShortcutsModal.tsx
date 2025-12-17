"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Keyboard, Command } from "lucide-react";
import { SHORTCUTS, getShortcutDisplay } from "@/hooks/useKeyboardShortcuts";

interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const shortcutCategories = [
  {
    title: "Navigation",
    shortcuts: [
      { ...SHORTCUTS.VIEW_LIST, key: "1", ctrl: true },
      { ...SHORTCUTS.VIEW_CALENDAR, key: "2", ctrl: true },
      { ...SHORTCUTS.VIEW_CARDS, key: "3", ctrl: true },
      { ...SHORTCUTS.VIEW_AGENT, key: "4", ctrl: true },
    ],
  },
  {
    title: "Actions",
    shortcuts: [
      { ...SHORTCUTS.ADD_PAYMENT, key: "n", ctrl: true },
      { ...SHORTCUTS.SEARCH, key: "k", ctrl: true },
      { ...SHORTCUTS.TOGGLE_THEME, key: "d", ctrl: true },
    ],
  },
  {
    title: "Help",
    shortcuts: [{ ...SHORTCUTS.HELP, key: "?", shift: true }],
  },
];

export function KeyboardShortcutsModal({
  isOpen,
  onClose,
}: KeyboardShortcutsModalProps) {
  const [isMac, setIsMac] = useState(false);

  useEffect(() => {
    setIsMac(navigator.platform.toUpperCase().indexOf("MAC") >= 0);
  }, []);

  // Close on Escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            aria-hidden="true"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md"
            role="dialog"
            aria-modal="true"
            aria-labelledby="shortcuts-title"
          >
            <div className="glass-card rounded-2xl p-6 shadow-2xl mx-4">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-500">
                    <Keyboard className="w-5 h-5 text-white" />
                  </div>
                  <h2
                    id="shortcuts-title"
                    className="text-lg font-semibold text-gray-900 dark:text-white"
                  >
                    Keyboard Shortcuts
                  </h2>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  aria-label="Close keyboard shortcuts"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              {/* Shortcut Categories */}
              <div className="space-y-6">
                {shortcutCategories.map((category) => (
                  <div key={category.title}>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-3">
                      {category.title}
                    </h3>
                    <div className="space-y-2">
                      {category.shortcuts.map((shortcut) => (
                        <div
                          key={shortcut.description}
                          className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                        >
                          <span className="text-sm text-gray-700 dark:text-gray-300">
                            {shortcut.description}
                          </span>
                          <ShortcutKeys shortcut={shortcut} isMac={isMac} />
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Footer hint */}
              <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-xs text-gray-500 dark:text-gray-400 text-center flex items-center justify-center gap-1">
                  Press{" "}
                  <kbd className="px-1.5 py-0.5 text-xs font-medium bg-gray-100 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                    Esc
                  </kbd>{" "}
                  to close
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

interface ShortcutKeysProps {
  shortcut: { key: string; ctrl?: boolean; shift?: boolean; alt?: boolean };
  isMac: boolean;
}

function ShortcutKeys({ shortcut, isMac }: ShortcutKeysProps) {
  const keys: string[] = [];

  if (shortcut.ctrl) {
    keys.push(isMac ? "⌘" : "Ctrl");
  }
  if (shortcut.shift) {
    keys.push(isMac ? "⇧" : "Shift");
  }
  if (shortcut.alt) {
    keys.push(isMac ? "⌥" : "Alt");
  }
  keys.push(shortcut.key.length === 1 ? shortcut.key.toUpperCase() : shortcut.key);

  return (
    <div className="flex items-center gap-1">
      {keys.map((key, index) => (
        <kbd
          key={index}
          className="min-w-[24px] h-6 px-1.5 flex items-center justify-center text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 rounded border border-gray-200 dark:border-gray-700"
        >
          {key}
        </kbd>
      ))}
    </div>
  );
}
