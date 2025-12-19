"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  subscriptionApi,
  categoriesApi,
  type Subscription,
  type PaymentType,
  type PaymentMode,
  type Category as _Category,
  PAYMENT_MODE_LABELS,
} from "@/lib/api";
import { formatDate, getFrequencyLabel, cn } from "@/lib/utils";
import { useCurrencyFormat } from "@/hooks/useCurrencyFormat";
import {
  Trash2,
  Calendar,
  CreditCard,
  Clock,
  Repeat,
  Plus,
  Sparkles,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Pencil,
  Home,
  Zap,
  Briefcase,
  Shield,
  PiggyBank,
  ArrowRightLeft,
  Tv,
  LayoutGrid,
  CircleDot,
  FolderOpen,
  Layers,
  type LucideIcon,
} from "lucide-react";
import React, { useState, useMemo, useEffect, useCallback, useRef, KeyboardEvent } from "react";

// All payment modes for filter tabs (including special "no_card" filter)
const ALL_PAYMENT_MODES: (PaymentMode | "all" | "no_card")[] = [
  "all",
  "recurring",
  "one_time",
  "debt",
  "savings",
  "no_card",
];

// Lucide icon components for each payment mode
const PAYMENT_MODE_ICON_COMPONENTS: Record<PaymentMode | "all" | "no_card", LucideIcon> = {
  all: LayoutGrid,
  recurring: Repeat,
  one_time: CircleDot,
  debt: CreditCard,
  savings: PiggyBank,
  no_card: AlertCircle,
};

// Keep old payment type icons for backwards compatibility (prefixed to silence unused warning)
const _PAYMENT_TYPE_ICON_COMPONENTS: Record<PaymentType | "all" | "no_card", LucideIcon> = {
  all: LayoutGrid,
  subscription: Tv,
  housing: Home,
  utility: Zap,
  professional_service: Briefcase,
  insurance: Shield,
  debt: CreditCard,
  savings: PiggyBank,
  transfer: ArrowRightLeft,
  one_time: CircleDot,
  no_card: AlertCircle,
};
import { AddSubscriptionModal } from "./AddSubscriptionModal";
import { EditSubscriptionModal } from "./EditSubscriptionModal";
import { findService, getIconUrl, CATEGORY_INFO } from "@/lib/service-icons";
import { toast } from "@/components/Toast";

// Stagger animation for list items
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: "spring" as const,
      stiffness: 300,
      damping: 24,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.9,
    y: -10,
    transition: { duration: 0.2 },
  },
};

// Status badge component with modern styling
function StatusBadge({ status, daysUntil }: { status: string; daysUntil: number }) {
  // Determine the label based on days until payment
  const getDaysLabel = (days: number) => {
    if (days === 0) return "Due today";
    if (days === 1) return "Tomorrow";
    if (days === -1) return "Yesterday";
    if (days < 0) return `${Math.abs(days)} days ago`;
    return `${days} days`;
  };

  const statusConfig: Record<
    string,
    { bg: string; text: string; label: string; icon: typeof CheckCircle2 }
  > = {
    overdue: {
      bg: "bg-gradient-to-r from-red-500/10 to-rose-500/10 border-red-200 dark:border-red-800",
      text: "text-red-600 dark:text-red-400",
      label: getDaysLabel(daysUntil),
      icon: AlertCircle,
    },
    due_soon: {
      bg: "bg-gradient-to-r from-amber-500/10 to-yellow-500/10 border-amber-200 dark:border-amber-800",
      text: "text-amber-600 dark:text-amber-400",
      label: getDaysLabel(daysUntil),
      icon: Clock,
    },
    upcoming: {
      bg: "bg-gradient-to-r from-blue-500/10 to-indigo-500/10 border-blue-200 dark:border-blue-800",
      text: "text-blue-600 dark:text-blue-400",
      label: getDaysLabel(daysUntil),
      icon: CheckCircle2,
    },
  };

  const config = statusConfig[status] || statusConfig.upcoming;
  const Icon = config.icon;

  return (
    <motion.span
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border",
        config.bg,
        config.text
      )}
    >
      <Icon className="w-3 h-3" />
      {config.label}
    </motion.span>
  );
}

