"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { User, Mail, Save, Loader2, Check } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export function ProfileSettings() {
  const { user } = useAuth();
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    // Simulate save - actual implementation would call API
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Profile</h2>
        <p className="mt-1 text-gray-500 dark:text-gray-400">
          Manage your account information
        </p>
      </div>

      {/* Profile Picture */}
      <div className="flex items-center gap-6 mb-8 pb-8 border-b border-gray-200 dark:border-gray-800">
        <div className="relative">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
            <User className="w-10 h-10 text-white" />
          </div>
          <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-2 border-white dark:border-gray-900" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {user?.full_name || "User"}
          </h3>
          <p className="text-gray-500 dark:text-gray-400">{user?.email}</p>
        </div>
      </div>

      {/* Form */}
      <div className="space-y-6">
        {/* Email Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Email Address
          </label>
          <div className="relative">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="email"
              value={user?.email || ""}
              readOnly
              className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all cursor-not-allowed"
            />
          </div>
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Email cannot be changed
          </p>
        </div>

        {/* Full Name Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Full Name
          </label>
          <div className="relative">
            <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              defaultValue={user?.full_name || ""}
              placeholder="Enter your full name"
              className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>
        </div>

        {/* Save Button */}
        <div className="pt-4">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSave}
            disabled={isSaving}
            className={`
              flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-medium transition-all
              ${saved
                ? "bg-green-500 text-white"
                : "bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:shadow-lg hover:shadow-blue-500/25"
              }
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
          >
            {isSaving ? (
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
                Save Changes
              </>
            )}
          </motion.button>
        </div>
      </div>

      {/* Coming Soon Features */}
      <div className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-800">
        <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
          Coming Soon
        </h3>
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
            <p className="font-medium text-gray-700 dark:text-gray-300">Change Password</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Update your password securely</p>
          </div>
          <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
            <p className="font-medium text-gray-700 dark:text-gray-300">Delete Account</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">Permanently remove your data</p>
          </div>
        </div>
      </div>
    </div>
  );
}
