"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Bell,
  Clock,
  Calendar,
  Copy,
  Check,
  ExternalLink,
  RefreshCw,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Send,
} from "lucide-react";
import { notificationApi, NotificationPreferences, TelegramLinkResponse } from "@/lib/api";

// Telegram icon component
function TelegramIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
    </svg>
  );
}

export function NotificationSettings() {
  const queryClient = useQueryClient();
  const [copiedCode, setCopiedCode] = useState(false);
  const [telegramLinkData, setTelegramLinkData] = useState<TelegramLinkResponse | null>(null);

  // Fetch notification preferences
  const { data: preferences, isLoading, error } = useQuery({
    queryKey: ["notification-preferences"],
    queryFn: notificationApi.getPreferences,
  });

  // Update preferences mutation
  const updateMutation = useMutation({
    mutationFn: notificationApi.updatePreferences,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notification-preferences"] });
    },
  });

  // Link Telegram mutation
  const linkTelegramMutation = useMutation({
    mutationFn: notificationApi.initiateTelegramLink,
    onSuccess: (data) => {
      setTelegramLinkData(data);
    },
  });

  // Unlink Telegram mutation
  const unlinkTelegramMutation = useMutation({
    mutationFn: notificationApi.unlinkTelegram,
    onSuccess: () => {
      setTelegramLinkData(null);
      queryClient.invalidateQueries({ queryKey: ["notification-preferences"] });
    },
  });

  // Test notification mutation
  const testNotificationMutation = useMutation({
    mutationFn: notificationApi.sendTestNotification,
  });

  const copyCode = async () => {
    if (telegramLinkData?.verification_code) {
      await navigator.clipboard.writeText(telegramLinkData.verification_code);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
  };

  const updatePreference = (key: string, value: boolean | number) => {
    updateMutation.mutate({ [key]: value });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-red-500">
        <AlertCircle className="w-6 h-6 mr-2" />
        Failed to load notification settings
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Notifications</h2>
        <p className="mt-1 text-gray-500 dark:text-gray-400">
          Configure how you receive payment reminders
        </p>
      </div>

      {/* Telegram Integration Section */}
      <section className="mb-8">
        <h3 className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white mb-4">
          <TelegramIcon className="w-5 h-5 text-[#0088cc]" />
          Telegram Integration
        </h3>

        <div className="rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          {preferences?.telegram.linked ? (
            /* Connected State */
            <div className="p-6 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-green-500 flex items-center justify-center">
                    <CheckCircle2 className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">Connected</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      @{preferences.telegram.username || "Telegram User"}
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => testNotificationMutation.mutate()}
                    disabled={testNotificationMutation.isPending}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    {testNotificationMutation.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                    Test
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => unlinkTelegramMutation.mutate()}
                    disabled={unlinkTelegramMutation.isPending}
                    className="px-4 py-2 rounded-xl text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                  >
                    Disconnect
                  </motion.button>
                </div>
              </div>
              {testNotificationMutation.isSuccess && (
                <motion.p
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-3 text-sm text-green-600 dark:text-green-400"
                >
                  ✓ Test notification sent! Check your Telegram.
                </motion.p>
              )}
            </div>
          ) : telegramLinkData ? (
            /* Verification Code State */
            <div className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20">
              <div className="text-center space-y-4">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#0088cc] mb-2">
                  <TelegramIcon className="w-8 h-8 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Your verification code</p>
                  <div className="flex items-center justify-center gap-2">
                    <code className="text-3xl font-mono font-bold tracking-widest text-gray-900 dark:text-white bg-white dark:bg-gray-800 px-6 py-3 rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600">
                      {telegramLinkData.verification_code}
                    </code>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={copyCode}
                      className="p-3 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      {copiedCode ? (
                        <Check className="w-5 h-5 text-green-500" />
                      ) : (
                        <Copy className="w-5 h-5 text-gray-500" />
                      )}
                    </motion.button>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    Expires in {telegramLinkData.expires_in_minutes} minutes
                  </p>
                </div>

                <a
                  href={telegramLinkData.bot_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-[#0088cc] text-white font-medium hover:bg-[#0077b5] transition-colors"
                >
                  <TelegramIcon className="w-5 h-5" />
                  Open @{telegramLinkData.bot_username}
                  <ExternalLink className="w-4 h-4" />
                </a>

                <div className="text-left bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
                  <p className="font-medium text-gray-900 dark:text-white mb-2">How to connect:</p>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600 dark:text-gray-400">
                    <li>Copy the code above</li>
                    <li>Click the blue button to open Telegram</li>
                    <li>Send the code to the bot</li>
                    <li>Click "Check Status" below to confirm</li>
                  </ol>
                </div>

                <button
                  onClick={() => queryClient.invalidateQueries({ queryKey: ["notification-preferences"] })}
                  className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Check Status
                </button>
              </div>
            </div>
          ) : (
            /* Not Connected State */
            <div className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                    <TelegramIcon className="w-6 h-6 text-gray-400" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">Not Connected</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Receive reminders directly in Telegram
                    </p>
                  </div>
                </div>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => linkTelegramMutation.mutate()}
                  disabled={linkTelegramMutation.isPending}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#0088cc] text-white font-medium hover:bg-[#0077b5] transition-colors disabled:opacity-50"
                >
                  {linkTelegramMutation.isPending ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <TelegramIcon className="w-5 h-5" />
                  )}
                  Connect Telegram
                </motion.button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Payment Reminders Section */}
      <section className="mb-8">
        <h3 className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white mb-4">
          <Bell className="w-5 h-5 text-blue-500" />
          Payment Reminders
        </h3>

        <div className="space-y-4">
          {/* Enable Reminders */}
          <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
            <div>
              <p className="font-medium text-gray-900 dark:text-white">Enable reminders</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Get notified before payments are due
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences?.reminder_enabled ?? true}
                onChange={(e) => updatePreference("reminder_enabled", e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-600 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Days Before */}
          <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-gray-400" />
              <div>
                <p className="font-medium text-gray-900 dark:text-white">Days before</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  When to send the reminder
                </p>
              </div>
            </div>
            <select
              value={preferences?.reminder_days_before ?? 3}
              onChange={(e) => updatePreference("reminder_days_before", parseInt(e.target.value))}
              className="px-4 py-2 rounded-xl border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value={1}>1 day</option>
              <option value={2}>2 days</option>
              <option value={3}>3 days</option>
              <option value={5}>5 days</option>
              <option value={7}>7 days</option>
            </select>
          </div>

          {/* Overdue Alerts */}
          <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
            <div>
              <p className="font-medium text-gray-900 dark:text-white">Overdue alerts</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Get notified about missed payments
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences?.overdue_alerts ?? true}
                onChange={(e) => updatePreference("overdue_alerts", e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-600 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>
      </section>

      {/* Digests Section */}
      <section>
        <h3 className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white mb-4">
          <Calendar className="w-5 h-5 text-purple-500" />
          Digests
        </h3>

        <div className="space-y-4">
          {/* Daily Digest */}
          <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
            <div>
              <p className="font-medium text-gray-900 dark:text-white">Daily digest</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Summary of today&apos;s and upcoming payments
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences?.daily_digest ?? false}
                onChange={(e) => updatePreference("daily_digest", e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-600 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-purple-600"></div>
            </label>
          </div>

          {/* Weekly Digest */}
          <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900 dark:text-white">Weekly digest</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Weekly summary of all payments
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences?.weekly_digest ?? true}
                  onChange={(e) => updatePreference("weekly_digest", e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-600 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-purple-600"></div>
              </label>
            </div>

            <AnimatePresence>
              {preferences?.weekly_digest && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700"
                >
                  <p className="text-sm text-gray-600 dark:text-gray-400">Send on</p>
                  <select
                    value={preferences?.weekly_digest_day ?? 0}
                    onChange={(e) => updatePreference("weekly_digest_day", parseInt(e.target.value))}
                    className="px-4 py-2 rounded-xl border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
                  >
                    <option value={0}>Monday</option>
                    <option value={1}>Tuesday</option>
                    <option value={2}>Wednesday</option>
                    <option value={3}>Thursday</option>
                    <option value={4}>Friday</option>
                    <option value={5}>Saturday</option>
                    <option value={6}>Sunday</option>
                  </select>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </section>
    </div>
  );
}
