"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  CreditCard,
  Plus,
  Pencil,
  Trash2,
  Building2,
  Wallet,
  AlertCircle,
  ChevronRight,
  PiggyBank,
  CheckCircle2,
  Clock,
  X,
  Link2,
  ChevronDown,
} from "lucide-react";
import { cardsApi, subscriptionApi, calendarApi, PaymentCard, CardBalanceSummary, PaymentCardCreate, Subscription } from "@/lib/api";
import { useCurrency, CURRENCIES } from "@/lib/currency-context";
import { cn } from "@/lib/utils";
import { useCurrencyFormat } from "@/hooks/useCurrencyFormat";
import { findService, getIconUrl } from "@/lib/service-icons";

// Check if a color is light (needs dark text)
const isLightColor = (hexColor: string): boolean => {
  const hex = hexColor.replace("#", "");
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);
  // Calculate relative luminance
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.6;
};

const CARD_TYPE_ICONS: Record<string, React.ElementType> = {
  debit: CreditCard,
  credit: CreditCard,
  prepaid: Wallet,
  bank_account: Building2,
};

const CARD_TYPE_LABELS: Record<string, string> = {
  debit: "Debit Card",
  credit: "Credit Card",
  prepaid: "Prepaid Card",
  bank_account: "Bank Account",
};

interface CardFormData {
  name: string;
  card_type: "debit" | "credit" | "prepaid" | "bank_account";
  last_four: string;
  bank_name: string;
  currency: string;
  color: string;
  icon_url: string;
  notes: string;
  funding_card_id: string | null;
}

const DEFAULT_FORM: CardFormData = {
  name: "",
  card_type: "debit",
  last_four: "",
  bank_name: "",
  currency: "GBP",
  color: "#3B82F6",
  icon_url: "",
  notes: "",
  funding_card_id: null,
};

const PRESET_COLORS = [
  "#3B82F6", // Blue
  "#10B981", // Emerald
  "#8B5CF6", // Purple
  "#F59E0B", // Amber
  "#EF4444", // Red
  "#EC4899", // Pink
  "#06B6D4", // Cyan
  "#1A1A1A", // Black
  "#006A4D", // Lloyds Green
  "#0666EB", // Revolut Blue
  "#FF5A5F", // Monzo Coral
  "#6366F1", // Indigo
];

