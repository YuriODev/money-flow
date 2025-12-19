"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { subscriptionApi, cardsApi, type Subscription, type PaymentMode, PAYMENT_MODE_LABELS, PAYMENT_MODE_ICONS } from "@/lib/api";
import { cn } from "@/lib/utils";
import { X, Save, Loader2, Calendar, CreditCard, Wallet, ChevronDown, Tag, FolderOpen } from "lucide-react";
import { toast } from "@/components/Toast";
import { CategorySelector } from "@/components/CategorySelector";

interface EditSubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  subscription: Subscription;
}

const CURRENCIES = [
  { code: "GBP", symbol: "£", name: "British Pound" },
  { code: "USD", symbol: "$", name: "US Dollar" },
  { code: "EUR", symbol: "€", name: "Euro" },
  { code: "UAH", symbol: "₴", name: "Ukrainian Hryvnia" },
];

const backdropVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
};

const modalVariants = {
  hidden: { opacity: 0, scale: 0.9, y: 20 },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { type: "spring" as const, damping: 25, stiffness: 300 },
  },
  exit: { opacity: 0, scale: 0.9, y: 20, transition: { duration: 0.2 } },
};

export function EditSubscriptionModal({
  isOpen,
  onClose,
  subscription,
}: EditSubscriptionModalProps) {
  const queryClient = useQueryClient();
  const [amount, setAmount] = useState(subscription.amount);
  const [currency, setCurrency] = useState(subscription.currency);
  const [startDate, setStartDate] = useState(subscription.start_date);
  const [cardId, setCardId] = useState<string | null>(subscription.card_id || null);
  const [categoryId, setCategoryId] = useState<string | null>(subscription.category_id || null);
  const [paymentMode, setPaymentMode] = useState<PaymentMode>(subscription.payment_mode);
  const [isCardDropdownOpen, setIsCardDropdownOpen] = useState(false);
  const [isPaymentModeDropdownOpen, setIsPaymentModeDropdownOpen] = useState(false);

  // Fetch available cards
  const { data: cards = [] } = useQuery({
    queryKey: ["cards"],
    queryFn: cardsApi.getAll,
  });

  const selectedCard = cards.find(c => c.id === cardId);

  // Reset form when subscription changes
  useEffect(() => {
    setAmount(subscription.amount);
    setCurrency(subscription.currency);
    setStartDate(subscription.start_date);
    setCardId(subscription.card_id || null);
    setCategoryId(subscription.category_id || null);
    setPaymentMode(subscription.payment_mode);
  }, [subscription]);

  const updateMutation = useMutation({
    mutationFn: (data: { amount: number; currency: string; start_date: string; card_id?: string | null; category_id?: string | null; payment_mode?: PaymentMode }) =>
      subscriptionApi.update(subscription.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
      queryClient.invalidateQueries({ queryKey: ["calendar-events"] });
      queryClient.invalidateQueries({ queryKey: ["cards"] });
      toast.success("Payment updated", `${subscription.name} has been updated.`);
      onClose();
    },
    onError: () => {
      toast.error("Failed to update", "There was an error updating the payment. Please try again.");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const numericAmount = parseFloat(amount);
    if (isNaN(numericAmount) || numericAmount <= 0) return;
    updateMutation.mutate({
      amount: numericAmount,
      currency,
      start_date: startDate,
      card_id: cardId,
      category_id: categoryId,
      payment_mode: paymentMode,
    });
  };

  const selectedCurrency = CURRENCIES.find((c) => c.code === currency);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            onClick={onClose}
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
          />

          {/* Modal */}
          <motion.div
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="relative w-full max-w-md glass-card rounded-3xl shadow-2xl"
          >
            {/* Header */}
            <div className="relative px-6 pt-6 pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                    Edit Subscription
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {subscription.name}
                  </p>
                </div>
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={onClose}
                  className="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                </motion.button>
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="px-6 pb-6">
              {/* Amount Input */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Amount
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-gray-500 font-medium">
                    {selectedCurrency?.symbol}
                  </span>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className={cn(
                      "w-full pl-10 pr-4 py-3 rounded-xl border-2 transition-all duration-200",
                      "focus:ring-0 focus:border-blue-400 dark:focus:border-blue-500 focus:shadow-lg focus:shadow-blue-100 dark:focus:shadow-blue-900/50",
                      "border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 text-lg font-semibold placeholder-gray-400 dark:placeholder-gray-500"
                    )}
                    placeholder="0.00"
                  />
                </div>
              </div>

              {/* Start Date */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Start Date
                </label>
                <div className="relative">
                  <Calendar className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className={cn(
                      "w-full pl-10 pr-4 py-3 rounded-xl border-2 transition-all duration-200",
                      "focus:ring-0 focus:border-blue-400 dark:focus:border-blue-500 focus:shadow-lg focus:shadow-blue-100 dark:focus:shadow-blue-900/50",
                      "border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100"
                    )}
                  />
                </div>
              </div>

              {/* Currency Selector */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Currency
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {CURRENCIES.map((curr) => (
                    <motion.button
                      key={curr.code}
                      type="button"
                      onClick={() => setCurrency(curr.code)}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className={cn(
                        "flex flex-col items-center gap-1 p-3 rounded-xl transition-all duration-200",
                        currency === curr.code
                          ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-lg"
                          : "glass-card-subtle hover:shadow-md"
                      )}
                    >
                      <span className="text-lg font-bold">{curr.symbol}</span>
                      <span className="text-xs opacity-75">{curr.code}</span>
                    </motion.button>
                  ))}
                </div>
              </div>

              {/* Payment Mode Selector */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <div className="flex items-center gap-2">
                    <Tag className="w-4 h-4" />
                    Payment Mode
                  </div>
                </label>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setIsPaymentModeDropdownOpen(!isPaymentModeDropdownOpen)}
                    className={cn(
                      "w-full px-4 py-3 rounded-xl border-2 transition-all duration-200 text-left",
                      "focus:ring-0 focus:border-blue-400 dark:focus:border-blue-500 focus:shadow-lg focus:shadow-blue-100 dark:focus:shadow-blue-900/50",
                      isPaymentModeDropdownOpen ? "border-blue-400 dark:border-blue-500 shadow-lg shadow-blue-100 dark:shadow-blue-900/50" : "border-gray-200 dark:border-gray-700",
                      "bg-white/50 dark:bg-gray-800/50 flex items-center justify-between"
                    )}
                  >
                    <span className="flex items-center gap-2 font-medium text-gray-900 dark:text-gray-100">
                      <span>{PAYMENT_MODE_ICONS[paymentMode]}</span>
                      {PAYMENT_MODE_LABELS[paymentMode]}
                    </span>
                    <ChevronDown className={cn(
                      "w-5 h-5 text-gray-400 dark:text-gray-500 transition-transform",
                      isPaymentModeDropdownOpen && "rotate-180"
                    )} />
                  </button>

                  <AnimatePresence>
                    {isPaymentModeDropdownOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: -10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.95 }}
                        transition={{ duration: 0.15 }}
                        className="absolute z-[100] w-full mt-2 py-2 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-100 dark:border-gray-700 max-h-64 overflow-y-auto"
                      >
                        {(Object.keys(PAYMENT_MODE_LABELS) as PaymentMode[]).map((mode) => (
                          <button
                            key={mode}
                            type="button"
                            onClick={() => {
                              setPaymentMode(mode);
                              setIsPaymentModeDropdownOpen(false);
                            }}
                            className={cn(
                              "w-full px-4 py-2.5 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center gap-2",
                              paymentMode === mode && "bg-blue-50 dark:bg-blue-900/30"
                            )}
                          >
                            <span>{PAYMENT_MODE_ICONS[mode]}</span>
                            <span className={cn(
                              "font-medium",
                              paymentMode === mode ? "text-blue-600 dark:text-blue-400" : "text-gray-700 dark:text-gray-300"
                            )}>
                              {PAYMENT_MODE_LABELS[mode]}
                            </span>
                          </button>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {isPaymentModeDropdownOpen && (
                    <div
                      className="fixed inset-0 z-[99]"
                      onClick={() => setIsPaymentModeDropdownOpen(false)}
                    />
                  )}
                </div>
              </div>

              {/* Category Selector */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <div className="flex items-center gap-2">
                    <FolderOpen className="w-4 h-4" />
                    Category
                  </div>
                </label>
                <CategorySelector
                  value={categoryId}
                  onChange={(newCategoryId) => setCategoryId(newCategoryId)}
                />
              </div>

              {/* Payment Card Selector - Custom Dropdown */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <div className="flex items-center gap-2">
                    <Wallet className="w-4 h-4" />
                    Payment Card
                  </div>
                </label>
                <div className="relative">
                  {/* Dropdown Trigger */}
                  <button
                    type="button"
                    onClick={() => setIsCardDropdownOpen(!isCardDropdownOpen)}
                    className={cn(
                      "w-full px-4 py-3 rounded-xl border-2 transition-all duration-200 text-left",
                      "focus:ring-0 focus:border-blue-400 dark:focus:border-blue-500 focus:shadow-lg focus:shadow-blue-100 dark:focus:shadow-blue-900/50",
                      isCardDropdownOpen ? "border-blue-400 dark:border-blue-500 shadow-lg shadow-blue-100 dark:shadow-blue-900/50" : "border-gray-200 dark:border-gray-700",
                      "bg-white/50 dark:bg-gray-800/50 flex items-center gap-3"
                    )}
                  >
                    {selectedCard ? (
                      <>
                        {selectedCard.icon_url ? (
                          <img
                            src={selectedCard.icon_url}
                            alt={selectedCard.bank_name}
                            className="w-8 h-8 rounded-lg object-contain bg-gray-50 dark:bg-gray-700"
                          />
                        ) : (
                          <div
                            className="w-8 h-8 rounded-lg flex items-center justify-center"
                            style={{ backgroundColor: selectedCard.color }}
                          >
                            <CreditCard className="w-4 h-4 text-white" />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 dark:text-gray-100 truncate">{selectedCard.name}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {selectedCard.bank_name} {selectedCard.last_four ? `• ${selectedCard.last_four}` : ""} • {selectedCard.currency}
                          </p>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="w-8 h-8 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                          <X className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                        </div>
                        <span className="text-gray-500 dark:text-gray-400">No card assigned</span>
                      </>
                    )}
                    <ChevronDown className={cn(
                      "w-5 h-5 text-gray-400 dark:text-gray-500 transition-transform ml-auto",
                      isCardDropdownOpen && "rotate-180"
                    )} />
                  </button>

                  {/* Dropdown Menu - Opens upward */}
                  <AnimatePresence>
                    {isCardDropdownOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                        transition={{ duration: 0.15 }}
                        className="absolute z-[100] w-full bottom-full mb-2 py-2 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-100 dark:border-gray-700 max-h-64 overflow-y-auto"
                      >
                        {/* No card option */}
                        <button
                          type="button"
                          onClick={() => {
                            setCardId(null);
                            setIsCardDropdownOpen(false);
                          }}
                          className={cn(
                            "w-full px-4 py-2.5 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors",
                            !cardId && "bg-blue-50 dark:bg-blue-900/30"
                          )}
                        >
                          <div className="w-8 h-8 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                            <X className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                          </div>
                          <span className={cn(
                            "font-medium",
                            !cardId ? "text-blue-600 dark:text-blue-400" : "text-gray-700 dark:text-gray-300"
                          )}>No card assigned</span>
                        </button>

                        {/* Card options */}
                        {cards.map((card) => (
                          <button
                            key={card.id}
                            type="button"
                            onClick={() => {
                              setCardId(card.id);
                              setIsCardDropdownOpen(false);
                            }}
                            className={cn(
                              "w-full px-4 py-2.5 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors",
                              cardId === card.id && "bg-blue-50 dark:bg-blue-900/30"
                            )}
                          >
                            {card.icon_url ? (
                              <img
                                src={card.icon_url}
                                alt={card.bank_name}
                                className="w-8 h-8 rounded-lg object-contain bg-gray-50 dark:bg-gray-700"
                              />
                            ) : (
                              <div
                                className="w-8 h-8 rounded-lg flex items-center justify-center"
                                style={{ backgroundColor: card.color }}
                              >
                                <CreditCard className="w-4 h-4 text-white" />
                              </div>
                            )}
                            <div className="flex-1 min-w-0 text-left">
                              <p className={cn(
                                "font-medium truncate",
                                cardId === card.id ? "text-blue-600 dark:text-blue-400" : "text-gray-900 dark:text-gray-100"
                              )}>{card.name}</p>
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                {card.bank_name} {card.last_four ? `• ${card.last_four}` : ""} • {card.currency}
                              </p>
                            </div>
                          </button>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Click outside to close */}
                  {isCardDropdownOpen && (
                    <div
                      className="fixed inset-0 z-[99]"
                      onClick={() => setIsCardDropdownOpen(false)}
                    />
                  )}
                </div>
              </div>

              {/* Submit Button */}
              <motion.button
                type="submit"
                disabled={updateMutation.isPending}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={cn(
                  "w-full py-3 rounded-xl font-semibold transition-all duration-200",
                  "bg-gradient-to-r from-blue-500 to-indigo-500 text-white",
                  "hover:shadow-lg hover:shadow-blue-200 dark:hover:shadow-blue-900/50",
                  "disabled:opacity-50 disabled:cursor-not-allowed",
                  "flex items-center justify-center gap-2"
                )}
              >
                {updateMutation.isPending ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-5 h-5" />
                    <span>Save Changes</span>
                  </>
                )}
              </motion.button>

              {/* Error Message */}
              {updateMutation.isError && (
                <motion.p
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 text-sm text-red-600 dark:text-red-400 text-center"
                >
                  Failed to update subscription. Please try again.
                </motion.p>
              )}
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
