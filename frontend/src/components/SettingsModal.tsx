"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  X,
  Settings,
  Bell,
  User,
  Check,
  Loader2,
  ExternalLink,
  Copy,
  RefreshCw,
  Unlink,
  Send,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { notificationApi, NotificationPreferences, TelegramLinkResponse } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { toast } from "@/components/Toast";

// Telegram icon SVG
const TelegramIcon = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" className={className} fill="currentColor">
    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
  </svg>
);

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type TabType = "profile" | "notifications";

const WEEKDAYS = [
  { value: 0, label: "Monday" },
  { value: 1, label: "Tuesday" },
  { value: 2, label: "Wednesday" },
  { value: 3, label: "Thursday" },
  { value: 4, label: "Friday" },
  { value: 5, label: "Saturday" },
  { value: 6, label: "Sunday" },
];

const REMINDER_DAYS = [1, 2, 3, 5, 7, 14];

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<TabType>("notifications");
  const [telegramLinkData, setTelegramLinkData] = useState<TelegramLinkResponse | null>(null);
  const [copied, setCopied] = useState(false);

  // Fetch notification preferences
  const { data: preferences, isLoading: prefsLoading } = useQuery({
    queryKey: ["notification-preferences"],
    queryFn: notificationApi.getPreferences,
    enabled: isOpen,
  });

  // Update preferences mutation
  const updatePrefsMutation = useMutation({
    mutationFn: notificationApi.updatePreferences,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notification-preferences"] });
      toast.success("Settings saved", "Your notification preferences have been updated.");
    },
    onError: () => {
      toast.error("Failed to save", "Could not update your preferences. Please try again.");
    },
  });

  // Initiate Telegram link mutation
  const linkTelegramMutation = useMutation({
    mutationFn: notificationApi.initiateTelegramLink,
    onSuccess: (data) => {
      setTelegramLinkData(data);
    },
    onError: () => {
      toast.error("Failed to generate code", "Could not generate verification code. Please try again.");
    },
  });

  // Unlink Telegram mutation
  const unlinkTelegramMutation = useMutation({
    mutationFn: notificationApi.unlinkTelegram,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notification-preferences"] });
      setTelegramLinkData(null);
      toast.success("Telegram unlinked", "Your Telegram account has been disconnected.");
    },
    onError: () => {
      toast.error("Failed to unlink", "Could not unlink Telegram. Please try again.");
    },
  });

  // Test notification mutation
  const testNotificationMutation = useMutation({
    mutationFn: notificationApi.sendTestNotification,
    onSuccess: () => {
      toast.success("Test sent", "Check your Telegram for the test message.");
    },
    onError: () => {
      toast.error("Failed to send", "Could not send test notification. Please try again.");
    },
  });

  // Copy verification code
  const copyCode = async () => {
    if (telegramLinkData?.verification_code) {
      await navigator.clipboard.writeText(telegramLinkData.verification_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Close on Escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setTelegramLinkData(null);
      setCopied(false);
    }
  }, [isOpen]);

  const handleToggle = (field: keyof NotificationPreferences) => {
    if (!preferences) return;
    updatePrefsMutation.mutate({
      [field]: !preferences[field],
    });
  };

  const handleSelectChange = (field: string, value: number | string) => {
    updatePrefsMutation.mutate({
      [field]: value,
    });
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-2xl max-h-[90vh] overflow-hidden"
            role="dialog"
            aria-modal="true"
            aria-labelledby="settings-title"
          >
            <div className="glass-card rounded-2xl shadow-2xl mx-4 flex flex-col max-h-[85vh]">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500">
                    <Settings className="w-5 h-5 text-white" />
                  </div>
                  <h2 id="settings-title" className="text-lg font-semibold text-gray-900 dark:text-white">
                    Settings
                  </h2>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  aria-label="Close settings"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              {/* Tabs */}
              <div className="flex border-b border-gray-200 dark:border-gray-700 px-6">
                <button
                  onClick={() => setActiveTab("profile")}
                  className={cn(
                    "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors",
                    activeTab === "profile"
                      ? "border-indigo-500 text-indigo-600 dark:text-indigo-400"
                      : "border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                  )}
                >
                  <User className="w-4 h-4" />
                  Profile
                </button>
                <button
                  onClick={() => setActiveTab("notifications")}
                  className={cn(
                    "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors",
                    activeTab === "notifications"
                      ? "border-indigo-500 text-indigo-600 dark:text-indigo-400"
                      : "border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                  )}
                >
                  <Bell className="w-4 h-4" />
                  Notifications
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {activeTab === "profile" && (
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Email
                      </label>
                      <input
                        type="email"
                        value={user?.email || ""}
                        disabled
                        className="w-full px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Full Name
                      </label>
                      <input
                        type="text"
                        value={user?.full_name || ""}
                        disabled
                        placeholder="Not set"
                        className="w-full px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                      />
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Profile editing coming soon.
                    </p>
                  </div>
                )}

                {activeTab === "notifications" && (
                  <div className="space-y-8">
                    {prefsLoading ? (
                      <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
                      </div>
                    ) : (
                      <>
                        {/* Telegram Connection */}
                        <section>
                          <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-4">
                            Telegram Integration
                          </h3>

                          {preferences?.telegram.linked ? (
                            <div className="glass-card-subtle rounded-xl p-4 space-y-4">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <div className="p-2 rounded-lg bg-[#0088cc]/10">
                                    <TelegramIcon className="w-5 h-5 text-[#0088cc]" />
                                  </div>
                                  <div>
                                    <p className="font-medium text-gray-900 dark:text-white">
                                      Connected
                                    </p>
                                    {preferences.telegram.username && (
                                      <p className="text-sm text-gray-500 dark:text-gray-400">
                                        @{preferences.telegram.username}
                                      </p>
                                    )}
                                  </div>
                                </div>
                                <div className="flex items-center gap-2">
                                  <button
                                    onClick={() => testNotificationMutation.mutate()}
                                    disabled={testNotificationMutation.isPending}
                                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-200 dark:hover:bg-indigo-900/50 transition-colors"
                                  >
                                    {testNotificationMutation.isPending ? (
                                      <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                      <Send className="w-4 h-4" />
                                    )}
                                    Test
                                  </button>
                                  <button
                                    onClick={() => unlinkTelegramMutation.mutate()}
                                    disabled={unlinkTelegramMutation.isPending}
                                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
                                  >
                                    {unlinkTelegramMutation.isPending ? (
                                      <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                      <Unlink className="w-4 h-4" />
                                    )}
                                    Unlink
                                  </button>
                                </div>
                              </div>
                            </div>
                          ) : telegramLinkData ? (
                            <div className="glass-card-subtle rounded-xl p-4 space-y-4">
                              <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-[#0088cc]/10">
                                  <TelegramIcon className="w-5 h-5 text-[#0088cc]" />
                                </div>
                                <div>
                                  <p className="font-medium text-gray-900 dark:text-white">
                                    Link Your Telegram
                                  </p>
                                  <p className="text-sm text-gray-500 dark:text-gray-400">
                                    Expires in {telegramLinkData.expires_in_minutes} minutes
                                  </p>
                                </div>
                              </div>

                              <div className="space-y-3">
                                <div className="flex items-center gap-2">
                                  <div className="flex-1 px-4 py-3 bg-gray-100 dark:bg-gray-800 rounded-lg font-mono text-lg text-center tracking-widest">
                                    {telegramLinkData.verification_code}
                                  </div>
                                  <button
                                    onClick={copyCode}
                                    className="p-3 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                                    aria-label="Copy code"
                                  >
                                    {copied ? (
                                      <Check className="w-5 h-5 text-green-500" />
                                    ) : (
                                      <Copy className="w-5 h-5 text-gray-500" />
                                    )}
                                  </button>
                                </div>

                                <a
                                  href={telegramLinkData.bot_link}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-lg bg-[#0088cc] text-white font-medium hover:bg-[#0077b5] transition-colors"
                                >
                                  <TelegramIcon className="w-5 h-5" />
                                  Open @{telegramLinkData.bot_username}
                                  <ExternalLink className="w-4 h-4" />
                                </a>

                                <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
                                  Send the code above to the bot to complete linking
                                </p>

                                <button
                                  onClick={() => queryClient.invalidateQueries({ queryKey: ["notification-preferences"] })}
                                  className="flex items-center justify-center gap-2 w-full px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                                >
                                  <RefreshCw className="w-4 h-4" />
                                  Check connection status
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="glass-card-subtle rounded-xl p-4">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <div className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800">
                                    <TelegramIcon className="w-5 h-5 text-gray-400" />
                                  </div>
                                  <div>
                                    <p className="font-medium text-gray-900 dark:text-white">
                                      Not Connected
                                    </p>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">
                                      Receive reminders via Telegram
                                    </p>
                                  </div>
                                </div>
                                <button
                                  onClick={() => linkTelegramMutation.mutate()}
                                  disabled={linkTelegramMutation.isPending}
                                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#0088cc] text-white font-medium hover:bg-[#0077b5] transition-colors disabled:opacity-50"
                                >
                                  {linkTelegramMutation.isPending ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                  ) : (
                                    <TelegramIcon className="w-4 h-4" />
                                  )}
                                  Connect
                                </button>
                              </div>
                            </div>
                          )}
                        </section>

                        {/* Reminder Settings */}
                        <section>
                          <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-4">
                            Payment Reminders
                          </h3>

                          <div className="space-y-4">
                            <SettingToggle
                              label="Enable reminders"
                              description="Receive notifications before payments are due"
                              checked={preferences?.reminder_enabled ?? true}
                              onChange={() => handleToggle("reminder_enabled" as keyof NotificationPreferences)}
                              disabled={updatePrefsMutation.isPending}
                            />

                            <div className="flex items-center justify-between py-2">
                              <div>
                                <p className="font-medium text-gray-900 dark:text-white">Days before</p>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                  When to send the reminder
                                </p>
                              </div>
                              <select
                                value={preferences?.reminder_days_before ?? 3}
                                onChange={(e) => handleSelectChange("reminder_days_before", parseInt(e.target.value))}
                                disabled={!preferences?.reminder_enabled}
                                className="px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white border-0 focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                              >
                                {REMINDER_DAYS.map((days) => (
                                  <option key={days} value={days}>
                                    {days} {days === 1 ? "day" : "days"}
                                  </option>
                                ))}
                              </select>
                            </div>

                            <SettingToggle
                              label="Overdue alerts"
                              description="Get notified about missed payments"
                              checked={preferences?.overdue_alerts ?? true}
                              onChange={() => handleToggle("overdue_alerts" as keyof NotificationPreferences)}
                              disabled={updatePrefsMutation.isPending || !preferences?.reminder_enabled}
                            />
                          </div>
                        </section>

                        {/* Digest Settings */}
                        <section>
                          <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-4">
                            Digests
                          </h3>

                          <div className="space-y-4">
                            <SettingToggle
                              label="Daily digest"
                              description="Receive a summary of today's and upcoming payments"
                              checked={preferences?.daily_digest ?? false}
                              onChange={() => handleToggle("daily_digest" as keyof NotificationPreferences)}
                              disabled={updatePrefsMutation.isPending}
                            />

                            <SettingToggle
                              label="Weekly digest"
                              description="Receive a weekly payment summary"
                              checked={preferences?.weekly_digest ?? true}
                              onChange={() => handleToggle("weekly_digest" as keyof NotificationPreferences)}
                              disabled={updatePrefsMutation.isPending}
                            />

                            {preferences?.weekly_digest && (
                              <div className="flex items-center justify-between py-2 pl-4">
                                <p className="text-sm text-gray-600 dark:text-gray-400">
                                  Send on
                                </p>
                                <select
                                  value={preferences?.weekly_digest_day ?? 0}
                                  onChange={(e) => handleSelectChange("weekly_digest_day", parseInt(e.target.value))}
                                  className="px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white border-0 focus:ring-2 focus:ring-indigo-500"
                                >
                                  {WEEKDAYS.map((day) => (
                                    <option key={day.value} value={day.value}>
                                      {day.label}
                                    </option>
                                  ))}
                                </select>
                              </div>
                            )}
                          </div>
                        </section>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

interface SettingToggleProps {
  label: string;
  description: string;
  checked: boolean;
  onChange: () => void;
  disabled?: boolean;
}

function SettingToggle({ label, description, checked, onChange, disabled }: SettingToggleProps) {
  return (
    <div className="flex items-center justify-between py-2">
      <div>
        <p className="font-medium text-gray-900 dark:text-white">{label}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
      </div>
      <button
        role="switch"
        aria-checked={checked}
        onClick={onChange}
        disabled={disabled}
        className={cn(
          "relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed",
          checked ? "bg-indigo-600" : "bg-gray-200 dark:bg-gray-700"
        )}
      >
        <span
          className={cn(
            "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
            checked ? "translate-x-6" : "translate-x-1"
          )}
        />
      </button>
    </div>
  );
}
