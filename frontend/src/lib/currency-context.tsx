"use client";

import { createContext, useContext, useState, useEffect, ReactNode, useCallback, useRef } from "react";
import { userApi } from "./api";

/**
 * Currency region identifiers matching backend regions.
 */
export type CurrencyRegion =
  | "popular"
  | "europe"
  | "americas"
  | "asia_pacific"
  | "middle_east"
  | "africa"
  | "caribbean";

/**
 * Currency information from the API.
 */
export interface CurrencyInfo {
  code: string;
  symbol: string;
  name: string;
  flag: string;
  region: CurrencyRegion;
  decimal_places: number;
  is_popular: boolean;
}

/**
 * Region information for grouping currencies.
 */
export interface RegionInfo {
  id: CurrencyRegion;
  name: string;
  count: number;
}

/**
 * Popular currencies - quick access list (subset of all currencies).
 * These are loaded immediately before the full list is fetched.
 */
export const POPULAR_CURRENCIES: CurrencyInfo[] = [
  { code: "USD", symbol: "$", name: "US Dollar", flag: "🇺🇸", region: "popular", decimal_places: 2, is_popular: true },
  { code: "EUR", symbol: "€", name: "Euro", flag: "🇪🇺", region: "popular", decimal_places: 2, is_popular: true },
  { code: "GBP", symbol: "£", name: "British Pound", flag: "🇬🇧", region: "popular", decimal_places: 2, is_popular: true },
  { code: "JPY", symbol: "¥", name: "Japanese Yen", flag: "🇯🇵", region: "popular", decimal_places: 0, is_popular: true },
  { code: "CNY", symbol: "¥", name: "Chinese Yuan", flag: "🇨🇳", region: "popular", decimal_places: 2, is_popular: true },
  { code: "CHF", symbol: "Fr", name: "Swiss Franc", flag: "🇨🇭", region: "popular", decimal_places: 2, is_popular: true },
  { code: "CAD", symbol: "$", name: "Canadian Dollar", flag: "🇨🇦", region: "popular", decimal_places: 2, is_popular: true },
  { code: "AUD", symbol: "$", name: "Australian Dollar", flag: "🇦🇺", region: "popular", decimal_places: 2, is_popular: true },
  { code: "INR", symbol: "₹", name: "Indian Rupee", flag: "🇮🇳", region: "popular", decimal_places: 2, is_popular: true },
  { code: "KRW", symbol: "₩", name: "South Korean Won", flag: "🇰🇷", region: "popular", decimal_places: 0, is_popular: true },
  { code: "BRL", symbol: "R$", name: "Brazilian Real", flag: "🇧🇷", region: "popular", decimal_places: 2, is_popular: true },
  { code: "MXN", symbol: "$", name: "Mexican Peso", flag: "🇲🇽", region: "popular", decimal_places: 2, is_popular: true },
  { code: "SGD", symbol: "$", name: "Singapore Dollar", flag: "🇸🇬", region: "popular", decimal_places: 2, is_popular: true },
  { code: "HKD", symbol: "$", name: "Hong Kong Dollar", flag: "🇭🇰", region: "popular", decimal_places: 2, is_popular: true },
  { code: "NZD", symbol: "$", name: "New Zealand Dollar", flag: "🇳🇿", region: "popular", decimal_places: 2, is_popular: true },
  { code: "SEK", symbol: "kr", name: "Swedish Krona", flag: "🇸🇪", region: "popular", decimal_places: 2, is_popular: true },
  { code: "NOK", symbol: "kr", name: "Norwegian Krone", flag: "🇳🇴", region: "popular", decimal_places: 2, is_popular: true },
  { code: "DKK", symbol: "kr", name: "Danish Krone", flag: "🇩🇰", region: "popular", decimal_places: 2, is_popular: true },
  { code: "PLN", symbol: "zł", name: "Polish Złoty", flag: "🇵🇱", region: "popular", decimal_places: 2, is_popular: true },
  { code: "RUB", symbol: "₽", name: "Russian Ruble", flag: "🇷🇺", region: "popular", decimal_places: 2, is_popular: true },
  { code: "TRY", symbol: "₺", name: "Turkish Lira", flag: "🇹🇷", region: "popular", decimal_places: 2, is_popular: true },
  { code: "ZAR", symbol: "R", name: "South African Rand", flag: "🇿🇦", region: "popular", decimal_places: 2, is_popular: true },
  { code: "THB", symbol: "฿", name: "Thai Baht", flag: "🇹🇭", region: "popular", decimal_places: 2, is_popular: true },
  { code: "UAH", symbol: "₴", name: "Ukrainian Hryvnia", flag: "🇺🇦", region: "popular", decimal_places: 2, is_popular: true },
];

