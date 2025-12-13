"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Wallet, Sparkles, Download } from "lucide-react";
import { CurrencySelector } from "./CurrencySelector";
import ImportExportModal from "./ImportExportModal";

export function Header() {
  const [isImportExportOpen, setIsImportExportOpen] = useState(false);
  return (
    <header className="relative z-20">
      <div className="glass-card border-b border-white/20">
        <div className="container mx-auto px-4 py-4 max-w-7xl">
          <div className="flex items-center justify-between">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="flex items-center gap-4"
            >
              <motion.div
                whileHover={{ scale: 1.05, rotate: 5 }}
                whileTap={{ scale: 0.95 }}
                className="relative"
              >
                {/* Glow effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl blur-lg opacity-50" />

                {/* Icon container */}
                <div className="relative w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                  <Wallet className="w-6 h-6 text-white" />
                </div>
              </motion.div>

              <div>
                <motion.h1
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="text-2xl font-bold"
                >
                  <span className="text-gradient">Money Flow</span>
                </motion.h1>
                <motion.p
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.15 }}
                  className="text-sm text-gray-500 flex items-center gap-1"
                >
                  Track all your recurring payments
                  <span className="inline-flex items-center gap-1 ml-1 px-2 py-0.5 rounded-full bg-gradient-to-r from-purple-100 to-indigo-100 text-purple-700 text-xs font-medium">
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
              className="flex items-center gap-3"
            >
              {/* Import/Export Button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsImportExportOpen(true)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium transition-colors"
                title="Import / Export"
              >
                <Download className="w-4 h-4" />
                <span className="hidden sm:inline">Import/Export</span>
              </motion.button>

              <CurrencySelector />
              <div className="hidden md:flex items-center gap-3">
                <div className="h-8 w-px bg-gray-200" />
                <p className="text-sm text-gray-500">
                  {new Date().toLocaleDateString("en-GB", {
                    weekday: "long",
                    day: "numeric",
                    month: "long",
                  })}
                </p>
              </div>
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
