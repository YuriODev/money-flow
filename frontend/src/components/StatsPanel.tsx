"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { subscriptionApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useCurrencyFormat } from "@/hooks/useCurrencyFormat";
import {
  Coins,
  TrendingUp,
  CreditCard,
  ArrowUpRight,
  ArrowDownRight,
  PiggyBank,
  Target,
} from "lucide-react";

const cardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      delay: i * 0.1,
      type: "spring" as const,
      stiffness: 300,
      damping: 24,
    },
  }),
};

export function StatsPanel() {
  const { format } = useCurrencyFormat();
  const { data: summary, isLoading } = useQuery({
    queryKey: ["summary"],
    queryFn: () => subscriptionApi.getSummary(),
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {[1, 2, 3].map((i) => (
          <div key={i} className="glass-card rounded-2xl p-6 overflow-hidden">
            <div className="flex justify-between items-start">
              <div className="space-y-3">
                <div className="h-4 w-24 shimmer rounded-lg" />
                <div className="h-8 w-32 shimmer rounded-lg" />
              </div>
              <div className="w-12 h-12 shimmer rounded-xl" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Use the currency from the API response (defaults to GBP)
  const sourceCurrency = summary?.currency || "GBP";

  // Check if we have debt or savings data to show additional cards
  const hasDebt = (summary?.total_debt || 0) > 0;
  const hasSavings = (summary?.total_savings_target || 0) > 0;

  const stats = [
    {
      label: "Monthly Spending",
      value: format(summary?.total_monthly || 0, sourceCurrency),
      icon: Coins,
      gradient: "from-blue-500 to-cyan-500",
      bgGradient: "from-blue-50 to-cyan-50",
      borderColor: "border-blue-100",
      textColor: "text-blue-700",
      trend: null,
    },
    {
      label: "Yearly Total",
      value: format(summary?.total_yearly || 0, sourceCurrency),
      icon: TrendingUp,
      gradient: "from-purple-500 to-pink-500",
      bgGradient: "from-purple-50 to-pink-50",
      borderColor: "border-purple-100",
      textColor: "text-purple-700",
      trend: null,
    },
    {
      label: "Active Payments",
      value: String(summary?.active_count || 0),
      icon: CreditCard,
      gradient: "from-emerald-500 to-teal-500",
      bgGradient: "from-emerald-50 to-teal-50",
      borderColor: "border-emerald-100",
      textColor: "text-emerald-700",
      trend: null,
    },
    // Show debt card only if there's debt
    ...(hasDebt
      ? [
          {
            label: "Total Debt",
            value: format(summary?.total_debt || 0, sourceCurrency),
            icon: Target,
            gradient: "from-red-500 to-rose-500",
            bgGradient: "from-red-50 to-rose-50",
            borderColor: "border-red-100",
            textColor: "text-red-700",
            trend: null,
          },
        ]
      : []),
    // Show savings card only if there's a savings goal
    ...(hasSavings
      ? [
          {
            label: "Savings Progress",
            value: `${format(summary?.total_current_saved || 0, sourceCurrency)} / ${format(summary?.total_savings_target || 0, sourceCurrency)}`,
            icon: PiggyBank,
            gradient: "from-green-500 to-emerald-500",
            bgGradient: "from-green-50 to-emerald-50",
            borderColor: "border-green-100",
            textColor: "text-green-700",
            trend:
              summary?.total_savings_target && summary?.total_savings_target > 0
                ? {
                    value: Math.round(
                      ((summary?.total_current_saved || 0) /
                        summary.total_savings_target) *
                        100
                    ),
                    isUp: true,
                    label: "% saved",
                  }
                : null,
          },
        ]
      : []),
  ];

  // Dynamic grid columns based on number of stats
  const gridCols =
    stats.length <= 3
      ? "md:grid-cols-3"
      : stats.length === 4
        ? "md:grid-cols-2 lg:grid-cols-4"
        : "md:grid-cols-3 lg:grid-cols-5";

  return (
    <div className={cn("grid grid-cols-1 gap-6 mb-8", gridCols)}>
      {stats.map((stat, index) => (
        <motion.div
          key={stat.label}
          custom={index}
          variants={cardVariants}
          initial="hidden"
          animate="visible"
          whileHover={{ y: -4, transition: { duration: 0.2 } }}
          className={cn(
            "relative overflow-hidden glass-card rounded-2xl p-6 border",
            stat.borderColor
          )}
        >
          {/* Background gradient decoration */}
          <div
            className={cn(
              "absolute -right-8 -top-8 w-32 h-32 rounded-full opacity-20 blur-2xl",
              `bg-gradient-to-br ${stat.gradient}`
            )}
          />

          <div className="relative">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-sm font-medium text-gray-500 mb-1">{stat.label}</p>
                <motion.p
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2 + index * 0.1 }}
                  className={cn(
                    stat.label === "Savings Progress" ? "text-xl" : "text-3xl",
                    "font-bold",
                    stat.textColor
                  )}
                >
                  {stat.value}
                </motion.p>
              </div>

              <motion.div
                whileHover={{ scale: 1.1, rotate: 5 }}
                className={cn(
                  "w-12 h-12 rounded-xl flex items-center justify-center shadow-lg",
                  `bg-gradient-to-br ${stat.gradient}`
                )}
              >
                <stat.icon className="w-6 h-6 text-white" />
              </motion.div>
            </div>

            {/* Trend indicator - only show if trend exists */}
            {stat.trend && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + index * 0.1 }}
                className={cn(
                  "inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium",
                  stat.trend.isUp
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-red-100 text-red-700"
                )}
              >
                {stat.trend.isUp ? (
                  <ArrowUpRight className="w-3 h-3" />
                ) : (
                  <ArrowDownRight className="w-3 h-3" />
                )}
                {stat.trend.value}{(stat.trend as any).label || "% vs last month"}
              </motion.div>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