// Category badge with colors
function CategoryBadge({ category }: { category: string }) {
  const categoryKey = category.toLowerCase();
  const categoryInfo = CATEGORY_INFO[categoryKey];

  // Default colors if category not found
  const bgColor = categoryInfo?.color || "#6B7280";
  const label = categoryInfo?.label || category;

  return (
    <span
      className="text-xs px-2 py-0.5 rounded-full font-medium"
      style={{
        backgroundColor: `${bgColor}15`,
        color: bgColor,
      }}
    >
      {label}
    </span>
  );
}

// Modern installment progress component
function InstallmentProgress({
  completed,
  total,
}: {
  completed: number;
  total: number;
}) {
  const percentage = (completed / total) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      className="mt-4 p-4 glass-card-subtle rounded-xl"
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-purple-700 dark:text-purple-400 flex items-center gap-1.5">
          <Repeat className="w-3.5 h-3.5" />
          Installment Plan
        </span>
        <span className="text-xs font-medium text-purple-600 dark:text-purple-400 bg-purple-100 dark:bg-purple-900/50 px-2 py-0.5 rounded-full">
          {completed}/{total}
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-purple-100 dark:bg-purple-900/50 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
          className="h-full bg-gradient-to-r from-purple-500 via-indigo-500 to-violet-500 rounded-full"
        />
      </div>

      <div className="flex justify-between mt-2">
        <p className="text-xs text-purple-500 dark:text-purple-400">
          {total - completed} remaining
        </p>
        <p className="text-xs font-medium text-purple-600 dark:text-purple-400">
          {Math.round(percentage)}%
        </p>
      </div>
    </motion.div>
  );
}

// Skeleton loader with shimmer effect
function SubscriptionSkeleton() {
  return (
    <div className="glass-card rounded-2xl p-6 overflow-hidden">
      <div className="flex gap-4">
        <div className="w-12 h-12 rounded-xl shimmer" />
        <div className="flex-1 space-y-3">
          <div className="h-5 w-32 shimmer rounded-lg" />
          <div className="h-4 w-24 shimmer rounded-lg" />
        </div>
      </div>
      <div className="mt-4 space-y-2">
        <div className="h-8 w-28 shimmer rounded-lg" />
        <div className="h-4 w-full shimmer rounded-lg" />
      </div>
    </div>
  );
}