/**
 * Legacy CURRENCIES export for backward compatibility.
 * Maps to popular currencies with simplified type.
 */
export type Currency = string;

export const CURRENCIES = POPULAR_CURRENCIES.map((c) => ({
  code: c.code as Currency,
  symbol: c.symbol,
  name: c.name,
  flag: c.flag,
}));

interface CurrencyContextType {
  /** Current selected currency code */
  currency: string;
  /** Set the current currency (also saves to user preferences) */
  setCurrency: (currency: string) => void;
  /** Update currency locally without saving to backend (used when settings already saved) */
  updateCurrencyLocally: (currency: string) => void;
  /** Current currency info (from popular or full list) */
  currencyInfo: CurrencyInfo;
  /** All available currencies grouped by region */
  allCurrencies: Record<CurrencyRegion, CurrencyInfo[]>;
  /** Available regions with currency counts */
  regions: RegionInfo[];
  /** Popular currencies for quick access */
  popularCurrencies: CurrencyInfo[];
  /** Search currencies by query */
  searchCurrencies: (query: string) => CurrencyInfo[];
  /** Loading state for full currency list */
  isLoading: boolean;
  /** Error if currency fetch failed */
  error: string | null;
  /** Refresh currency data from API */
  refresh: () => Promise<void>;
  /** Whether currency is synced with backend */
  isSynced: boolean;
  /** Sync currency from user preferences (call after login) */
  syncFromPreferences: () => Promise<void>;
}

const CurrencyContext = createContext<CurrencyContextType | undefined>(undefined);

const STORAGE_KEY = "subscription-tracker-currency";

/**
 * Region display names for UI.
 */
const REGION_NAMES: Record<CurrencyRegion, string> = {
  popular: "Popular",
  europe: "Europe",
  americas: "Americas",
  asia_pacific: "Asia & Pacific",
  middle_east: "Middle East",
  africa: "Africa",
  caribbean: "Caribbean",
};

/**
 * Default currency (GBP for this app).
 */
const DEFAULT_CURRENCY = "GBP";

