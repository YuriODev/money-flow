"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  User,
  Bell,
  CreditCard,
  Settings,
  Shield,
  HelpCircle,
  FolderOpen,
} from "lucide-react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ProfileSettings } from "@/components/settings/ProfileSettings";
import { NotificationSettings } from "@/components/settings/NotificationSettings";
import { PreferencesSettings } from "@/components/settings/PreferencesSettings";
import CategoriesSettings from "@/components/settings/CategoriesSettings";

type SettingsTab = "profile" | "preferences" | "notifications" | "categories" | "cards" | "security" | "help";

const tabs: { id: SettingsTab; label: string; icon: React.ReactNode; available: boolean }[] = [
  { id: "profile", label: "Profile", icon: <User className="w-5 h-5" />, available: true },
  { id: "preferences", label: "Preferences", icon: <Settings className="w-5 h-5" />, available: true },
  { id: "notifications", label: "Notifications", icon: <Bell className="w-5 h-5" />, available: true },
  { id: "categories", label: "Categories", icon: <FolderOpen className="w-5 h-5" />, available: true },
  { id: "cards", label: "Payment Cards", icon: <CreditCard className="w-5 h-5" />, available: false },
  { id: "security", label: "Security", icon: <Shield className="w-5 h-5" />, available: false },
  { id: "help", label: "Help & Support", icon: <HelpCircle className="w-5 h-5" />, available: false },
];

function SettingsContent() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<SettingsTab>("profile");

  const renderTabContent = () => {
    switch (activeTab) {
      case "profile":
        return <ProfileSettings />;
      case "preferences":
        return <PreferencesSettings />;
      case "notifications":
        return <NotificationSettings />;
      case "categories":
        return (
          <div className="p-6">
            <CategoriesSettings />
          </div>
        );
      case "cards":
        return (
          <div className="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
            <p>Payment Cards settings coming soon...</p>
          </div>
        );
      case "security":
        return (
          <div className="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
            <p>Security settings coming soon...</p>
          </div>
        );
      case "help":
        return (
          <div className="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
            <p>Help & Support coming soon...</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4 h-16">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => router.push("/")}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="hidden sm:inline">Back to Dashboard</span>
            </motion.button>
            <div className="h-6 w-px bg-gray-200 dark:bg-gray-700" />
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Settings</h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <aside className="lg:w-64 shrink-0">
            <nav className="space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => tab.available && setActiveTab(tab.id)}
                  disabled={!tab.available}
                  className={`
                    w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all
                    ${activeTab === tab.id
                      ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/25"
                      : tab.available
                        ? "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                        : "text-gray-400 dark:text-gray-600 cursor-not-allowed opacity-50"
                    }
                  `}
                >
                  {tab.icon}
                  <span className="font-medium">{tab.label}</span>
                  {!tab.available && (
                    <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
                      Soon
                    </span>
                  )}
                </button>
              ))}
            </nav>
          </aside>

          {/* Content Area */}
          <main className="flex-1 min-w-0">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className="bg-white dark:bg-gray-900 rounded-2xl shadow-xl shadow-gray-200/50 dark:shadow-none border border-gray-200 dark:border-gray-800 overflow-hidden"
            >
              {renderTabContent()}
            </motion.div>
          </main>
        </div>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <ProtectedRoute>
      <SettingsContent />
    </ProtectedRoute>
  );
}
