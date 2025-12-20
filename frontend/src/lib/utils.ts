import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Exchange rates cache (USD-based rates fetched from API)
 * Rates are relative to USD (1 USD = X currency)
 */
let cachedRates: Record<string, number> = {};
let cacheTimestamp: number = 0;
const CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour cache

/**
 * Fetch exchange rates from backend API
 */
async function fetchExchangeRates(): Promise<Record<string, number>> {
  try {
    const response = await fetch("/api/v1/subscriptions/exchange-rates");
    if (!response.ok) {
      throw new Error(`Failed to fetch rates: ${response.status}`);
    }
    const data = await response.json();
    return data.rates || {};
  } catch (err) {
    console.error("Failed to fetch exchange rates:", err);
    // Return minimal fallback rates if API fails
    return {
      USD: 1,
      GBP: 0.79,
      EUR: 0.92,
      UAD: 42.0,
    };
  }
}

/**
 * Get exchange rates (cached)
 */
export async function getExchangeRates(): Promise<Record<string, number>> {
  const now = Date.now();
  if (Object.keys(cachedRates).length === 0 || now - cacheTimestamp > CACHE_TTL_MS) {
    cachedRates = await fetchExchangeRates();
    cacheTimestamp = now;
  }
  return cachedRates;
}

/**
 * Set exchange rates from external source (e.g., currency context)
 */
export function setExchangeRates(rates: Record<string, number>): void {
  cachedRates = rates;
  cacheTimestamp = Date.now();
}

/**
 * Get cached exchange rates synchronously (returns empty if not loaded)
 */
export function getCachedRates(): Record<string, number> {
  return cachedRates;
}

/**
 * Convert amount from one currency to another using USD-based rates
 * @param amount The amount to convert
 * @param fromCurrency Source currency code
 * @param toCurrency Target currency code
 * @param rates USD-based exchange rates
 * @returns Converted amount
 */
function convertWithRates(
  amount: number,
  fromCurrency: string,
  toCurrency: string,
  rates: Record<string, number>
): number {
  if (fromCurrency === toCurrency) return amount;

  const fromRate = rates[fromCurrency] || rates[fromCurrency.toUpperCase()];
  const toRate = rates[toCurrency] || rates[toCurrency.toUpperCase()];

  if (!fromRate || !toRate) {
    console.warn(`Missing rate for ${fromCurrency} or ${toCurrency}, using 1:1`);
    return amount;
  }

  // Convert: amount in fromCurrency -> USD -> toCurrency
  // fromRate = how many fromCurrency per 1 USD
  // toRate = how many toCurrency per 1 USD
  // amountInUSD = amount / fromRate
  // amountInTarget = amountInUSD * toRate
  return (amount / fromRate) * toRate;
}

/**
 * Format currency with proper locale and symbol
 */
export function formatCurrency(
  amount: number | string,
  currency: string = "GBP",
  displayCurrency?: string
): string {
  const num = typeof amount === "string" ? parseFloat(amount) : amount;

  // If displayCurrency is provided and different, convert
  const targetCurrency = displayCurrency || currency;
  let convertedAmount = num;

  if (displayCurrency && displayCurrency !== currency) {
    convertedAmount = convertWithRates(num, currency, displayCurrency, cachedRates);
  }

  // Use Intl.NumberFormat with the target currency
  // Let the browser handle locale selection based on currency
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: targetCurrency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(convertedAmount);
  } catch {
    // Fallback for unknown currencies
    return `${targetCurrency} ${convertedAmount.toFixed(0)}`;
  }
}

/**
 * Convert amount between currencies (sync version using cached rates)
 */
export function convertCurrency(
  amount: number,
  fromCurrency: string,
  toCurrency: string
): number {
  return convertWithRates(amount, fromCurrency, toCurrency, cachedRates);
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString("en-GB", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function getFrequencyLabel(frequency: string, interval: number = 1): string {
  // For CUSTOM frequency, show "Every X months"
  if (frequency.toUpperCase() === "CUSTOM") {
    return `Every ${interval} month${interval > 1 ? "s" : ""}`;
  }
  if (interval > 1) {
    return `Every ${interval} ${frequency.toLowerCase()}${interval > 1 ? "s" : ""}`;
  }
  return frequency.charAt(0).toUpperCase() + frequency.slice(1).toLowerCase();
}
