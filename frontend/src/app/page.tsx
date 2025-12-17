"use client";

import { useState, useEffect, useMemo } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { SubscriptionList } from "@/components/SubscriptionList";
import { AgentChat } from "@/components/AgentChat";
import { StatsPanel } from "@/components/StatsPanel";
import { Header } from "@/components/Header";
import { PaymentCalendar } from "@/components/PaymentCalendar";
import { CardsDashboard } from "@/components/CardsDashboard";
import { Bot, CreditCard, Calendar, Sparkles, Wallet } from "lucide-react";
import { cn } from "@/lib/utils";

type ViewType = "list" | "calendar" | "cards" | "agent";
const VALID_VIEWS: ViewType[] = ["list", "calendar", "cards", "agent"];

const viewConfig = {
  list: {
    icon: CreditCard,
    label: "Payments",
    gradient: "from-blue-500 to-indigo-500",
  },
  calendar: {
    icon: Calendar,
    label: "Calendar",
    gradient: "from-purple-500 to-pink-500",
  },
  cards: {
    icon: Wallet,
    label: "Cards",
    gradient: "from-indigo-500 to-purple-500",
  },
  agent: {
    icon: Bot,
    label: "AI Assistant",
    gradient: "from-emerald-500 to-teal-500",
  },
} as const;

export default function Home() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Get initial view from URL params (computed once, no effect needed)
  const initialView = useMemo(() => {
    const viewParam = searchParams.get("view") as ViewType | null;
    return viewParam && VALID_VIEWS.includes(viewParam) ? viewParam : "list";
  }, []);

  const [view, setView] = useState<ViewType>(initialView);

  // Sync view state when URL changes (e.g., browser back/forward)
  useEffect(() => {
    const viewParam = searchParams.get("view") as ViewType | null;
    const newView = viewParam && VALID_VIEWS.includes(viewParam) ? viewParam : "list";
    if (newView !== view) {
      setView(newView);
    }
  }, [searchParams]);

  // Update URL when view changes (only if not from URL)
  const handleViewChange = (newView: ViewType) => {
    setView(newView);
    // Clear filter when switching away from list view
    if (newView !== "list") {
      router.push(`/?view=${newView}`, { scroll: false });
    } else {
      router.push(`/?view=${newView}`, { scroll: false });
    }
  };

  // Get filter from URL for SubscriptionList
  const filterParam = searchParams.get("filter");

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Animated mesh gradient background */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 gradient-mesh" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/50 to-white dark:via-gray-900/50 dark:to-gray-900" />

        {/* Floating orbs for visual interest */}
        <motion.div
          className="absolute top-20 left-10 w-72 h-72 rounded-full opacity-30"
          style={{
            background: "radial-gradient(circle, oklch(0.7 0.15 250) 0%, transparent 70%)",
          }}
          animate={{
            y: [0, -20, 0],
            scale: [1, 1.05, 1],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute bottom-40 right-20 w-96 h-96 rounded-full opacity-20"
          style={{
            background: "radial-gradient(circle, oklch(0.7 0.18 300) 0%, transparent 70%)",
          }}
          animate={{
            y: [0, 20, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 1,
          }}
        />
      </div>

      <Header />

      <main id="main-content" className="container mx-auto px-4 py-8 max-w-7xl relative z-10" role="main" tabIndex={-1}>
        {/* Stats Panel with entrance animation */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <StatsPanel />
        </motion.div>

        {/* View Toggle - Glass morphism style with mobile scroll */}
        <motion.nav
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="flex gap-2 mb-6 sm:mb-8 p-1.5 glass-card rounded-2xl w-full sm:w-fit overflow-x-auto scrollbar-hide"
          role="tablist"
          aria-label="View options"
        >
          {(Object.keys(viewConfig) as ViewType[]).map((viewKey) => {
            const config = viewConfig[viewKey];
            const Icon = config.icon;
            const isActive = view === viewKey;

            return (
              <motion.button
                key={viewKey}
                onClick={() => handleViewChange(viewKey)}
                className={cn(
                  "relative flex items-center gap-1.5 sm:gap-2 px-3 sm:px-5 py-2 sm:py-2.5 rounded-xl transition-all duration-300 whitespace-nowrap shrink-0",
                  isActive
                    ? "text-white"
                    : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-white/50 dark:hover:bg-white/10"
                )}
                whileHover={{ scale: isActive ? 1 : 1.02 }}
                whileTap={{ scale: 0.98 }}
                role="tab"
                aria-selected={isActive}
                aria-controls={`${viewKey}-panel`}
                tabIndex={isActive ? 0 : -1}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className={cn(
                      "absolute inset-0 rounded-xl bg-gradient-to-r shadow-lg",
                      config.gradient
                    )}
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <Icon className="w-4 h-4 relative z-10" />
                <span className="font-medium relative z-10 text-sm sm:text-base">{config.label}</span>
                {viewKey === "agent" && (
                  <Sparkles className="w-3 h-3 relative z-10 opacity-75 hidden sm:block" />
                )}
              </motion.button>
            );
          })}
        </motion.nav>

        {/* Content with smooth transitions */}
        <AnimatePresence mode="wait">
          <motion.div
            key={view}
            initial={{ opacity: 0, y: 20, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.98 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            role="tabpanel"
            id={`${view}-panel`}
            aria-labelledby={`${view}-tab`}
          >
            {view === "list" && <SubscriptionList initialFilter={filterParam} />}
            {view === "calendar" && <PaymentCalendar />}
            {view === "cards" && <CardsDashboard />}
            {view === "agent" && <AgentChat />}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Decorative bottom gradient */}
      <div className="fixed bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-white dark:from-gray-900 to-transparent pointer-events-none z-0" />
    </div>
  );
}
