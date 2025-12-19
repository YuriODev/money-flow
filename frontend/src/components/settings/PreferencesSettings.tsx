"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Globe,
  Calendar,
  Layout,
  Sun,
  Moon,
  Monitor,
  Save,
  Loader2,
  Check,
  Clock,
  Hash,
} from "lucide-react";
import { userApi, UserPreferences, UserPreferencesUpdate } from "@/lib/api";
import { useTheme } from "@/lib/theme-context";

const CURRENCIES = [
  { code: "GBP", name: "British Pound", symbol: "£" },
  { code: "USD", name: "US Dollar", symbol: "$" },
  { code: "EUR", name: "Euro", symbol: "€" },
  { code: "UAH", name: "Ukrainian Hryvnia", symbol: "₴" },
  { code: "CAD", name: "Canadian Dollar", symbol: "C$" },
  { code: "AUD", name: "Australian Dollar", symbol: "A$" },
  { code: "JPY", name: "Japanese Yen", symbol: "¥" },
  { code: "CHF", name: "Swiss Franc", symbol: "CHF" },
  { code: "CNY", name: "Chinese Yuan", symbol: "¥" },
  { code: "INR", name: "Indian Rupee", symbol: "₹" },
] as const;

const DATE_FORMATS = [
  { value: "DD/MM/YYYY", label: "DD/MM/YYYY", example: "25/12/2025" },
  { value: "MM/DD/YYYY", label: "MM/DD/YYYY", example: "12/25/2025" },
  { value: "YYYY-MM-DD", label: "YYYY-MM-DD", example: "2025-12-25" },
] as const;

const NUMBER_FORMATS = [
  { value: "1,234.56", label: "1,234.56", description: "UK/US format" },
  { value: "1.234,56", label: "1.234,56", description: "EU format" },
] as const;

const DEFAULT_VIEWS = [
  { value: "list", label: "List View", description: "Traditional list layout" },
  { value: "calendar", label: "Calendar View", description: "Monthly calendar view" },
  { value: "cards", label: "Cards View", description: "Card-based dashboard" },
  { value: "agent", label: "Agent View", description: "AI assistant interface" },
] as const;

const WEEK_STARTS = [
  { value: "monday", label: "Monday" },
  { value: "sunday", label: "Sunday" },
] as const;

