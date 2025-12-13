"use client";

import { useCallback } from "react";
import { useCurrency } from "@/lib/currency-context";
import { formatCurrency as formatCurrencyUtil, convertCurrency } from "@/lib/utils";

/**
 * Hook for currency formatting with global currency preference
 *
 * Usage:
 * const { format, convert } = useCurrencyFormat();
 * format(15.99, "GBP") // Will show in user's preferred currency
 */
export function useCurrencyFormat() {
  const { currency: displayCurrency } = useCurrency();

  /**
   * Format amount in the user's preferred display currency
   * @param amount - The amount to format
   * @param originalCurrency - The currency the amount is stored in
   * @returns Formatted string in display currency
   */
  const format = useCallback(
    (amount: number | string, originalCurrency: string = "GBP") => {
      return formatCurrencyUtil(amount, originalCurrency, displayCurrency);
    },
    [displayCurrency]
  );

  /**
   * Convert amount to display currency
   * @param amount - The amount to convert
   * @param originalCurrency - The currency the amount is in
   * @returns The converted number
   */
  const convert = useCallback(
    (amount: number, originalCurrency: string = "GBP") => {
      return convertCurrency(amount, originalCurrency, displayCurrency);
    },
    [displayCurrency]
  );

  return {
    format,
    convert,
    displayCurrency,
  };
}
