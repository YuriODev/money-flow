"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Wallet, Sparkles, Download, User, LogOut, ChevronDown, Sun, Moon, Settings } from "lucide-react";
import { CurrencySelector } from "./CurrencySelector";
import ImportExportModal from "./ImportExportModal";
import { useAuth } from "@/lib/auth-context";
import { useTheme } from "@/lib/theme-context";

export function Header() {
  const router = useRouter();
  const [isImportExportOpen, setIsImportExportOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const { user, logout, isAuthenticated } = useAuth();
  const { theme, toggleTheme } = useTheme();

  // Close user menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = async () => {
    setIsUserMenuOpen(false);
    await logout();
  };

  const handleSettingsClick = () => {
    setIsUserMenuOpen(false);
    router.push("/settings");
  };

  return (
    <header className="relative z-20" role="banner">
      <div className="glass-card border-b border-white/20">
        <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4 max-w-7xl">
          <div className="flex items-center justify-between gap-2">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="flex items-center gap-2 sm:gap-4 min-w-0"
            >
              <motion.div
                whileHover={{ scale: 1.05, rotate: 5 }}
                whileTap={{ scale: 0.95 }}
                className="relative shrink-0"
              >
                {/* Glow effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl blur-lg opacity-50" />

                {/* Icon container */}
                <div className="relative w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                  <Wallet className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                </div>
              </motion.div>

              <div className="min-w-0">
                <motion.h1
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="text-xl sm:text-2xl font-bold"
                >
                  <span className="text-gradient">Money Flow</span>
                </motion.h1>
                <motion.p
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15 }}
                  className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 flex items-center gap-1 truncate"
                >
                  <span className="hidden xs:inline">Track all your recurring payments</span>
                  <span className="xs:hidden">Recurring payments</span>
                  <span className="hidden sm:inline-flex items-center gap-1 ml-1 px-2 py-0.5 rounded-full bg-gradient-to-r from-purple-100 to-indigo-100 dark:from-purple-900/40 dark:to-indigo-900/40 text-purple-700 dark:text-purple-300 text-xs font-medium">
                    <Sparkles className="w-3 h-3" />
                    AI Powered
                  </span>
                </motion.p>
              </div>
            </motion.div>

            {/* Right side: Import/Export, Currency selector and date */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="flex items-center gap-1.5 sm:gap-3"
            >
              {/* Import/Export Button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsImportExportOpen(true)}
                className="flex items-center gap-2 px-2 sm:px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium transition-colors"
                title="Import / Export"
                aria-label="Import or export data"
              >
                <Download className="w-4 h-4" />
                <span className="hidden sm:inline">Import/Export</span>
              </motion.button>

              <CurrencySelector />

              {/* Theme Toggle */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={toggleTheme}
                className="flex items-center justify-center w-9 h-9 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors"
                aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
                title={theme === "dark" ? "Dark mode" : "Light mode"}
              >
                {theme === "dark" ? (
                  <Sun className="w-4 h-4" />
                ) : (
                  <Moon className="w-4 h-4" />
                )}
              </motion.button>

              <div className="hidden lg:flex items-center gap-3">
                <div className="h-8 w-px bg-gray-200 dark:bg-gray-700" />
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {new Date().toLocaleDateString("en-GB", {
                    weekday: "long",
                    day: "numeric",
                    month: "long",
                  })}
                </p>
              </div>

              {/* User Menu */}
              {isAuthenticated && user && (
                <>
                  <div className="hidden sm:block h-8 w-px bg-gray-200 dark:bg-gray-700" />
                  <div ref={userMenuRef} className="relative">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                      className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium transition-colors"
                      aria-expanded={isUserMenuOpen}
                      aria-haspopup="true"
                      aria-label="User menu"
                    >
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                        <User className="w-4 h-4 text-white" />
                      </div>
                      <span className="hidden md:inline max-w-[120px] truncate">
                        {user.full_name || user.email.split("@")[0]}
                      </span>
                      <ChevronDown className={`w-4 h-4 transition-transform hidden sm:block ${isUserMenuOpen ? "rotate-180" : ""}`} />
                    </motion.button>

                    {/* Dropdown Menu */}
                    <AnimatePresence>
                      {isUserMenuOpen && (
                        <motion.div
                          initial={{ opacity: 0, y: -10, scale: 0.95 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          exit={{ opacity: 0, y: -10, scale: 0.95 }}
                          transition={{ duration: 0.15 }}
                          className="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 py-2 z-50"
                        >
                          {/* User Info */}
                          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                              {user.full_name || "User"}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{user.email}</p>
                          </div>

                          {/* Menu Items */}
                          <div className="py-1">
                            <button
                              onClick={handleSettingsClick}
                              className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                            >
                              <Settings className="w-4 h-4" />
                              Settings
                            </button>
                            <button
                              onClick={handleLogout}
                              className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                            >
                              <LogOut className="w-4 h-4" />
                              Sign out
                            </button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </>
              )}
            </motion.div>
          </div>
        </div>
      </div>

      {/* Import/Export Modal */}
      <ImportExportModal
        isOpen={isImportExportOpen}
        onClose={() => setIsImportExportOpen(false)}
      />
    </header>
  );
}
