import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Static exchange rates (approximate - for display conversion)
const EXCHANGE_RATES: Record<string, Record<string, number>> = {
  GBP: { GBP: 1, USD: 1.27, EUR: 1.17, UAH: 52.5 },
  USD: { GBP: 0.79, USD: 1, EUR: 0.92, UAH: 41.3 },
  EUR: { GBP: 0.86, USD: 1.09, EUR: 1, UAH: 45.0 },
  UAH: { GBP: 0.019, USD: 0.024, EUR: 0.022, UAH: 1 },
};

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
    const rate = EXCHANGE_RATES[currency]?.[displayCurrency] || 1;
    convertedAmount = num * rate;
  }

  // Use appropriate locale for currency to get correct symbol
  const localeMap: Record<string, string> = {
    USD: "en-US",
    GBP: "en-GB",
    EUR: "en-IE", // Irish English: €4,284 (symbol first, comma separator)
    UAH: "uk-UA",
  };
  const locale = localeMap[targetCurrency] || "en-GB";

  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: targetCurrency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(convertedAmount);
}

/**
 * Convert amount between currencies
 */
export function convertCurrency(
  amount: number,
  fromCurrency: string,
  toCurrency: string
): number {
  if (fromCurrency === toCurrency) return amount;
  const rate = EXCHANGE_RATES[fromCurrency]?.[toCurrency] || 1;
  return amount * rate;
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