export function CurrencyProvider({ children }: { children: ReactNode }) {
  const [currency, setCurrencyState] = useState<string>(DEFAULT_CURRENCY);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSynced, setIsSynced] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [allCurrencies, setAllCurrencies] = useState<Record<CurrencyRegion, CurrencyInfo[]>>({
    popular: POPULAR_CURRENCIES,
    europe: [],
    americas: [],
    asia_pacific: [],
    middle_east: [],
    africa: [],
    caribbean: [],
  });
  const [regions, setRegions] = useState<RegionInfo[]>([
    { id: "popular", name: "Popular", count: POPULAR_CURRENCIES.length },
  ]);

  // Track if we're currently saving to avoid race conditions
  const isSavingRef = useRef(false);
  // Track if initial sync from preferences has happened
  const initialSyncDone = useRef(false);

  // Flatten all currencies for search
  const flatCurrencies = Object.values(allCurrencies).flat();

  // Load currency from localStorage on mount (fallback before API sync)
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      // Validate the stored currency exists in our list
      const exists = flatCurrencies.some((c) => c.code === stored) ||
                     POPULAR_CURRENCIES.some((c) => c.code === stored);
      if (exists) {
        setCurrencyState(stored);
      }
    }
    setIsLoaded(true);
  }, []);

  // Fetch full currency list from API
  const fetchCurrencies = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/v1/currencies");
      if (!response.ok) {
        throw new Error(`Failed to fetch currencies: ${response.status}`);
      }

      const data = await response.json();

      // Update regions
      if (data.regions) {
        setRegions(
          data.regions.map((r: { id: string; name: string; count: number }) => ({
            id: r.id as CurrencyRegion,
            name: r.name,
            count: r.count,
          }))
        );
      }

      // Update currencies by region
      if (data.currencies) {
        const newCurrencies: Record<CurrencyRegion, CurrencyInfo[]> = {
          popular: [],
          europe: [],
          americas: [],
          asia_pacific: [],
          middle_east: [],
          africa: [],
          caribbean: [],
        };

        for (const [regionId, currencies] of Object.entries(data.currencies)) {
          const region = regionId as CurrencyRegion;
          if (region in newCurrencies) {
            newCurrencies[region] = currencies as CurrencyInfo[];
          }
        }

        setAllCurrencies(newCurrencies);
      }
    } catch (err) {
      console.error("Failed to fetch currencies:", err);
      setError(err instanceof Error ? err.message : "Failed to load currencies");
      // Keep using popular currencies as fallback
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch currencies on mount
  useEffect(() => {
    fetchCurrencies();
  }, [fetchCurrencies]);

  // Sync currency from user preferences (called after login or on mount if authenticated)
  const syncFromPreferences = useCallback(async () => {
    // Skip if already syncing or already done initial sync
    if (isSavingRef.current) return;

    try {
      const preferences = await userApi.getPreferences();
      if (preferences.currency) {
        setCurrencyState(preferences.currency);
        localStorage.setItem(STORAGE_KEY, preferences.currency);
        setIsSynced(true);
        initialSyncDone.current = true;
      }
    } catch (err) {
      // If not authenticated or error, just use localStorage value
      console.debug("Could not sync currency from preferences:", err);
    }
  }, []);

  // Try to sync from preferences on mount (if user is already logged in)
  useEffect(() => {
    if (isLoaded && !initialSyncDone.current) {
      // Check if we have an auth token
      const token = localStorage.getItem("money_flow_access_token");
      if (token) {
        syncFromPreferences();
      }
    }
  }, [isLoaded, syncFromPreferences]);

  // Update currency locally without saving to backend (used when settings already saved)
  const updateCurrencyLocally = useCallback((newCurrency: string) => {
    setCurrencyState(newCurrency);
    localStorage.setItem(STORAGE_KEY, newCurrency);
    setIsSynced(true);
  }, []);

  // Save to localStorage and user preferences when currency changes
  const setCurrency = useCallback(async (newCurrency: string) => {
    setCurrencyState(newCurrency);
    localStorage.setItem(STORAGE_KEY, newCurrency);

    // Save to backend user preferences if authenticated
    const token = localStorage.getItem("money_flow_access_token");
    if (token && !isSavingRef.current) {
      isSavingRef.current = true;
      try {
        await userApi.updatePreferences({ currency: newCurrency as any });
        setIsSynced(true);
      } catch (err) {
        console.error("Failed to save currency preference:", err);
        // Still works locally, just not synced
        setIsSynced(false);
      } finally {
        isSavingRef.current = false;
      }
    }
  }, []);

  // Get current currency info
  const currencyInfo =
    flatCurrencies.find((c) => c.code === currency) ||
    POPULAR_CURRENCIES.find((c) => c.code === currency) ||
    POPULAR_CURRENCIES.find((c) => c.code === DEFAULT_CURRENCY) ||
    POPULAR_CURRENCIES[0];

  // Search currencies
  const searchCurrencies = useCallback(
    (query: string): CurrencyInfo[] => {
      if (!query.trim()) {
        return POPULAR_CURRENCIES;
      }

      const lowerQuery = query.toLowerCase().trim();
      const results: Array<{ score: number; currency: CurrencyInfo }> = [];

      for (const curr of flatCurrencies) {
        let score = 0;

        // Exact code match (highest priority)
        if (curr.code.toLowerCase() === lowerQuery) {
          score = 100;
        }
        // Code starts with query
        else if (curr.code.toLowerCase().startsWith(lowerQuery)) {
          score = 80;
        }
        // Code contains query
        else if (curr.code.toLowerCase().includes(lowerQuery)) {
          score = 60;
        }
        // Name starts with query
        else if (curr.name.toLowerCase().startsWith(lowerQuery)) {
          score = 50;
        }
        // Name contains query
        else if (curr.name.toLowerCase().includes(lowerQuery)) {
          score = 30;
        }
        // Symbol matches
        else if (curr.symbol.toLowerCase() === lowerQuery) {
          score = 40;
        }

        if (score > 0) {
          // Boost popular currencies
          if (curr.is_popular) {
            score += 10;
          }
          results.push({ score, currency: curr });
        }
      }

      // Sort by score descending, then by code
      results.sort((a, b) => {
        if (b.score !== a.score) return b.score - a.score;
        return a.currency.code.localeCompare(b.currency.code);
      });

      return results.slice(0, 20).map((r) => r.currency);
    },
    [flatCurrencies]
  );

  // Prevent hydration mismatch by not rendering until loaded
  if (!isLoaded) {
    return null;
  }

  return (
    <CurrencyContext.Provider
      value={{
        currency,
        setCurrency,
        updateCurrencyLocally,
        currencyInfo,
        allCurrencies,
        regions,
        popularCurrencies: POPULAR_CURRENCIES,
        searchCurrencies,
        isLoading,
        error,
        refresh: fetchCurrencies,
        isSynced,
        syncFromPreferences,
      }}
    >
      {children}
    </CurrencyContext.Provider>
  );
}

export function useCurrency() {
  const context = useContext(CurrencyContext);
  if (context === undefined) {
    throw new Error("useCurrency must be used within a CurrencyProvider");
  }
  return context;
}