export function CardsDashboard() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const { currencyInfo } = useCurrency();
  const { format, convert } = useCurrencyFormat();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingCard, setEditingCard] = useState<PaymentCard | null>(null);
  const [formData, setFormData] = useState<CardFormData>(DEFAULT_FORM);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [selectedCardSubs, setSelectedCardSubs] = useState<{ card: PaymentCard; subscriptions: Subscription[]; fundedSubscriptions?: Subscription[] } | null>(null);
  const [isFundingDropdownOpen, setIsFundingDropdownOpen] = useState(false);

  // Fetch cards and balance summary
  const { data: cards = [], isLoading: cardsLoading } = useQuery({
    queryKey: ["cards"],
    queryFn: cardsApi.getAll,
  });

  const { data: balanceSummary, isLoading: summaryLoading } = useQuery({
    queryKey: ["cards", "balance-summary", currencyInfo.code],
    queryFn: () => cardsApi.getBalanceSummary(currencyInfo.code),
  });

  // Fetch unified payments summary (same as Calendar for consistent totals)
  const { data: paymentsSummary } = useQuery({
    queryKey: ["payments-summary", currencyInfo.code],
    queryFn: () => calendarApi.getPaymentsSummary(currencyInfo.code),
    staleTime: 0,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  });

  // Fetch subscriptions for the modal
  const { data: allSubscriptions = [] } = useQuery({
    queryKey: ["subscriptions"],
    queryFn: () => subscriptionApi.getAll(),
  });

  // Navigate to subscriptions with "no_card" filter
  const handleUnassignedClick = () => {
    router.push("/?view=list&filter=no_card");
  };

  // Open modal with card's subscriptions (including funded cards)
  const handleCardSubscriptionsClick = (card: PaymentCard, balance?: CardBalanceSummary) => {
    const cardSubs = allSubscriptions.filter((s) => s.card_id === card.id && s.is_active);
    // Find subscriptions from funded cards
    const fundedSubs = balance?.funded_subscriptions?.length
      ? allSubscriptions.filter((s) => balance.funded_subscriptions.includes(s.name) && s.is_active)
      : [];
    setSelectedCardSubs({ card, subscriptions: cardSubs, fundedSubscriptions: fundedSubs });
  };

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: PaymentCardCreate) => cardsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cards"] });
      closeForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<PaymentCardCreate> }) =>
      cardsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cards"] });
      closeForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => cardsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cards"] });
      setDeleteConfirm(null);
    },
  });

  const openForm = (card?: PaymentCard) => {
    if (card) {
      setEditingCard(card);
      setFormData({
        name: card.name,
        card_type: card.card_type,
        last_four: card.last_four || "",
        bank_name: card.bank_name,
        currency: card.currency,
        color: card.color,
        icon_url: card.icon_url || "",
        notes: card.notes || "",
        funding_card_id: card.funding_card_id,
      });
    } else {
      setEditingCard(null);
      setFormData(DEFAULT_FORM);
    }
    setIsFormOpen(true);
    setIsFundingDropdownOpen(false);
  };

  const closeForm = () => {
    setIsFormOpen(false);
    setEditingCard(null);
    setFormData(DEFAULT_FORM);
    setIsFundingDropdownOpen(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: PaymentCardCreate = {
      name: formData.name,
      card_type: formData.card_type,
      bank_name: formData.bank_name,
      currency: formData.currency,
      color: formData.color,
      last_four: formData.last_four || undefined,
      icon_url: formData.icon_url || undefined,
      notes: formData.notes || undefined,
      funding_card_id: formData.funding_card_id,
    };

    if (editingCard) {
      updateMutation.mutate({ id: editingCard.id, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  // Get available cards for funding (exclude current card if editing)
  const availableFundingCards = cards.filter(
    (c) => c.id !== editingCard?.id && !c.funding_card_id // Can't chain funding cards
  );

  // Get balance info for a card
  const getCardBalance = (cardId: string): CardBalanceSummary | undefined => {
    return balanceSummary?.cards.find((c) => c.card_id === cardId);
  };

  const isLoading = cardsLoading || summaryLoading;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500 text-white">
            <Wallet className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Payment Cards</h2>
            <p className="text-sm text-gray-500">
              Manage your cards and see required balances
            </p>
          </div>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => openForm()}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 transition-shadow"
        >
          <Plus className="w-5 h-5" />
          Add Card
        </motion.button>
      </div>

      {/* Summary Cards */}
      {(balanceSummary || paymentsSummary) && (
        <div className="space-y-4">
          {/* Main Progress Card - uses unified payments summary for consistent totals */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-6 rounded-2xl"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-blue-100 text-blue-600">
                <CreditCard className="w-5 h-5" />
              </div>
              <span className="text-lg font-semibold text-gray-900">This Month&apos;s Progress</span>
            </div>

            {/* Progress Bar - uses unified summary */}
            <div className="mb-4">
              <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
                {(() => {
                  const total = paymentsSummary ? parseFloat(paymentsSummary.current_month_total) : (balanceSummary ? parseFloat(balanceSummary.total_all_cards_this_month) : 0);
                  const paid = paymentsSummary ? parseFloat(paymentsSummary.current_month_paid) : (balanceSummary ? parseFloat(balanceSummary.total_paid_this_month) : 0);
                  const percentage = total > 0 ? Math.min(100, (paid / total) * 100) : 0;
                  return (
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${percentage}%` }}
                      transition={{ duration: 0.8, ease: "easeOut" }}
                      className="h-full bg-gradient-to-r from-emerald-500 to-green-500 rounded-full"
                    />
                  );
                })()}
              </div>
              <div className="flex justify-between mt-2 text-sm">
                <span className="text-gray-500">
                  {(() => {
                    const total = paymentsSummary ? parseFloat(paymentsSummary.current_month_total) : (balanceSummary ? parseFloat(balanceSummary.total_all_cards_this_month) : 0);
                    const paid = paymentsSummary ? parseFloat(paymentsSummary.current_month_paid) : (balanceSummary ? parseFloat(balanceSummary.total_paid_this_month) : 0);
                    return total > 0 ? Math.round((paid / total) * 100) : 0;
                  })()}% paid
                </span>
                <span className="text-gray-500">
                  {format(
                    paymentsSummary ? parseFloat(paymentsSummary.current_month_remaining) : (balanceSummary ? parseFloat(balanceSummary.total_remaining_this_month) : 0),
                    currencyInfo.code
                  )} remaining
                </span>
              </div>
            </div>

            {/* Stats Row - uses unified summary */}
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 rounded-xl bg-gray-50">
                <div className="flex items-center justify-center gap-1.5 mb-1">
                  <Clock className="w-4 h-4 text-blue-500" />
                  <span className="text-xs font-medium text-gray-500">Total Due</span>
                </div>
                <p className="text-lg font-bold text-gray-900">
                  {format(
                    paymentsSummary ? parseFloat(paymentsSummary.current_month_total) : (balanceSummary ? parseFloat(balanceSummary.total_all_cards_this_month) : 0),
                    currencyInfo.code
                  )}
                </p>
              </div>
              <div className="text-center p-3 rounded-xl bg-emerald-50">
                <div className="flex items-center justify-center gap-1.5 mb-1">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span className="text-xs font-medium text-gray-500">Paid</span>
                </div>
                <p className="text-lg font-bold text-emerald-600">
                  {format(
                    paymentsSummary ? parseFloat(paymentsSummary.current_month_paid) : (balanceSummary ? parseFloat(balanceSummary.total_paid_this_month) : 0),
                    currencyInfo.code
                  )}
                </p>
              </div>
              <div className="text-center p-3 rounded-xl bg-amber-50">
                <div className="flex items-center justify-center gap-1.5 mb-1">
                  <AlertCircle className="w-4 h-4 text-amber-500" />
                  <span className="text-xs font-medium text-gray-500">Remaining</span>
                </div>
                <p className="text-lg font-bold text-amber-600">
                  {format(
                    paymentsSummary ? parseFloat(paymentsSummary.current_month_remaining) : (balanceSummary ? parseFloat(balanceSummary.total_remaining_this_month) : 0),
                    currencyInfo.code
                  )}
                </p>
              </div>
            </div>
          </motion.div>

          {/* Secondary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="glass-card p-5 rounded-2xl"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-purple-100 text-purple-600">
                  <PiggyBank className="w-5 h-5" />
                </div>
                <span className="text-sm font-medium text-gray-600">Due Next Month</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {format(
                  paymentsSummary ? parseFloat(paymentsSummary.next_month_total) : (balanceSummary ? parseFloat(balanceSummary.total_all_cards_next_month) : 0),
                  currencyInfo.code
                )}
              </p>
            </motion.div>

            {balanceSummary && balanceSummary.unassigned_count > 0 && (
              <motion.button
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleUnassignedClick}
                className="glass-card p-5 rounded-2xl text-left hover:shadow-lg hover:border-amber-200 border-2 border-transparent transition-all cursor-pointer"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-amber-100 text-amber-600">
                      <AlertCircle className="w-5 h-5" />
                    </div>
                    <span className="text-sm font-medium text-gray-600">Unassigned</span>
                  </div>
                  <ChevronRight className="w-5 h-5 text-amber-400" />
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {balanceSummary.unassigned_count} payment{balanceSummary.unassigned_count !== 1 ? "s" : ""}
                </p>
                <p className="text-sm text-gray-500">
                  {format(parseFloat(balanceSummary.unassigned_total), currencyInfo.code)} total
                </p>
              </motion.button>
            )}
          </div>
        </div>
      )}

      {/* Cards Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass-card p-6 rounded-2xl animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-4" />
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
              <div className="h-8 bg-gray-200 rounded w-1/3" />
            </div>
          ))}
        </div>
      ) : cards.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card p-12 rounded-2xl text-center"
        >
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
            <CreditCard className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No cards yet</h3>
          <p className="text-gray-500 mb-4">
            Add your payment cards to track which card pays for each subscription
          </p>
          <button
            onClick={() => openForm()}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Your First Card
          </button>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <AnimatePresence>
            {cards.map((card, index) => {
              const balance = getCardBalance(card.id);
              const Icon = CARD_TYPE_ICONS[card.card_type] || CreditCard;

              return (
                <motion.div
                  key={card.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ delay: index * 0.05 }}
                  className="glass-card rounded-2xl overflow-hidden group"
                >
                  {/* Card Header with Color */}
                  {(() => {
                    const isLight = isLightColor(card.color);
                    return (
                      <div
                        className={cn(
                          "p-4 relative",
                          isLight ? "text-gray-800" : "text-white"
                        )}
                        style={{ backgroundColor: card.color }}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-3">
                            {card.icon_url ? (
                              <div className={cn(
                                "w-10 h-10 rounded-lg flex items-center justify-center overflow-hidden",
                                isLight ? "bg-white shadow-sm" : "bg-white/90"
                              )}>
                                <img
                                  src={card.icon_url}
                                  alt={card.bank_name}
                                  className="w-6 h-6 object-contain"
                                />
                              </div>
                            ) : (
                              <div className={cn(
                                "w-10 h-10 rounded-lg flex items-center justify-center",
                                isLight ? "bg-gray-800/10" : "bg-white/20"
                              )}>
                                <Icon className="w-5 h-5" />
                              </div>
                            )}
                            <div>
                              <h3 className="font-semibold">{card.name}</h3>
                              <p className={cn("text-sm", isLight ? "text-gray-600" : "opacity-80")}>{card.bank_name}</p>
                            </div>
                          </div>
                          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => openForm(card)}
                              className={cn(
                                "p-1.5 rounded-lg transition-colors",
                                isLight ? "bg-gray-800/10 hover:bg-gray-800/20" : "bg-white/20 hover:bg-white/30"
                              )}
                            >
                              <Pencil className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => setDeleteConfirm(card.id)}
                              className={cn(
                                "p-1.5 rounded-lg transition-colors",
                                isLight ? "bg-gray-800/10 hover:bg-red-500/30" : "bg-white/20 hover:bg-red-500/50"
                              )}
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                        <p className={cn("mt-3 font-mono text-sm", isLight ? "text-gray-600" : "opacity-80")}>
                          •••• •••• •••• {card.last_four || "••••"}
                        </p>
                        <div className={cn("mt-2 text-xs flex items-center gap-2", isLight ? "text-gray-500" : "opacity-70")}>
                          <span>{CARD_TYPE_LABELS[card.card_type]} &bull; {card.currency}</span>
                          {card.funding_card && (
                            <span className={cn(
                              "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium",
                              isLight ? "bg-gray-800/10" : "bg-white/20"
                            )}>
                              <Link2 className="w-2.5 h-2.5" />
                              via {card.funding_card.name}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })()}

                  {/* Balance Info */}
                  <div className="p-3 space-y-2">
                    {balance ? (
                      <>
                        {/* This Month Progress */}
                        <div>
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-sm text-gray-500">This month</span>
                            <div className="text-right">
                              <span className="font-semibold text-gray-900">
                                {format(parseFloat(balance.total_this_month) + parseFloat(balance.funded_this_month), currencyInfo.code)}
                              </span>
                              {parseFloat(balance.funded_this_month) > 0 && (
                                <span className="text-xs text-purple-500 ml-1">
                                  (+{format(parseFloat(balance.funded_this_month), currencyInfo.code)} via linked)
                                </span>
                              )}
                            </div>
                          </div>
                          {/* Mini Progress Bar */}
                          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            {(() => {
                              const total = parseFloat(balance.total_this_month) + parseFloat(balance.funded_this_month);
                              const paid = parseFloat(balance.paid_this_month);
                              const percentage = total > 0 ? Math.min(100, (paid / total) * 100) : 0;
                              return (
                                <motion.div
                                  initial={{ width: 0 }}
                                  animate={{ width: `${percentage}%` }}
                                  transition={{ duration: 0.6, ease: "easeOut", delay: index * 0.1 }}
                                  className={cn(
                                    "h-full rounded-full",
                                    percentage >= 100
                                      ? "bg-gradient-to-r from-emerald-500 to-green-500"
                                      : "bg-gradient-to-r from-blue-500 to-indigo-500"
                                  )}
                                />
                              );
                            })()}
                          </div>
                          <div className="flex justify-between mt-0.5 text-xs">
                            <span className="text-emerald-600 font-medium">
                              {format(parseFloat(balance.paid_this_month), currencyInfo.code)} paid
                            </span>
                            <span className="text-amber-600 font-medium">
                              {format(parseFloat(balance.remaining_this_month), currencyInfo.code)} left
                            </span>
                          </div>
                        </div>

                        <div className="flex justify-between items-center pt-1.5 border-t border-gray-100">
                          <span className="text-sm text-gray-500">Next month</span>
                          <span className="font-medium text-gray-600">
                            {format(parseFloat(balance.total_next_month) + parseFloat(balance.funded_next_month), currencyInfo.code)}
                          </span>
                        </div>
                        <button
                          onClick={() => handleCardSubscriptionsClick(card, balance)}
                          className="w-full pt-1.5 border-t border-gray-100 hover:bg-gray-50 rounded-lg transition-colors -mx-1 px-1"
                        >
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-500">
                              {balance.subscription_count + balance.funded_subscription_count} payment
                              {(balance.subscription_count + balance.funded_subscription_count) !== 1 ? "s" : ""}
                              {balance.funded_subscription_count > 0 && (
                                <span className="text-purple-500 ml-1">
                                  ({balance.funded_subscription_count} via linked)
                                </span>
                              )}
                            </span>
                            <ChevronRight className="w-4 h-4 text-gray-400" />
                          </div>
                          {(balance.subscriptions.length > 0 || balance.funded_subscriptions.length > 0) && (
                            <p className="text-xs text-gray-400 mt-0.5 truncate text-left">
                              {[...balance.subscriptions, ...balance.funded_subscriptions].slice(0, 3).join(", ")}
                              {[...balance.subscriptions, ...balance.funded_subscriptions].length > 3 &&
                                ` +${[...balance.subscriptions, ...balance.funded_subscriptions].length - 3} more`}
                            </p>
                          )}
                        </button>
                      </>
                    ) : (
                      <p className="text-sm text-gray-400 text-center py-2">
                        No payments assigned
                      </p>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}

      {/* Add/Edit Card Modal */}
      <AnimatePresence>
        {isFormOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={closeForm}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto"
            >
              <div className="p-6 border-b border-gray-100">
                <h3 className="text-xl font-bold text-gray-900">
                  {editingCard ? "Edit Card" : "Add New Card"}
                </h3>
              </div>

              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                {/* Card Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Card Name
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Revolut Platinum"
                    required
                    className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all"
                  />
                </div>

                {/* Bank Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Bank / Provider
                  </label>
                  <input
                    type="text"
                    value={formData.bank_name}
                    onChange={(e) => setFormData({ ...formData, bank_name: e.target.value })}
                    placeholder="e.g., Revolut"
                    required
                    className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all"
                  />
                </div>

                {/* Card Type & Currency */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Card Type
                    </label>
                    <select
                      value={formData.card_type}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          card_type: e.target.value as CardFormData["card_type"],
                        })
                      }
                      className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all"
                    >
                      <option value="debit">Debit</option>
                      <option value="credit">Credit</option>
                      <option value="prepaid">Prepaid</option>
                      <option value="bank_account">Bank Account</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Currency
                    </label>
                    <select
                      value={formData.currency}
                      onChange={(e) =>
                        setFormData({ ...formData, currency: e.target.value })
                      }
                      className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all"
                    >
                      <option value="GBP">GBP (£)</option>
                      <option value="USD">USD ($)</option>
                      <option value="EUR">EUR (€)</option>
                      <option value="UAH">UAH (₴)</option>
                    </select>
                  </div>
                </div>

                {/* Last 4 Digits */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Last 4 Digits (optional)
                  </label>
                  <input
                    type="text"
                    value={formData.last_four}
                    onChange={(e) => {
                      const val = e.target.value.replace(/\D/g, "").slice(0, 4);
                      setFormData({ ...formData, last_four: val });
                    }}
                    placeholder="1234"
                    maxLength={4}
                    className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all font-mono"
                  />
                </div>

                {/* Color Picker */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Card Color
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {PRESET_COLORS.map((color) => (
                      <button
                        key={color}
                        type="button"
                        onClick={() => setFormData({ ...formData, color })}
                        className={cn(
                          "w-8 h-8 rounded-lg transition-all",
                          formData.color === color
                            ? "ring-2 ring-offset-2 ring-blue-500 scale-110"
                            : "hover:scale-105"
                        )}
                        style={{ backgroundColor: color }}
                      />
                    ))}
                    <input
                      type="color"
                      value={formData.color}
                      onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                      className="w-8 h-8 rounded-lg cursor-pointer"
                    />
                  </div>
                </div>

                {/* Icon URL */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Icon URL (optional)
                  </label>
                  <input
                    type="url"
                    value={formData.icon_url}
                    onChange={(e) => setFormData({ ...formData, icon_url: e.target.value })}
                    placeholder="https://logo.clearbit.com/bank.com"
                    className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all"
                  />
                </div>

                {/* Funding Card (for cards like PayPal funded by Monzo) */}
                {availableFundingCards.length > 0 && (
                  <div className="relative">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <div className="flex items-center gap-1.5">
                        <Link2 className="w-4 h-4" />
                        Funded By (optional)
                      </div>
                      <span className="text-xs text-gray-500 font-normal">
                        Link to another card that funds this one (e.g., PayPal funded by Monzo)
                      </span>
                    </label>
                    <button
                      type="button"
                      onClick={() => setIsFundingDropdownOpen(!isFundingDropdownOpen)}
                      className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all text-left flex items-center justify-between"
                    >
                      {formData.funding_card_id ? (
                        <div className="flex items-center gap-2">
                          {(() => {
                            const fundingCard = cards.find(c => c.id === formData.funding_card_id);
                            if (!fundingCard) return <span className="text-gray-500">Select a card...</span>;
                            return (
                              <>
                                <div
                                  className="w-4 h-4 rounded"
                                  style={{ backgroundColor: fundingCard.color }}
                                />
                                <span>{fundingCard.name}</span>
                              </>
                            );
                          })()}
                        </div>
                      ) : (
                        <span className="text-gray-500">None (standalone card)</span>
                      )}
                      <ChevronDown className={cn(
                        "w-5 h-5 text-gray-400 transition-transform",
                        isFundingDropdownOpen && "rotate-180"
                      )} />
                    </button>

                    <AnimatePresence>
                      {isFundingDropdownOpen && (
                        <motion.div
                          initial={{ opacity: 0, y: -10, scale: 0.95 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          exit={{ opacity: 0, y: -10, scale: 0.95 }}
                          transition={{ duration: 0.15 }}
                          className="absolute z-50 w-full mt-2 py-2 bg-white rounded-xl shadow-xl border border-gray-100 max-h-48 overflow-y-auto"
                        >
                          <button
                            type="button"
                            onClick={() => {
                              setFormData({ ...formData, funding_card_id: null });
                              setIsFundingDropdownOpen(false);
                            }}
                            className={cn(
                              "w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-2",
                              !formData.funding_card_id && "bg-blue-50"
                            )}
                          >
                            <div className="w-4 h-4 rounded border border-gray-300" />
                            <span className="text-gray-600">None (standalone)</span>
                          </button>
                          {availableFundingCards.map((fundCard) => (
                            <button
                              key={fundCard.id}
                              type="button"
                              onClick={() => {
                                setFormData({ ...formData, funding_card_id: fundCard.id });
                                setIsFundingDropdownOpen(false);
                              }}
                              className={cn(
                                "w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-2",
                                formData.funding_card_id === fundCard.id && "bg-blue-50"
                              )}
                            >
                              <div
                                className="w-4 h-4 rounded"
                                style={{ backgroundColor: fundCard.color }}
                              />
                              <span>{fundCard.name}</span>
                              <span className="text-xs text-gray-400">({fundCard.bank_name})</span>
                            </button>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {isFundingDropdownOpen && (
                      <div
                        className="fixed inset-0 z-40"
                        onClick={() => setIsFundingDropdownOpen(false)}
                      />
                    )}
                  </div>
                )}

                {/* Notes */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notes (optional)
                  </label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="Any notes about this card..."
                    rows={2}
                    className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all resize-none"
                  />
                </div>

                {/* Actions */}
                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={closeForm}
                    className="flex-1 px-4 py-2.5 border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createMutation.isPending || updateMutation.isPending}
                    className="flex-1 px-4 py-2.5 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-xl font-medium hover:shadow-lg transition-shadow disabled:opacity-50"
                  >
                    {createMutation.isPending || updateMutation.isPending
                      ? "Saving..."
                      : editingCard
                      ? "Update Card"
                      : "Add Card"}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {deleteConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setDeleteConfirm(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl shadow-xl max-w-sm w-full p-6"
            >
              <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
                <Trash2 className="w-6 h-6 text-red-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 text-center mb-2">
                Delete Card?
              </h3>
              <p className="text-gray-500 text-center mb-6">
                This will unlink all subscriptions from this card. This action cannot be
                undone.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setDeleteConfirm(null)}
                  className="flex-1 px-4 py-2.5 border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => deleteMutation.mutate(deleteConfirm)}
                  disabled={deleteMutation.isPending}
                  className="flex-1 px-4 py-2.5 bg-red-500 text-white rounded-xl font-medium hover:bg-red-600 transition-colors disabled:opacity-50"
                >
                  {deleteMutation.isPending ? "Deleting..." : "Delete"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Card Subscriptions Modal */}
      <AnimatePresence>
        {selectedCardSubs && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedCardSubs(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl shadow-xl max-w-md w-full overflow-hidden"
            >
              {/* Modal Header with Card Color */}
              {(() => {
                const isLight = isLightColor(selectedCardSubs.card.color);
                return (
                  <div
                    className={cn("p-5", isLight ? "text-gray-800" : "text-white")}
                    style={{ backgroundColor: selectedCardSubs.card.color }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {selectedCardSubs.card.icon_url ? (
                          <div className={cn(
                            "w-10 h-10 rounded-lg flex items-center justify-center overflow-hidden",
                            isLight ? "bg-white shadow-sm" : "bg-white/90"
                          )}>
                            <img
                              src={selectedCardSubs.card.icon_url}
                              alt={selectedCardSubs.card.bank_name}
                              className="w-6 h-6 object-contain"
                            />
                          </div>
                        ) : (
                          <div className={cn(
                            "w-10 h-10 rounded-lg flex items-center justify-center",
                            isLight ? "bg-gray-800/10" : "bg-white/20"
                          )}>
                            <CreditCard className="w-5 h-5" />
                          </div>
                        )}
                        <div>
                          <h3 className="font-semibold text-lg">{selectedCardSubs.card.name}</h3>
                          <p className={cn("text-sm", isLight ? "text-gray-600" : "opacity-80")}>{selectedCardSubs.card.bank_name}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => setSelectedCardSubs(null)}
                        className={cn(
                          "p-2 rounded-lg transition-colors",
                          isLight ? "bg-gray-800/10 hover:bg-gray-800/20" : "bg-white/20 hover:bg-white/30"
                        )}
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                );
              })()}

              {/* Subscriptions List */}
              <div className="p-4 max-h-[60vh] overflow-y-auto">
                {selectedCardSubs.subscriptions.length === 0 && (!selectedCardSubs.fundedSubscriptions || selectedCardSubs.fundedSubscriptions.length === 0) ? (
                  <p className="text-center text-gray-500 py-8">
                    No payments assigned to this card
                  </p>
                ) : (
                  <div className="space-y-4">
                    {/* Direct Subscriptions */}
                    {selectedCardSubs.subscriptions.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Direct Payments</h4>
                        {selectedCardSubs.subscriptions.map((sub) => {
                          const serviceInfo = findService(sub.name);
                          const iconUrl = serviceInfo?.iconUrl || (serviceInfo?.icon ? getIconUrl(serviceInfo.icon) : null) || sub.icon_url;
                          const brandColor = serviceInfo?.color || sub.color || "#6366F1";
                          return (
                            <div
                              key={sub.id}
                              className="flex items-center justify-between p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors"
                            >
                              <div className="flex items-center gap-3">
                                {iconUrl ? (
                                  <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-gray-100 overflow-hidden">
                                    <img
                                      src={iconUrl}
                                      alt={sub.name}
                                      className="w-5 h-5 object-contain"
                                      onError={(e) => {
                                        const target = e.target as HTMLImageElement;
                                        target.style.display = "none";
                                        const parent = target.parentElement;
                                        if (parent) {
                                          parent.style.backgroundColor = brandColor;
                                          parent.innerHTML = `<span class="text-white font-medium text-sm">${sub.name.charAt(0).toUpperCase()}</span>`;
                                        }
                                      }}
                                    />
                                  </div>
                                ) : (
                                  <div
                                    className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-medium"
                                    style={{ backgroundColor: brandColor }}
                                  >
                                    {sub.name.charAt(0).toUpperCase()}
                                  </div>
                                )}
                                <div>
                                  <p className="font-medium text-gray-900 text-sm">{sub.name}</p>
                                  <p className="text-xs text-gray-500">
                                    {sub.frequency === "monthly" ? "Monthly" :
                                     sub.frequency === "yearly" ? "Yearly" :
                                     sub.frequency === "weekly" ? "Weekly" : sub.frequency}
                                  </p>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className="font-semibold text-gray-900">
                                  {format(parseFloat(sub.amount), sub.currency)}
                                </p>
                                {sub.is_installment && sub.installments_remaining && (
                                  <p className="text-xs text-gray-500">
                                    {sub.installments_remaining} left
                                  </p>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* Funded Subscriptions (from linked cards like PayPal) */}
                    {selectedCardSubs.fundedSubscriptions && selectedCardSubs.fundedSubscriptions.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-xs font-semibold text-purple-500 uppercase tracking-wider flex items-center gap-1">
                          <Link2 className="w-3 h-3" />
                          Via Linked Cards
                        </h4>
                        {selectedCardSubs.fundedSubscriptions.map((sub) => {
                          const serviceInfo = findService(sub.name);
                          const iconUrl = serviceInfo?.iconUrl || (serviceInfo?.icon ? getIconUrl(serviceInfo.icon) : null) || sub.icon_url;
                          const brandColor = serviceInfo?.color || sub.color || "#6366F1";
                          return (
                            <div
                              key={sub.id}
                              className="flex items-center justify-between p-3 rounded-xl bg-purple-50/50 hover:bg-purple-50 transition-colors"
                            >
                              <div className="flex items-center gap-3">
                                {iconUrl ? (
                                  <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-gray-100 overflow-hidden">
                                    <img
                                      src={iconUrl}
                                      alt={sub.name}
                                      className="w-5 h-5 object-contain"
                                      onError={(e) => {
                                        const target = e.target as HTMLImageElement;
                                        target.style.display = "none";
                                        const parent = target.parentElement;
                                        if (parent) {
                                          parent.style.backgroundColor = brandColor;
                                          parent.innerHTML = `<span class="text-white font-medium text-sm">${sub.name.charAt(0).toUpperCase()}</span>`;
                                        }
                                      }}
                                    />
                                  </div>
                                ) : (
                                  <div
                                    className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-medium"
                                    style={{ backgroundColor: brandColor }}
                                  >
                                    {sub.name.charAt(0).toUpperCase()}
                                  </div>
                                )}
                                <div>
                                  <p className="font-medium text-gray-900 text-sm">{sub.name}</p>
                                  <p className="text-xs text-gray-500">
                                    {sub.frequency === "monthly" ? "Monthly" :
                                     sub.frequency === "yearly" ? "Yearly" :
                                     sub.frequency === "weekly" ? "Weekly" : sub.frequency}
                                  </p>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className="font-semibold text-gray-900">
                                  {format(parseFloat(sub.amount), sub.currency)}
                                </p>
                                {sub.is_installment && sub.installments_remaining && (
                                  <p className="text-xs text-gray-500">
                                    {sub.installments_remaining} left
                                  </p>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Footer */}
              {(selectedCardSubs.subscriptions.length > 0 || (selectedCardSubs.fundedSubscriptions && selectedCardSubs.fundedSubscriptions.length > 0)) && (
                <div className="p-4 border-t border-gray-100 bg-gray-50">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">
                      {selectedCardSubs.subscriptions.length + (selectedCardSubs.fundedSubscriptions?.length || 0)} payment
                      {(selectedCardSubs.subscriptions.length + (selectedCardSubs.fundedSubscriptions?.length || 0)) !== 1 ? "s" : ""}
                    </span>
                    <span className="font-semibold text-gray-900">
                      {format(
                        [...selectedCardSubs.subscriptions, ...(selectedCardSubs.fundedSubscriptions || [])].reduce((sum, s) => sum + convert(parseFloat(s.amount), s.currency), 0),
                        currencyInfo.code
                      )}
                      <span className="text-xs text-gray-500 font-normal">/mo</span>
                    </span>
                  </div>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
