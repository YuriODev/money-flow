"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Check } from "lucide-react";
import { useCurrency, CURRENCIES, type Currency } from "@/lib/currency-context";
import { cn } from "@/lib/utils";

export function CurrencySelector() {
  const { currency, setCurrency, currencyInfo } = useCurrency();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (code: Currency) => {
    setCurrency(code);
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className="relative">
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className={cn(
          "flex items-center gap-2 px-3 py-2 rounded-xl transition-all duration-200",
          "glass-card-subtle hover:shadow-md",
          isOpen && "ring-2 ring-blue-200"
        )}
      >
        <span className="text-lg">{currencyInfo.flag}</span>
        <span className="font-semibold text-gray-700">{currencyInfo.symbol}</span>
        <span className="text-sm text-gray-500 hidden sm:inline">{currency}</span>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown className="w-4 h-4 text-gray-400" />
        </motion.div>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-full mt-2 z-50 w-56 glass-card rounded-2xl shadow-xl p-2 overflow-hidden"
          >
            <p className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wide">
              Display Currency
            </p>
            {CURRENCIES.map((c) => (
              <motion.button
                key={c.code}
                onClick={() => handleSelect(c.code)}
                whileHover={{ x: 4 }}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200",
                  currency === c.code
                    ? "bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700"
                    : "hover:bg-gray-50 text-gray-700"
                )}
              >
                <span className="text-xl">{c.flag}</span>
                <div className="flex-1 text-left">
                  <p className="font-medium">{c.symbol} {c.code}</p>
                  <p className="text-xs text-gray-500">{c.name}</p>
                </div>
                {currency === c.code && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-5 h-5 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-center"
                  >
                    <Check className="w-3 h-3 text-white" />
                  </motion.div>
                )}
              </motion.button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