// Main subscription card component
function SubscriptionCard({
  subscription,
  onDelete,
  onEdit,
  isDeleting,
}: {
  subscription: Subscription;
  onDelete: () => void;
  onEdit: () => void;
  isDeleting: boolean;
}) {
  const { format } = useCurrencyFormat();
  const [iconError, setIconError] = useState(false);

  // Try to find service icon from library
  const serviceInfo = useMemo(() => {
    return findService(subscription.name);
  }, [subscription.name]);

  // Reset icon error when subscription changes
  useEffect(() => {
    setIconError(false);
  }, [subscription.id]);

  // Use service color if available, otherwise subscription color
  const displayColor = serviceInfo?.color || subscription.color;

  // Get icon URL - prefer custom iconUrl, then SimpleIcons, then subscription icon_url
  const iconUrl = useMemo(() => {
    if (serviceInfo) {
      // Use custom iconUrl if available (e.g., Brandfetch)
      if (serviceInfo.iconUrl) {
        return serviceInfo.iconUrl;
      }
      // Use SimpleIcons if icon slug exists - pass the service color for proper coloring
      if (serviceInfo.icon) {
        return getIconUrl(serviceInfo.icon, serviceInfo.color);
      }
    }
    return subscription.icon_url;
  }, [serviceInfo, subscription.icon_url]);

  return (
    <motion.article
      variants={itemVariants}
      className="group relative"
      aria-label={`${subscription.name} - ${format(subscription.amount, subscription.currency)} ${getFrequencyLabel(subscription.frequency, subscription.frequency_interval)}`}
    >

      {/* Card content */}
      <div
        className={cn(
          "relative glass-card rounded-2xl overflow-hidden transition-all duration-300",
          "border-l-4 hover:shadow-xl dark:hover:shadow-2xl dark:hover:shadow-black/30"
        )}
        style={{ borderLeftColor: displayColor }}
      >
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-start mb-4">
            <div className="flex items-center gap-3">
              {/* Icon/Avatar */}
              <div className="relative transition-transform duration-200 hover:scale-105">
                {iconUrl && !iconError ? (
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center shadow-lg bg-white/80 dark:bg-white/90"
                  >
                    <img
                      src={iconUrl}
                      alt={subscription.name}
                      className="w-7 h-7"
                      onError={() => setIconError(true)}
                    />
                  </div>
                ) : (
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-lg"
                    style={{
                      background: `linear-gradient(135deg, ${displayColor} 0%, ${displayColor}cc 100%)`,
                    }}
                  >
                    {subscription.name.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 group-hover:text-gray-800 dark:group-hover:text-gray-200 transition-colors">
                  {subscription.name}
                </h3>
                {/* Use service library category if available, otherwise database category */}
                {(serviceInfo?.category || subscription.category) && (
                  <CategoryBadge category={serviceInfo?.category || subscription.category || ""} />
                )}
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-1" role="group" aria-label="Payment actions">
              {/* Edit button */}
              <button
                onClick={onEdit}
                className="p-2 rounded-xl transition-all duration-200 text-gray-400 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/30 hover:scale-110 active:scale-95"
                aria-label={`Edit ${subscription.name}`}
              >
                <Pencil className="w-4 h-4" aria-hidden="true" />
              </button>

              {/* Delete button */}
              <button
                onClick={onDelete}
                disabled={isDeleting}
                className={cn(
                  "p-2 rounded-xl transition-all duration-200 hover:scale-110 active:scale-95",
                  "text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30",
                  isDeleting && "opacity-50 cursor-not-allowed"
                )}
                aria-label={`Delete ${subscription.name}`}
              >
                <Trash2 className="w-4 h-4" aria-hidden="true" />
              </button>
            </div>
          </div>

          {/* Amount with gradient text */}
          <div className="flex items-baseline gap-2 mb-4">
            <motion.span
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              className="text-3xl font-bold"
              style={{
                background: `linear-gradient(135deg, ${displayColor} 0%, ${displayColor}aa 100%)`,
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              {format(subscription.amount, subscription.currency)}
            </motion.span>
            <span className="text-sm text-gray-500 dark:text-gray-400 font-medium">
              / {getFrequencyLabel(subscription.frequency, subscription.frequency_interval)}
            </span>
          </div>

          {/* Payment info grid */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <div className="p-1.5 bg-gray-100 dark:bg-gray-800 rounded-lg">
                  <Calendar className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                </div>
                <span className="font-medium">{formatDate(subscription.next_payment_date)}</span>
              </div>
              <StatusBadge
                status={subscription.payment_status_label}
                daysUntil={subscription.days_until_payment}
              />
            </div>

            {subscription.payment_method && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400"
              >
                <div className="p-1.5 bg-gray-100 dark:bg-gray-800 rounded-lg">
                  <CreditCard className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                </div>
                <span>{subscription.payment_method}</span>
              </motion.div>
            )}

            {!subscription.auto_renew && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.15 }}
                className="flex items-center gap-2 text-xs"
              >
                <div className="p-1 bg-amber-100 dark:bg-amber-900/50 rounded-lg">
                  <Clock className="w-3 h-3 text-amber-600 dark:text-amber-400" />
                </div>
                <span className="text-amber-600 dark:text-amber-400 font-medium">Manual renewal</span>
              </motion.div>
            )}
          </div>

          {/* Installment Progress */}
          {subscription.is_installment && subscription.total_installments && (
            <InstallmentProgress
              completed={subscription.completed_installments}
              total={subscription.total_installments}
            />
          )}

          {/* Notes */}
          {subscription.notes && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-sm text-gray-500 dark:text-gray-400 mt-4 line-clamp-2 italic border-t border-gray-100 dark:border-gray-700 pt-3"
            >
              "{subscription.notes}"
            </motion.p>
          )}
        </div>

        {/* Bottom accent line - using CSS group-hover for smooth transition */}
        <div
          className="h-0.5 origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-300"
          style={{
            background: `linear-gradient(90deg, ${displayColor} 0%, transparent 100%)`,
          }}
          aria-hidden="true"
        />
      </div>
    </motion.article>
  );
}

// Empty state component
function EmptyState({ onAdd }: { onAdd: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-card rounded-3xl p-12 text-center"
    >
      <motion.div
        animate={{
          y: [0, -10, 0],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center shadow-lg"
      >
        <Sparkles className="w-10 h-10 text-white" />
      </motion.div>

      <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">No subscriptions yet</h3>
      <p className="text-gray-500 dark:text-gray-400 mb-6 max-w-sm mx-auto">
        Start tracking your recurring payments to get insights into your spending
      </p>

      <motion.button
        onClick={onAdd}
        whileHover={{ scale: 1.02, y: -2 }}
        whileTap={{ scale: 0.98 }}
        className="btn-primary inline-flex items-center gap-2"
      >
        <Plus className="w-5 h-5" />
        Add Your First Subscription
      </motion.button>
    </motion.div>
  );
}

interface SubscriptionListProps {
  initialFilter?: string | null;
}

// Filter type: either by payment mode or by category
type FilterType = "mode" | "category";

export function SubscriptionList({ initialFilter }: SubscriptionListProps) {
  const queryClient = useQueryClient();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingSubscription, setEditingSubscription] = useState<Subscription | null>(null);
  const [filterType, setFilterType] = useState<FilterType>("mode");
  const [selectedPaymentMode, setSelectedPaymentMode] = useState<PaymentMode | "all" | "no_card">(
    initialFilter === "no_card" ? "no_card" : "all"
  );
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | "all" | "uncategorized">("all");
  const filterTabsRef = useRef<HTMLDivElement>(null);

  // Update filter when initialFilter changes (from URL)
  useEffect(() => {
    if (initialFilter === "no_card") {
      setSelectedPaymentMode("no_card");
      setFilterType("mode");
    }
  }, [initialFilter]);

  const { data: subscriptions, isLoading } = useQuery({
    queryKey: ["subscriptions"],
    queryFn: () => subscriptionApi.getAll(),
  });

  // Fetch categories for category filtering
  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: () => categoriesApi.getAll(),
  });

  // Filter subscriptions by payment mode or category
  const filteredSubscriptions = useMemo(() => {
    if (!subscriptions) return [];
    const active = subscriptions.filter((s: Subscription) => s.is_active);

    if (filterType === "mode") {
      if (selectedPaymentMode === "all") return active;
      if (selectedPaymentMode === "no_card") return active.filter((s: Subscription) => !s.card_id);
      return active.filter((s: Subscription) => s.payment_mode === selectedPaymentMode);
    } else {
      // Filter by category
      if (selectedCategoryId === "all") return active;
      if (selectedCategoryId === "uncategorized") return active.filter((s: Subscription) => !s.category_id);
      return active.filter((s: Subscription) => s.category_id === selectedCategoryId);
    }
  }, [subscriptions, filterType, selectedPaymentMode, selectedCategoryId]);

  // Count subscriptions by payment mode for badges
  const paymentModeCounts = useMemo(() => {
    if (!subscriptions) return {};
    const active = subscriptions.filter((s: Subscription) => s.is_active);
    const counts: Record<string, number> = { all: active.length };
    for (const mode of Object.keys(PAYMENT_MODE_LABELS)) {
      counts[mode] = active.filter((s: Subscription) => s.payment_mode === mode).length;
    }
    // Count subscriptions without a card assigned
    counts["no_card"] = active.filter((s: Subscription) => !s.card_id).length;
    return counts;
  }, [subscriptions]);

  // Count subscriptions by category for badges
  const categoryCounts = useMemo(() => {
    if (!subscriptions) return {};
    const active = subscriptions.filter((s: Subscription) => s.is_active);
    const counts: Record<string, number> = { all: active.length };
    // Count uncategorized
    counts["uncategorized"] = active.filter((s: Subscription) => !s.category_id).length;
    // Count by each category
    for (const cat of categories) {
      counts[cat.id] = active.filter((s: Subscription) => s.category_id === cat.id).length;
    }
    return counts;
  }, [subscriptions, categories]);

  // Get visible tabs for keyboard navigation (depends on filter type)
  const visibleTabs = useMemo(() => {
    return ALL_PAYMENT_MODES.filter(
      (mode) => mode === "all" || (paymentModeCounts[mode] || 0) > 0
    );
  }, [paymentModeCounts]);

  // Get visible category tabs (prefixed for future use)
  const _visibleCategoryTabs = useMemo(() => {
    const tabs: (string | "all" | "uncategorized")[] = ["all"];
    // Add categories that have subscriptions
    for (const cat of categories) {
      if ((categoryCounts[cat.id] || 0) > 0) {
        tabs.push(cat.id);
      }
    }
    // Add uncategorized if there are any
    if ((categoryCounts["uncategorized"] || 0) > 0) {
      tabs.push("uncategorized");
    }
    return tabs;
  }, [categories, categoryCounts]);

  // Keyboard navigation for filter tabs
  const handleFilterKeyDown = useCallback(
    (e: KeyboardEvent<HTMLButtonElement>, currentMode: PaymentMode | "all" | "no_card") => {
      const currentIndex = visibleTabs.indexOf(currentMode);
      let nextIndex = currentIndex;

      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        nextIndex = (currentIndex + 1) % visibleTabs.length;
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        nextIndex = (currentIndex - 1 + visibleTabs.length) % visibleTabs.length;
      } else if (e.key === "Home") {
        e.preventDefault();
        nextIndex = 0;
      } else if (e.key === "End") {
        e.preventDefault();
        nextIndex = visibleTabs.length - 1;
      }

      if (nextIndex !== currentIndex) {
        const nextMode = visibleTabs[nextIndex];
        setSelectedPaymentMode(nextMode);
        // Focus the new tab
        const buttons = filterTabsRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]');
        buttons?.[nextIndex]?.focus();
      }
    },
    [visibleTabs]
  );

  const deleteMutation = useMutation({
    mutationFn: (id: string) => subscriptionApi.delete(id),
    // Optimistic update - immediately remove from UI
    onMutate: async (deletedId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["subscriptions"] });

      // Snapshot previous value
      const previousSubscriptions = queryClient.getQueryData<Subscription[]>(["subscriptions"]);

      // Optimistically update by removing the item
      queryClient.setQueryData<Subscription[]>(["subscriptions"], (old) =>
        old?.filter((sub) => sub.id !== deletedId) ?? []
      );

      // Return context with snapshot
      return { previousSubscriptions };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["summary"] });
      queryClient.invalidateQueries({ queryKey: ["calendar-events"] });
      toast.success("Payment deleted", "The payment has been removed from your list.");
    },
    onError: (_err, _deletedId, context) => {
      // Rollback on error
      if (context?.previousSubscriptions) {
        queryClient.setQueryData(["subscriptions"], context.previousSubscriptions);
      }
      toast.error("Failed to delete", "There was an error deleting the payment. Please try again.");
    },
    onSettled: () => {
      // Always refetch after error or success to ensure sync
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
    },
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <SubscriptionSkeleton />
          </motion.div>
        ))}
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4 sm:space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-4"
        >
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="p-2 sm:p-2.5 rounded-lg sm:rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500">
              <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">Your Payments</h2>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                {filteredSubscriptions.length} active payment{filteredSubscriptions.length !== 1 ? "s" : ""}
                {filterType === "mode" && selectedPaymentMode !== "all" && (
                  <span className="hidden sm:inline"> ({selectedPaymentMode === "no_card" ? "No Card Assigned" : PAYMENT_MODE_LABELS[selectedPaymentMode]})</span>
                )}
                {filterType === "category" && selectedCategoryId !== "all" && (
                  <span className="hidden sm:inline"> ({selectedCategoryId === "uncategorized" ? "Uncategorized" : categories.find(c => c.id === selectedCategoryId)?.name || ""})</span>
                )}
              </p>
            </div>
          </div>

          <motion.button
            onClick={() => setIsAddModalOpen(true)}
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
            className="btn-primary flex items-center gap-2 text-sm sm:text-base px-3 sm:px-4 py-2"
          >
            <Plus className="w-4 h-4 sm:w-5 sm:h-5" />
            <span className="hidden xs:inline">Add Payment</span>
            <span className="xs:hidden">Add</span>
          </motion.button>
        </motion.div>

        {/* Filter Type Toggle + Filter Tabs */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="space-y-3"
        >
          {/* Filter Type Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Filter by:</span>
            <div className="flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5">
              <button
                onClick={() => setFilterType("mode")}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200",
                  filterType === "mode"
                    ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm"
                    : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                )}
              >
                <Layers className="w-3.5 h-3.5" />
                Mode
              </button>
              <button
                onClick={() => setFilterType("category")}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200",
                  filterType === "category"
                    ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm"
                    : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                )}
              >
                <FolderOpen className="w-3.5 h-3.5" />
                Category
              </button>
            </div>
          </div>

          {/* Filter Tabs - conditionally render based on filter type */}
          <div
            ref={filterTabsRef}
            className="flex gap-2 pb-2 overflow-x-auto scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0 sm:flex-wrap"
            role="tablist"
            aria-label={filterType === "mode" ? "Filter payments by mode" : "Filter payments by category"}
          >
            {filterType === "mode" ? (
              // Payment Mode Tabs
              <>
                {ALL_PAYMENT_MODES.map((mode) => {
                  const count = paymentModeCounts[mode] || 0;
                  const isSelected = selectedPaymentMode === mode;
                  const label = mode === "all" ? "All" : mode === "no_card" ? "No Card" : PAYMENT_MODE_LABELS[mode];
                  const IconComponent = PAYMENT_MODE_ICON_COMPONENTS[mode];

                  // Only show tabs with items (or "All")
                  if (mode !== "all" && count === 0) return null;

                  return (
                    <motion.button
                      key={mode}
                      onClick={() => setSelectedPaymentMode(mode)}
                      onKeyDown={(e) => handleFilterKeyDown(e, mode)}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className={cn(
                        "flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg sm:rounded-xl text-xs sm:text-sm font-medium transition-all duration-200 whitespace-nowrap shrink-0",
                        isSelected
                          ? mode === "no_card"
                            ? "bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg"
                            : "bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-lg"
                          : mode === "no_card"
                            ? "glass-card-subtle text-amber-600 dark:text-amber-400 hover:shadow-md border border-amber-200 dark:border-amber-800"
                            : "glass-card-subtle text-gray-600 dark:text-gray-400 hover:shadow-md"
                      )}
                      role="tab"
                      aria-selected={isSelected}
                      aria-controls="payments-list"
                      tabIndex={isSelected ? 0 : -1}
                    >
                      <IconComponent className="w-3.5 h-3.5 sm:w-4 sm:h-4" aria-hidden="true" />
                      <span>{label}</span>
                      <span
                        className={cn(
                          "ml-0.5 sm:ml-1 px-1.5 sm:px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-semibold",
                          isSelected
                            ? "bg-white/20 text-white"
                            : "bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
                        )}
                        aria-label={`${count} ${label === "All" ? "total" : label} payments`}
                      >
                        {count}
                      </span>
                    </motion.button>
                  );
                })}
              </>
            ) : (
              // Category Tabs
              <>
                {/* All tab */}
                <motion.button
                  key="all"
                  onClick={() => setSelectedCategoryId("all")}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={cn(
                    "flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg sm:rounded-xl text-xs sm:text-sm font-medium transition-all duration-200 whitespace-nowrap shrink-0",
                    selectedCategoryId === "all"
                      ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-lg"
                      : "glass-card-subtle text-gray-600 dark:text-gray-400 hover:shadow-md"
                  )}
                  role="tab"
                  aria-selected={selectedCategoryId === "all"}
                  aria-controls="payments-list"
                  tabIndex={selectedCategoryId === "all" ? 0 : -1}
                >
                  <LayoutGrid className="w-3.5 h-3.5 sm:w-4 sm:h-4" aria-hidden="true" />
                  <span>All</span>
                  <span
                    className={cn(
                      "ml-0.5 sm:ml-1 px-1.5 sm:px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-semibold",
                      selectedCategoryId === "all"
                        ? "bg-white/20 text-white"
                        : "bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
                    )}
                  >
                    {categoryCounts["all"] || 0}
                  </span>
                </motion.button>

                {/* Category tabs */}
                {categories.map((cat) => {
                  const count = categoryCounts[cat.id] || 0;
                  if (count === 0) return null;
                  const isSelected = selectedCategoryId === cat.id;

                  return (
                    <motion.button
                      key={cat.id}
                      onClick={() => setSelectedCategoryId(cat.id)}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className={cn(
                        "flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg sm:rounded-xl text-xs sm:text-sm font-medium transition-all duration-200 whitespace-nowrap shrink-0",
                        isSelected
                          ? "text-white shadow-lg"
                          : "glass-card-subtle hover:shadow-md"
                      )}
                      style={{
                        backgroundColor: isSelected ? cat.color : undefined,
                        color: isSelected ? "white" : cat.color,
                        borderColor: isSelected ? undefined : cat.color,
                        borderWidth: isSelected ? undefined : "1px",
                      }}
                      role="tab"
                      aria-selected={isSelected}
                      aria-controls="payments-list"
                      tabIndex={isSelected ? 0 : -1}
                    >
                      {cat.icon && <span aria-hidden="true">{cat.icon}</span>}
                      <span>{cat.name}</span>
                      <span
                        className={cn(
                          "ml-0.5 sm:ml-1 px-1.5 sm:px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-semibold",
                          isSelected
                            ? "bg-white/20 text-white"
                            : "bg-gray-200 dark:bg-gray-700"
                        )}
                        style={{ color: isSelected ? "white" : cat.color }}
                      >
                        {count}
                      </span>
                    </motion.button>
                  );
                })}

                {/* Uncategorized tab */}
                {(categoryCounts["uncategorized"] || 0) > 0 && (
                  <motion.button
                    key="uncategorized"
                    onClick={() => setSelectedCategoryId("uncategorized")}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={cn(
                      "flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg sm:rounded-xl text-xs sm:text-sm font-medium transition-all duration-200 whitespace-nowrap shrink-0",
                      selectedCategoryId === "uncategorized"
                        ? "bg-gradient-to-r from-gray-500 to-gray-600 text-white shadow-lg"
                        : "glass-card-subtle text-gray-500 dark:text-gray-400 hover:shadow-md border border-gray-300 dark:border-gray-600"
                    )}
                    role="tab"
                    aria-selected={selectedCategoryId === "uncategorized"}
                    aria-controls="payments-list"
                    tabIndex={selectedCategoryId === "uncategorized" ? 0 : -1}
                  >
                    <AlertCircle className="w-3.5 h-3.5 sm:w-4 sm:h-4" aria-hidden="true" />
                    <span>Uncategorized</span>
                    <span
                      className={cn(
                        "ml-0.5 sm:ml-1 px-1.5 sm:px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-semibold",
                        selectedCategoryId === "uncategorized"
                          ? "bg-white/20 text-white"
                          : "bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
                      )}
                    >
                      {categoryCounts["uncategorized"]}
                    </span>
                  </motion.button>
                )}
              </>
            )}
          </div>
        </motion.div>

        {/* Content */}
        <div id="payments-list" role="tabpanel" aria-label={`${selectedPaymentMode === "all" ? "All" : selectedPaymentMode === "no_card" ? "No Card Assigned" : PAYMENT_MODE_LABELS[selectedPaymentMode]} payments`}>
        {filteredSubscriptions.length === 0 ? (
          <EmptyState onAdd={() => setIsAddModalOpen(true)} />
        ) : (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6"
          >
            <AnimatePresence mode="popLayout">
              {filteredSubscriptions.map((subscription: Subscription) => (
                <SubscriptionCard
                  key={subscription.id}
                  subscription={subscription}
                  onDelete={() => deleteMutation.mutate(subscription.id)}
                  onEdit={() => setEditingSubscription(subscription)}
                  isDeleting={deleteMutation.isPending}
                />
              ))}
            </AnimatePresence>
          </motion.div>
        )}
        </div>
      </div>

      <AddSubscriptionModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
      />

      {editingSubscription && (
        <EditSubscriptionModal
          isOpen={!!editingSubscription}
          onClose={() => setEditingSubscription(null)}
          subscription={editingSubscription}
        />
      )}
    </>
  );
}