export function PreferencesSettings() {
  const queryClient = useQueryClient();
  const { theme: currentTheme, themePreference: _themePreference, setTheme: setAppTheme } = useTheme();

  // Fetch preferences
  const { data: preferences, isLoading } = useQuery({
    queryKey: ["userPreferences"],
    queryFn: () => userApi.getPreferences(),
  });

  // Form state
  const [formData, setFormData] = useState<UserPreferencesUpdate>({});
  const [saved, setSaved] = useState(false);
  const [initialSynced, setInitialSynced] = useState(false);

  // Initialize form data when preferences are loaded
  useEffect(() => {
    if (preferences) {
      setFormData({
        currency: preferences.currency,
        date_format: preferences.date_format,
        number_format: preferences.number_format,
        theme: preferences.theme,
        default_view: preferences.default_view,
        compact_mode: preferences.compact_mode,
        week_start: preferences.week_start,
        show_currency_symbol: preferences.show_currency_symbol,
      });

      // Sync theme from server preferences on initial load
      if (!initialSynced && preferences.theme) {
        setAppTheme(preferences.theme as "light" | "dark" | "system");
        setInitialSynced(true);
      }
    }
  }, [preferences, initialSynced, setAppTheme]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: UserPreferencesUpdate) => userApi.updatePreferences(data),
    onSuccess: (data) => {
      setSaved(true);
      queryClient.setQueryData(["userPreferences"], data);
      // Apply theme change immediately - pass the preference directly
      if (data.theme) {
        setAppTheme(data.theme as "light" | "dark" | "system");
      }
      setTimeout(() => setSaved(false), 2000);
    },
  });

  const handleChange = (key: keyof UserPreferencesUpdate, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    updateMutation.mutate(formData);
  };

  const hasChanges = () => {
    if (!preferences) return false;
    return Object.keys(formData).some(
      (key) => formData[key as keyof UserPreferencesUpdate] !== preferences[key as keyof UserPreferences]
    );
  };

  if (isLoading) {
    return (
      <div className="p-6 lg:p-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded-lg" />
          <div className="h-4 w-72 bg-gray-200 dark:bg-gray-700 rounded-lg" />
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Preferences
        </h2>
        <p className="mt-1 text-gray-500 dark:text-gray-400">
          Customize your experience
        </p>
      </div>

      <div className="space-y-8">
        {/* Display Section */}
        <section>
          <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
            Display
          </h3>

          {/* Currency */}
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shrink-0">
                  <Globe className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <label className="block text-sm font-medium text-gray-900 dark:text-white mb-1">
                    Default Currency
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                    Used for displaying amounts and conversions
                  </p>
                  <select
                    value={formData.currency || "GBP"}
                    onChange={(e) => handleChange("currency", e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  >
                    {CURRENCIES.map((currency) => (
                      <option key={currency.code} value={currency.code}>
                        {currency.symbol} - {currency.name} ({currency.code})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Date Format */}
            <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shrink-0">
                  <Calendar className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <label className="block text-sm font-medium text-gray-900 dark:text-white mb-1">
                    Date Format
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                    How dates are displayed throughout the app
                  </p>
                  <div className="grid grid-cols-3 gap-2">
                    {DATE_FORMATS.map((format) => (
                      <button
                        key={format.value}
                        onClick={() => handleChange("date_format", format.value)}
                        className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                          formData.date_format === format.value
                            ? "bg-blue-500 text-white"
                            : "bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-600 hover:border-blue-500"
                        }`}
                      >
                        <span className="block">{format.label}</span>
                        <span className="block text-xs opacity-70">{format.example}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Number Format */}
            <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center shrink-0">
                  <Hash className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <label className="block text-sm font-medium text-gray-900 dark:text-white mb-1">
                    Number Format
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                    How numbers are formatted
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    {NUMBER_FORMATS.map((format) => (
                      <button
                        key={format.value}
                        onClick={() => handleChange("number_format", format.value)}
                        className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                          formData.number_format === format.value
                            ? "bg-purple-500 text-white"
                            : "bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-600 hover:border-purple-500"
                        }`}
                      >
                        <span className="block">{format.label}</span>
                        <span className="block text-xs opacity-70">{format.description}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Appearance Section */}
        <section>
          <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
            Appearance
          </h3>

          <div className="space-y-4">
            {/* Theme */}
            <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shrink-0">
                  {currentTheme === "dark" ? (
                    <Moon className="w-5 h-5 text-white" />
                  ) : (
                    <Sun className="w-5 h-5 text-white" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <label className="block text-sm font-medium text-gray-900 dark:text-white mb-1">
                    Theme
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                    Choose your preferred color scheme
                  </p>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { value: "light", label: "Light", icon: Sun },
                      { value: "dark", label: "Dark", icon: Moon },
                      { value: "system", label: "System", icon: Monitor },
                    ].map((option) => (
                      <button
                        key={option.value}
                        onClick={() => handleChange("theme", option.value)}
                        className={`flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                          formData.theme === option.value
                            ? "bg-amber-500 text-white"
                            : "bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-600 hover:border-amber-500"
                        }`}
                      >
                        <option.icon className="w-4 h-4" />
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Default View */}
            <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shrink-0">
                  <Layout className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <label className="block text-sm font-medium text-gray-900 dark:text-white mb-1">
                    Default View
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                    Which view to show when you open the app
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    {DEFAULT_VIEWS.map((view) => (
                      <button
                        key={view.value}
                        onClick={() => handleChange("default_view", view.value)}
                        className={`px-3 py-2 rounded-lg text-sm font-medium text-left transition-all ${
                          formData.default_view === view.value
                            ? "bg-cyan-500 text-white"
                            : "bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-600 hover:border-cyan-500"
                        }`}
                      >
                        <span className="block">{view.label}</span>
                        <span className="block text-xs opacity-70">{view.description}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Compact Mode Toggle */}
            <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gray-500 to-gray-600 flex items-center justify-center shrink-0">
                    <Layout className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-900 dark:text-white">
                      Compact Mode
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Show more items with less spacing
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleChange("compact_mode", !formData.compact_mode)}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    formData.compact_mode
                      ? "bg-blue-500"
                      : "bg-gray-300 dark:bg-gray-600"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform ${
                      formData.compact_mode ? "translate-x-6" : ""
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Regional Section */}
        <section>
          <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
            Regional
          </h3>

          <div className="space-y-4">
            {/* Week Start */}
            <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 to-green-600 flex items-center justify-center shrink-0">
                  <Clock className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <label className="block text-sm font-medium text-gray-900 dark:text-white mb-1">
                    Week Starts On
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                    First day of the week in calendars
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    {WEEK_STARTS.map((day) => (
                      <button
                        key={day.value}
                        onClick={() => handleChange("week_start", day.value)}
                        className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                          formData.week_start === day.value
                            ? "bg-teal-500 text-white"
                            : "bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-600 hover:border-teal-500"
                        }`}
                      >
                        {day.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Currency Symbol Toggle */}
            <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shrink-0">
                    <span className="text-white text-lg font-bold">£</span>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-900 dark:text-white">
                      Show Currency Symbols
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Display £, $, etc. before amounts
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleChange("show_currency_symbol", !formData.show_currency_symbol)}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    formData.show_currency_symbol
                      ? "bg-green-500"
                      : "bg-gray-300 dark:bg-gray-600"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform ${
                      formData.show_currency_symbol ? "translate-x-6" : ""
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Save Button */}
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSave}
            disabled={updateMutation.isPending || !hasChanges()}
            className={`
              flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-medium transition-all
              ${
                saved
                  ? "bg-green-500 text-white"
                  : "bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:shadow-lg hover:shadow-blue-500/25"
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
          >
            {updateMutation.isPending ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Saving...
              </>
            ) : saved ? (
              <>
                <Check className="w-5 h-5" />
                Saved!
              </>
            ) : (
              <>
                <Save className="w-5 h-5" />
                Save Preferences
              </>
            )}
          </motion.button>
        </div>
      </div>
    </div>
  );
}
