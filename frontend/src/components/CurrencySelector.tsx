"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Check, Search, Globe, Loader2 } from "lucide-react";
import { useCurrency, type CurrencyInfo, type CurrencyRegion } from "@/lib/currency-context";
import { cn } from "@/lib/utils";

/**
 * Region tab for filtering currencies.
 */
interface RegionTab {
  id: CurrencyRegion | "all";
  label: string;
  count: number;
}

export function CurrencySelector() {
  const {
    currency,
    setCurrency,
    currencyInfo,
    allCurrencies,
    regions,
    popularCurrencies,
    searchCurrencies,
    isLoading,
  } = useCurrency();

  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeRegion, setActiveRegion] = useState<CurrencyRegion | "all">("popular");
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery("");
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      setTimeout(() => searchInputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Build region tabs
  const regionTabs: RegionTab[] = useMemo(() => {
    const tabs: RegionTab[] = [
      { id: "popular", label: "Popular", count: popularCurrencies.length },
    ];

    // Add other regions from API
    for (const region of regions) {
      if (region.id !== "popular") {
        tabs.push({
          id: region.id,
          label: region.name,
          count: region.count,
        });
      }
    }

    return tabs;
  }, [regions, popularCurrencies]);

  // Get currencies for current view
  const displayedCurrencies = useMemo(() => {
    // If searching, use search results
    if (searchQuery.trim()) {
      return searchCurrencies(searchQuery);
    }

    // Otherwise filter by region
    if (activeRegion === "all") {
      return Object.values(allCurrencies).flat();
    }

    return allCurrencies[activeRegion] || popularCurrencies;
  }, [searchQuery, activeRegion, allCurrencies, popularCurrencies, searchCurrencies]);

  const handleSelect = (code: string) => {
    setCurrency(code);
    setIsOpen(false);
    setSearchQuery("");
  };

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open);
    if (!open) {
      setSearchQuery("");
    }
  };

  return (
    <div ref={containerRef} className="relative">
      {/* Trigger Button */}
      <motion.button
        onClick={() => handleOpenChange(!isOpen)}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className={cn(
          "flex items-center gap-2 px-3 py-2 rounded-xl transition-all duration-200",
          "glass-card-subtle hover:shadow-md",
          isOpen && "ring-2 ring-blue-200 dark:ring-blue-700"
        )}
        aria-label="Select currency"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <span className="text-lg">{currencyInfo.flag}</span>
        <span className="font-semibold text-gray-700 dark:text-gray-200">
          {currencyInfo.symbol}
        </span>
        <span className="text-sm text-gray-500 dark:text-gray-400 hidden sm:inline">
          {currency}
        </span>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown className="w-4 h-4 text-gray-400 dark:text-gray-500" />
        </motion.div>
      </motion.button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-full mt-2 z-50 w-80 sm:w-96 glass-card rounded-2xl shadow-xl overflow-hidden bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700"
            role="listbox"
            aria-label="Currency options"
          >
            {/* Search Input */}
            <div className="p-3 border-b border-gray-100 dark:border-gray-700">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search currencies..."
                  className={cn(
                    "w-full pl-9 pr-4 py-2 rounded-xl text-sm",
                    "bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700",
                    "focus:outline-none focus:ring-2 focus:ring-blue-200 dark:focus:ring-blue-700",
                    "text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
                  )}
                  aria-label="Search currencies"
                />
                {isLoading && (
                  <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 animate-spin" />
                )}
              </div>
            </div>

            {/* Region Tabs (only show when not searching) */}
            {!searchQuery.trim() && (
              <div className="px-3 py-2 border-b border-gray-100 dark:border-gray-700">
                <div className="flex gap-1 overflow-x-auto scrollbar-hide">
                  {regionTabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveRegion(tab.id)}
                      className={cn(
                        "px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors",
                        activeRegion === tab.id
                          ? "bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300"
                          : "text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                      )}
                    >
                      {tab.label}
                      <span className="ml-1 text-gray-400 dark:text-gray-500">
                        ({tab.count})
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Currency List */}
            <div className="max-h-72 overflow-y-auto p-2">
              {displayedCurrencies.length === 0 ? (
                <div className="py-8 text-center text-gray-500 dark:text-gray-400">
                  <Globe className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No currencies found</p>
                  <p className="text-xs mt-1">Try a different search term</p>
                </div>
              ) : (
                <div className="space-y-0.5">
                  {displayedCurrencies.map((c) => (
                    <CurrencyOption
                      key={c.code}
                      currency={c}
                      isSelected={currency === c.code}
                      onSelect={handleSelect}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Footer with count */}
            <div className="px-3 py-2 border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
              <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                {searchQuery.trim() ? (
                  <>
                    {displayedCurrencies.length} result
                    {displayedCurrencies.length !== 1 ? "s" : ""} for &quot;
                    {searchQuery}&quot;
                  </>
                ) : (
                  <>
                    {displayedCurrencies.length} currencies in{" "}
                    {activeRegion === "all"
                      ? "all regions"
                      : regionTabs.find((t) => t.id === activeRegion)?.label || activeRegion}
                  </>
                )}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * Individual currency option in the dropdown.
 */
function CurrencyOption({
  currency,
  isSelected,
  onSelect,
}: {
  currency: CurrencyInfo;
  isSelected: boolean;
  onSelect: (code: string) => void;
}) {
  return (
    <motion.button
      onClick={() => onSelect(currency.code)}
      whileHover={{ x: 4 }}
      className={cn(
        "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200",
        isSelected
          ? "bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/30 dark:to-indigo-900/30 text-blue-700 dark:text-blue-400"
          : "hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200"
      )}
      role="option"
      aria-selected={isSelected}
    >
      <span className="text-xl">{currency.flag}</span>
      <div className="flex-1 text-left min-w-0">
        <p className="font-medium truncate">
          {currency.symbol} {currency.code}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
          {currency.name}
        </p>
      </div>
      {currency.is_popular && !isSelected && (
        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">
          Popular
        </span>
      )}
      {isSelected && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="w-5 h-5 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-center flex-shrink-0"
        >
          <Check className="w-3 h-3 text-white" />
        </motion.div>
      )}
    </motion.button>
  );
}
