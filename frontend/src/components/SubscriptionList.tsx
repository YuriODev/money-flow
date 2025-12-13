"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  subscriptionApi,
  type Subscription,
  type PaymentType,
  PAYMENT_TYPE_LABELS,
  PAYMENT_TYPE_ICONS,
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
  type LucideIcon,
} from "lucide-react";
import React, { useState, useMemo, useEffect } from "react";

// All payment types for filter tabs (including special "no_card" filter)
const ALL_PAYMENT_TYPES: (PaymentType | "all" | "no_card")[] = [
  "all",
  "subscription",
  "housing",
  "utility",
  "professional_service",
  "insurance",
  "debt",
  "savings",
  "transfer",
  "one_time",
  "no_card",
];

// Lucide icon components for each payment type
const PAYMENT_TYPE_ICON_COMPONENTS: Record<PaymentType | "all" | "no_card", LucideIcon> = {
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
      bg: "bg-gradient-to-r from-red-500/10 to-rose-500/10 border-red-200",
      text: "text-red-600",
      label: getDaysLabel(daysUntil),
      icon: AlertCircle,
    },
    due_soon: {
      bg: "bg-gradient-to-r from-amber-500/10 to-yellow-500/10 border-amber-200",
      text: "text-amber-600",
      label: getDaysLabel(daysUntil),
      icon: Clock,
    },
    upcoming: {
      bg: "bg-gradient-to-r from-blue-500/10 to-indigo-500/10 border-blue-200",
      text: "text-blue-600",
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
        <span className="text-xs font-semibold text-purple-700 flex items-center gap-1.5">
          <Repeat className="w-3.5 h-3.5" />
          Installment Plan
        </span>
        <span className="text-xs font-medium text-purple-600 bg-purple-100 px-2 py-0.5 rounded-full">
          {completed}/{total}
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-purple-100 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
          className="h-full bg-gradient-to-r from-purple-500 via-indigo-500 to-violet-500 rounded-full"
        />
      </div>

      <div className="flex justify-between mt-2">
        <p className="text-xs text-purple-500">
          {total - completed} remaining
        </p>
        <p className="text-xs font-medium text-purple-600">
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
  const [isHovered, setIsHovered] = useState(false);
  const { format } = useCurrencyFormat();

  // Try to find service icon from library
  const serviceInfo = useMemo(() => {
    return findService(subscription.name);
  }, [subscription.name]);

  // Use service color if available, otherwise subscription color
  const displayColor = serviceInfo?.color || subscription.color;

  // Get icon URL - prefer custom iconUrl, then SimpleIcons, then subscription icon_url
  const iconUrl = useMemo(() => {
    if (serviceInfo) {
      // Use custom iconUrl if available (e.g., Brandfetch)
      if (serviceInfo.iconUrl) {
        return serviceInfo.iconUrl;
      }
      // Use SimpleIcons if icon slug exists
      if (serviceInfo.icon) {
        return getIconUrl(serviceInfo.icon);
      }
    }
    return subscription.icon_url;
  }, [serviceInfo, subscription.icon_url]);

  return (
    <motion.div
      layout
      variants={itemVariants}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="group relative"
    >
      {/* Glow effect on hover */}
      <motion.div
        initial={false}
        animate={{
          opacity: isHovered ? 1 : 0,
          scale: isHovered ? 1 : 0.8,
        }}
        className="absolute -inset-px rounded-2xl blur-xl transition-opacity"
        style={{
          background: `linear-gradient(135deg, ${displayColor}40 0%, ${displayColor}20 100%)`,
        }}
      />

      {/* Card content */}
      <div
        className={cn(
          "relative glass-card rounded-2xl overflow-hidden transition-all duration-300",
          "border-l-4 hover:shadow-xl"
        )}
        style={{ borderLeftColor: displayColor }}
      >
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-start mb-4">
            <div className="flex items-center gap-3">
              {/* Icon/Avatar */}
              <motion.div
                whileHover={{ scale: 1.1, rotate: 5 }}
                transition={{ type: "spring", stiffness: 400 }}
                className="relative"
              >
                {iconUrl ? (
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center shadow-lg"
                    style={{ backgroundColor: `${displayColor}15` }}
                  >
                    <img
                      src={iconUrl}
                      alt={subscription.name}
                      className="w-7 h-7"
                      style={{ filter: `drop-shadow(0 1px 2px ${displayColor}40)` }}
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
              </motion.div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 group-hover:text-gray-800 transition-colors">
                  {subscription.name}
                </h3>
                {/* Use service library category if available, otherwise database category */}
                {(serviceInfo?.category || subscription.category) && (
                  <CategoryBadge category={serviceInfo?.category || subscription.category || ""} />
                )}
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-1">
              {/* Edit button */}
              <motion.button
                onClick={onEdit}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                className="p-2 rounded-xl transition-all duration-200 text-gray-400 hover:text-blue-500 hover:bg-blue-50"
              >
                <Pencil className="w-4 h-4" />
              </motion.button>

              {/* Delete button */}
              <motion.button
                onClick={onDelete}
                disabled={isDeleting}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                className={cn(
                  "p-2 rounded-xl transition-all duration-200",
                  "text-gray-400 hover:text-red-500 hover:bg-red-50",
                  isDeleting && "opacity-50 cursor-not-allowed"
                )}
              >
                <Trash2 className="w-4 h-4" />
              </motion.button>
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
            <span className="text-sm text-gray-500 font-medium">
              / {getFrequencyLabel(subscription.frequency, subscription.frequency_interval)}
            </span>
          </div>

          {/* Payment info grid */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <div className="p-1.5 bg-gray-100 rounded-lg">
                  <Calendar className="w-4 h-4 text-gray-500" />
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
                className="flex items-center gap-2 text-sm text-gray-500"
              >
                <div className="p-1.5 bg-gray-100 rounded-lg">
                  <CreditCard className="w-4 h-4 text-gray-500" />
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
                <div className="p-1 bg-amber-100 rounded-lg">
                  <Clock className="w-3 h-3 text-amber-600" />
                </div>
                <span className="text-amber-600 font-medium">Manual renewal</span>
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
              className="text-sm text-gray-500 mt-4 line-clamp-2 italic border-t border-gray-100 pt-3"
            >
              "{subscription.notes}"
            </motion.p>
          )}
        </div>

        {/* Bottom accent line */}
        <motion.div
          initial={false}
          animate={{ scaleX: isHovered ? 1 : 0 }}
          transition={{ duration: 0.3 }}
          className="h-0.5 origin-left"
          style={{
            background: `linear-gradient(90deg, ${displayColor} 0%, transparent 100%)`,
          }}
        />
      </div>
    </motion.div>
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

      <h3 className="text-xl font-bold text-gray-900 mb-2">No subscriptions yet</h3>
      <p className="text-gray-500 mb-6 max-w-sm mx-auto">
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

export function SubscriptionList({ initialFilter }: SubscriptionListProps) {
  const queryClient = useQueryClient();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingSubscription, setEditingSubscription] = useState<Subscription | null>(null);
  const [selectedPaymentType, setSelectedPaymentType] = useState<PaymentType | "all" | "no_card">(
    initialFilter === "no_card" ? "no_card" : "all"
  );

  // Update filter when initialFilter changes (from URL)
  useEffect(() => {
    if (initialFilter === "no_card") {
      setSelectedPaymentType("no_card");
    }
  }, [initialFilter]);

  const { data: subscriptions, isLoading } = useQuery({
    queryKey: ["subscriptions"],
    queryFn: () => subscriptionApi.getAll(),
  });

  // Filter subscriptions by payment type
  const filteredSubscriptions = useMemo(() => {
    if (!subscriptions) return [];
    const active = subscriptions.filter((s: Subscription) => s.is_active);
    if (selectedPaymentType === "all") return active;
    if (selectedPaymentType === "no_card") return active.filter((s: Subscription) => !s.card_id);
    return active.filter((s: Subscription) => s.payment_type === selectedPaymentType);
  }, [subscriptions, selectedPaymentType]);

  // Count subscriptions by payment type for badges
  const paymentTypeCounts = useMemo(() => {
    if (!subscriptions) return {};
    const active = subscriptions.filter((s: Subscription) => s.is_active);
    const counts: Record<string, number> = { all: active.length };
    for (const type of Object.keys(PAYMENT_TYPE_LABELS)) {
      counts[type] = active.filter((s: Subscription) => s.payment_type === type).length;
    }
    // Count subscriptions without a card assigned
    counts["no_card"] = active.filter((s: Subscription) => !s.card_id).length;
    return counts;
  }, [subscriptions]);

  const deleteMutation = useMutation({
    mutationFn: (id: string) => subscriptionApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
      queryClient.invalidateQueries({ queryKey: ["calendar-events"] });
    },
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
      <div className="space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4"
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Your Payments</h2>
              <p className="text-sm text-gray-500">
                {filteredSubscriptions.length} active payment{filteredSubscriptions.length !== 1 ? "s" : ""}
                {selectedPaymentType !== "all" && ` (${selectedPaymentType === "no_card" ? "No Card Assigned" : PAYMENT_TYPE_LABELS[selectedPaymentType]})`}
              </p>
            </div>
          </div>

          <motion.button
            onClick={() => setIsAddModalOpen(true)}
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Add Payment
          </motion.button>
        </motion.div>

        {/* Payment Type Filter Tabs */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="flex flex-wrap gap-2 pb-2"
        >
          {ALL_PAYMENT_TYPES.map((type) => {
            const count = paymentTypeCounts[type] || 0;
            const isSelected = selectedPaymentType === type;
            const label = type === "all" ? "All" : type === "no_card" ? "No Card" : PAYMENT_TYPE_LABELS[type];
            const IconComponent = PAYMENT_TYPE_ICON_COMPONENTS[type];

            // Only show tabs with items (or "All")
            if (type !== "all" && count === 0) return null;

            return (
              <motion.button
                key={type}
                onClick={() => setSelectedPaymentType(type)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200",
                  isSelected
                    ? type === "no_card"
                      ? "bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg"
                      : "bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-lg"
                    : type === "no_card"
                      ? "glass-card-subtle text-amber-600 hover:shadow-md border border-amber-200"
                      : "glass-card-subtle text-gray-600 hover:shadow-md"
                )}
              >
                <IconComponent className="w-4 h-4" />
                <span>{label}</span>
                <span
                  className={cn(
                    "ml-1 px-2 py-0.5 rounded-full text-xs font-semibold",
                    isSelected
                      ? "bg-white/20 text-white"
                      : "bg-gray-200 text-gray-600"
                  )}
                >
                  {count}
                </span>
              </motion.button>
            );
          })}
        </motion.div>

        {/* Content */}
        {filteredSubscriptions.length === 0 ? (
          <EmptyState onAdd={() => setIsAddModalOpen(true)} />
        ) : (
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
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
