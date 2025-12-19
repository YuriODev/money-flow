"use client";

import { useState, useMemo, useEffect, useRef } from "react";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  subscriptionApi,
  userApi,
  type SubscriptionCreate,
  type PaymentMode,
  PAYMENT_MODE_LABELS,
  PAYMENT_MODE_ICONS,
} from "@/lib/api";
import {
  X,
  Plus,
  Sparkles,
  Calendar,
  Coins,
  FolderOpen,
  Search,
  Check,
  CreditCard,
  PiggyBank,
  User,
} from "lucide-react";
import {
  SERVICES,
  findService,
  getIconUrl,
  CATEGORY_INFO,
  type ServiceInfo,
} from "@/lib/service-icons";
import { cn } from "@/lib/utils";
import { toast } from "@/components/Toast";
import { CategorySelector } from "@/components/CategorySelector";

interface AddSubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

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
    transition: {
      type: "spring" as const,
      stiffness: 300,
      damping: 25,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.9,
    y: 20,
    transition: { duration: 0.2 },
  },
};

const inputVariants = {
  focus: { scale: 1.02, transition: { duration: 0.2 } },
  blur: { scale: 1, transition: { duration: 0.2 } },
};

// Service suggestion item
function ServiceSuggestion({
  service,
  isSelected,
  onClick,
}: {
  service: ServiceInfo;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={cn(
        "flex items-center gap-3 w-full p-3 rounded-xl transition-all duration-200",
        isSelected
          ? "bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/30 dark:to-indigo-900/30 border-2 border-blue-200 dark:border-blue-700"
          : "hover:bg-gray-50 dark:hover:bg-gray-800 border-2 border-transparent"
      )}
    >
      {(service.icon || service.iconUrl) ? (
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center shadow-sm"
          style={{ backgroundColor: `${service.color}15` }}
        >
          <img
            src={service.iconUrl || getIconUrl(service.icon)}
            alt={service.name}
            className="w-6 h-6"
            style={{ filter: `drop-shadow(0 1px 2px ${service.color}40)` }}
          />
        </div>
      ) : (
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold shadow-sm"
          style={{ background: `linear-gradient(135deg, ${service.color} 0%, ${service.color}cc 100%)` }}
        >
          {service.name.charAt(0).toUpperCase()}
        </div>
      )}
      <div className="flex-1 text-left">
        <p className="font-medium text-gray-900 dark:text-gray-100">{service.name}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{service.category}</p>
      </div>
      {isSelected && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="w-6 h-6 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-center"
        >
          <Check className="w-4 h-4 text-white" />
        </motion.div>
      )}
    </motion.button>
  );
}

// Quick service picker (popular services)
function QuickServicePicker({
  onSelect,
  selectedName,
}: {
  onSelect: (service: ServiceInfo) => void;
  selectedName: string;
}) {
  const popularServices = [
    "netflix",
    "spotify",
    "youtube",
    "disneyplus",
    "amazon",
    "chatgpt",
    "github",
    "figma",
  ];

  return (
    <div className="flex flex-wrap gap-2">
      {popularServices.map((key) => {
        const service = SERVICES[key];
        if (!service) return null;
        const isSelected =
          selectedName.toLowerCase() === service.name.toLowerCase();

        return (
          <motion.button
            key={key}
            type="button"
            onClick={() => onSelect(service)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-xl transition-all duration-200",
              isSelected
                ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-lg"
                : "glass-card-subtle hover:shadow-md"
            )}
          >
            <img
              src={getIconUrl(service.icon)}
              alt={service.name}
              className={cn("w-4 h-4", isSelected && "brightness-0 invert")}
            />
            <span className="text-sm font-medium">{service.name}</span>
          </motion.button>
        );
      })}
    </div>
  );
}

export function AddSubscriptionModal({
  isOpen,
  onClose,
}: AddSubscriptionModalProps) {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedService, setSelectedService] = useState<ServiceInfo | null>(
    null
  );

  // Fetch user preferences for default card and category
  const { data: preferences } = useQuery({
    queryKey: ["user-preferences"],
    queryFn: () => userApi.getPreferences(),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  const [formData, setFormData] = useState<SubscriptionCreate>({
    name: "",
    amount: 0,
    currency: "GBP",
    frequency: "monthly",
    start_date: new Date().toISOString().split("T")[0],
    payment_mode: "recurring",
    category: "",
    category_id: null,
    card_id: undefined,
    // Debt fields
    total_owed: undefined,
    remaining_balance: undefined,
    creditor: undefined,
    // Savings fields
    target_amount: undefined,
    current_saved: undefined,
    recipient: undefined,
  });

  // Apply default card and category when preferences load
  useEffect(() => {
    if (preferences && isOpen) {
      setFormData((prev) => ({
        ...prev,
        card_id: prev.card_id || preferences.default_card_id || undefined,
        category_id: prev.category_id || preferences.default_category_id || null,
      }));
    }
  }, [preferences, isOpen]);

  // Filter services based on search
  const filteredServices = useMemo(() => {
    if (!searchQuery.trim()) return [];

    const query = searchQuery.toLowerCase();
    return Object.values(SERVICES)
      .filter(
        (service) =>
          service.name.toLowerCase().includes(query) ||
          service.aliases.some((alias) => alias.includes(query)) ||
          service.category.includes(query)
      )
      .slice(0, 5);
  }, [searchQuery]);

  // Auto-detect service when name changes
  useEffect(() => {
    if (formData.name && !selectedService) {
      const detected = findService(formData.name);
      if (detected) {
        setSelectedService(detected);
        if (!formData.category) {
          const categoryInfo = CATEGORY_INFO[detected.category];
          setFormData((prev) => ({
            ...prev,
            category: categoryInfo?.label || detected.category,
          }));
        }
      }
    }
  }, [formData.name, selectedService, formData.category]);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const handleServiceSelect = (service: ServiceInfo) => {
    setSelectedService(service);
    setFormData((prev) => ({
      ...prev,
      name: service.name,
      category: CATEGORY_INFO[service.category]?.label || service.category,
    }));
    setSearchQuery("");
    setShowSuggestions(false);
  };

  const createMutation = useMutation({
    mutationFn: (data: SubscriptionCreate) => subscriptionApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
      queryClient.invalidateQueries({ queryKey: ["calendar-events"] });
      toast.success("Payment added", `${formData.name} has been added to your payments.`);
      onClose();
      // Reset form - defaults will be applied by useEffect when modal reopens
      setFormData({
        name: "",
        amount: 0,
        currency: preferences?.currency || "GBP",
        frequency: "monthly",
        start_date: new Date().toISOString().split("T")[0],
        payment_mode: "recurring",
        category: "",
        category_id: null,
        card_id: undefined,
        total_owed: undefined,
        remaining_balance: undefined,
        creditor: undefined,
        target_amount: undefined,
        current_saved: undefined,
        recipient: undefined,
      });
      setSelectedService(null);
      setSearchQuery("");
    },
    onError: () => {
      toast.error("Failed to add payment", "There was an error adding the payment. Please try again.");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  const handleClose = () => {
    onClose();
    setShowSuggestions(false);
    setSearchQuery("");
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          variants={backdropVariants}
          initial="hidden"
          animate="visible"
          exit="hidden"
          onClick={handleClose}
          className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 z-50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="add-payment-title"
        >
          <motion.div
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={(e) => e.stopPropagation()}
            className="glass-card rounded-3xl max-w-lg w-full p-8 shadow-2xl overflow-hidden relative"
          >
            {/* Decorative gradient orbs */}
            <div className="absolute -top-20 -right-20 w-40 h-40 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full opacity-20 blur-3xl" />
            <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-gradient-to-br from-pink-400 to-orange-500 rounded-full opacity-20 blur-3xl" />

            {/* Header */}
            <div className="relative flex justify-between items-center mb-8">
              <div className="flex items-center gap-3">
                <motion.div
                  whileHover={{ scale: 1.1, rotate: 10 }}
                  className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg"
                  aria-hidden="true"
                >
                  <Plus className="w-6 h-6 text-white" />
                </motion.div>
                <div>
                  <h2 id="add-payment-title" className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    Add Payment
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Track your recurring payments
                  </p>
                </div>
              </div>
              <motion.button
                onClick={handleClose}
                whileHover={{ scale: 1.1, rotate: 90 }}
                whileTap={{ scale: 0.9 }}
                className="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                aria-label="Close modal"
              >
                <X className="w-6 h-6 text-gray-400 dark:text-gray-500" aria-hidden="true" />
              </motion.button>
            </div>

            {/* Payment Mode Selector */}
            <fieldset className="relative mb-6">
              <legend className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
                Payment Mode
              </legend>
              <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Select payment mode">
                {(Object.keys(PAYMENT_MODE_LABELS) as PaymentMode[]).map((mode) => (
                  <motion.button
                    key={mode}
                    type="button"
                    onClick={() => setFormData({ ...formData, payment_mode: mode })}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2 rounded-xl transition-all duration-200",
                      formData.payment_mode === mode
                        ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-lg"
                        : "glass-card-subtle hover:shadow-md"
                    )}
                    role="radio"
                    aria-checked={formData.payment_mode === mode}
                  >
                    <span aria-hidden="true">{PAYMENT_MODE_ICONS[mode]}</span>
                    <span className="text-sm font-medium">{PAYMENT_MODE_LABELS[mode]}</span>
                  </motion.button>
                ))}
              </div>
            </fieldset>

            {/* Quick picks - only show for recurring payments */}
            {formData.payment_mode === "recurring" && (
              <div className="relative mb-6">
                <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Popular Services
                </p>
                <QuickServicePicker
                  onSelect={handleServiceSelect}
                  selectedName={formData.name}
                />
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="relative space-y-5" aria-label="Add payment form">
              {/* Service name with autocomplete */}
              <div className="relative">
                <label htmlFor="service-name" className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <Search className="w-4 h-4" aria-hidden="true" />
                  Service Name
                </label>
                <div className="relative">
                  <motion.input
                    ref={inputRef}
                    id="service-name"
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => {
                      setFormData({ ...formData, name: e.target.value });
                      setSearchQuery(e.target.value);
                      setShowSuggestions(true);
                      if (!e.target.value) setSelectedService(null);
                    }}
                    onFocus={() => setShowSuggestions(true)}
                    onBlur={() =>
                      setTimeout(() => setShowSuggestions(false), 200)
                    }
                    variants={inputVariants}
                    whileFocus="focus"
                    className={cn(
                      "w-full px-4 py-3 rounded-xl border-2 transition-all duration-200 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500",
                      "focus:ring-0 focus:border-blue-400 dark:focus:border-blue-500 focus:shadow-lg focus:shadow-blue-100 dark:focus:shadow-blue-900/50",
                      selectedService
                        ? "border-green-200 dark:border-green-700 bg-green-50/50 dark:bg-green-900/20"
                        : "border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50"
                    )}
                    placeholder="Netflix, Spotify, etc."
                    aria-required="true"
                    aria-autocomplete="list"
                    aria-expanded={showSuggestions && filteredServices.length > 0}
                    aria-controls="service-suggestions"
                  />
                  {selectedService && (
                    <motion.div
                      initial={{ scale: 0, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="absolute right-3 top-1/2 -translate-y-1/2"
                    >
                      {(selectedService.icon || selectedService.iconUrl) ? (
                        <img
                          src={selectedService.iconUrl || getIconUrl(selectedService.icon)}
                          alt={selectedService.name}
                          className="w-6 h-6"
                        />
                      ) : (
                        <div
                          className="w-6 h-6 rounded-md flex items-center justify-center text-white text-xs font-bold"
                          style={{ backgroundColor: selectedService.color }}
                        >
                          {selectedService.name.charAt(0).toUpperCase()}
                        </div>
                      )}
                    </motion.div>
                  )}
                </div>

                {/* Suggestions dropdown */}
                <AnimatePresence>
                  {showSuggestions && filteredServices.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      id="service-suggestions"
                      className="absolute z-50 w-full mt-2 p-2 glass-card rounded-2xl shadow-xl max-h-64 overflow-y-auto"
                      role="listbox"
                      aria-label="Service suggestions"
                    >
                      {filteredServices.map((service) => (
                        <ServiceSuggestion
                          key={service.name}
                          service={service}
                          isSelected={selectedService?.name === service.name}
                          onClick={() => handleServiceSelect(service)}
                        />
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Amount and Currency */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="payment-amount" className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    <Coins className="w-4 h-4" aria-hidden="true" />
                    Amount
                  </label>
                  <motion.input
                    id="payment-amount"
                    type="number"
                    required
                    step="0.01"
                    min="0"
                    value={formData.amount || ""}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        amount: parseFloat(e.target.value) || 0,
                      })
                    }
                    variants={inputVariants}
                    whileFocus="focus"
                    className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-0 focus:border-blue-400 dark:focus:border-blue-500 focus:shadow-lg focus:shadow-blue-100 dark:focus:shadow-blue-900/50 transition-all duration-200"
                    placeholder="15.99"
                    aria-required="true"
                  />
                </div>
                <div>
                  <label htmlFor="payment-currency" className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                    Currency
                  </label>
                  <motion.select
                    id="payment-currency"
                    value={formData.currency}
                    onChange={(e) =>
                      setFormData({ ...formData, currency: e.target.value })
                    }
                    variants={inputVariants}
                    whileFocus="focus"
                    className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 focus:ring-0 focus:border-blue-400 dark:focus:border-blue-500 focus:shadow-lg focus:shadow-blue-100 dark:focus:shadow-blue-900/50 transition-all duration-200"
                  >
                    <option value="GBP">£ GBP</option>
                    <option value="USD">$ USD</option>
                    <option value="EUR">€ EUR</option>
                    <option value="UAH">₴ UAH</option>
                  </motion.select>
                </div>
              </div>

              {/* Frequency */}
              <fieldset>
                <legend className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <Calendar className="w-4 h-4" aria-hidden="true" />
                  Billing Frequency
                </legend>
                <div className="grid grid-cols-3 gap-2" role="radiogroup" aria-label="Select billing frequency">
                  {[
                    { value: "monthly", label: "Monthly" },
                    { value: "yearly", label: "Yearly" },
                    { value: "weekly", label: "Weekly" },
                  ].map((option) => (
                    <motion.button
                      key={option.value}
                      type="button"
                      onClick={() =>
                        setFormData({ ...formData, frequency: option.value })
                      }
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className={cn(
                        "py-3 rounded-xl font-medium transition-all duration-200",
                        formData.frequency === option.value
                          ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-lg"
                          : "glass-card-subtle text-gray-600 dark:text-gray-300 hover:shadow-md"
                      )}
                      role="radio"
                      aria-checked={formData.frequency === option.value}
                    >
                      {option.label}
                    </motion.button>
                  ))}
                </div>
              </fieldset>

              {/* Category */}
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <FolderOpen className="w-4 h-4" aria-hidden="true" />
                  Category
                </label>
                <CategorySelector
                  value={formData.category_id || null}
                  onChange={(categoryId, categoryName) =>
                    setFormData({
                      ...formData,
                      category_id: categoryId,
                      category: categoryName || "",
                    })
                  }
                />
              </div>

              {/* Debt-specific fields */}
              {formData.payment_mode === "debt" && (
                <motion.fieldset
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-4 p-4 rounded-xl bg-red-50/50 dark:bg-red-900/20 border-2 border-red-100 dark:border-red-800"
                >
                  <legend className="text-sm font-semibold text-red-700 dark:text-red-400 flex items-center gap-2">
                    <CreditCard className="w-4 h-4" aria-hidden="true" />
                    Debt Details
                  </legend>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="total-owed" className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                        Total Owed
                      </label>
                      <motion.input
                        id="total-owed"
                        type="number"
                        step="0.01"
                        min="0"
                        value={formData.total_owed || ""}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            total_owed: parseFloat(e.target.value) || undefined,
                          })
                        }
                        variants={inputVariants}
                        whileFocus="focus"
                        className="w-full px-4 py-3 rounded-xl border-2 border-red-200 dark:border-red-700 bg-white/50 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-0 focus:border-red-400 dark:focus:border-red-500 focus:shadow-lg focus:shadow-red-100 dark:focus:shadow-red-900/50 transition-all duration-200"
                        placeholder="5000.00"
                      />
                    </div>
                    <div>
                      <label htmlFor="remaining-balance" className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                        Remaining Balance
                      </label>
                      <motion.input
                        id="remaining-balance"
                        type="number"
                        step="0.01"
                        min="0"
                        value={formData.remaining_balance || ""}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            remaining_balance: parseFloat(e.target.value) || undefined,
                          })
                        }
                        variants={inputVariants}
                        whileFocus="focus"
                        className="w-full px-4 py-3 rounded-xl border-2 border-red-200 dark:border-red-700 bg-white/50 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-0 focus:border-red-400 dark:focus:border-red-500 focus:shadow-lg focus:shadow-red-100 dark:focus:shadow-red-900/50 transition-all duration-200"
                        placeholder="3500.00"
                      />
                    </div>
                  </div>
                  <div>
                    <label htmlFor="creditor" className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      <User className="w-4 h-4" aria-hidden="true" />
                      Creditor
                    </label>
                    <motion.input
                      id="creditor"
                      type="text"
                      value={formData.creditor || ""}
                      onChange={(e) =>
                        setFormData({ ...formData, creditor: e.target.value || undefined })
                      }
                      variants={inputVariants}
                      whileFocus="focus"
                      className="w-full px-4 py-3 rounded-xl border-2 border-red-200 dark:border-red-700 bg-white/50 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-0 focus:border-red-400 dark:focus:border-red-500 focus:shadow-lg focus:shadow-red-100 dark:focus:shadow-red-900/50 transition-all duration-200"
                      placeholder="Bank name, friend, etc."
                    />
                  </div>
                </motion.fieldset>
              )}

              {/* Savings-specific fields */}
              {formData.payment_mode === "savings" && (
                <motion.fieldset
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-4 p-4 rounded-xl bg-green-50/50 dark:bg-green-900/20 border-2 border-green-100 dark:border-green-800"
                >
                  <legend className="text-sm font-semibold text-green-700 dark:text-green-400 flex items-center gap-2">
                    <PiggyBank className="w-4 h-4" aria-hidden="true" />
                    Savings Goal
                  </legend>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="target-amount" className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                        Target Amount
                      </label>
                      <motion.input
                        id="target-amount"
                        type="number"
                        step="0.01"
                        min="0"
                        value={formData.target_amount || ""}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            target_amount: parseFloat(e.target.value) || undefined,
                          })
                        }
                        variants={inputVariants}
                        whileFocus="focus"
                        className="w-full px-4 py-3 rounded-xl border-2 border-green-200 dark:border-green-700 bg-white/50 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-0 focus:border-green-400 dark:focus:border-green-500 focus:shadow-lg focus:shadow-green-100 dark:focus:shadow-green-900/50 transition-all duration-200"
                        placeholder="10000.00"
                      />
                    </div>
                    <div>
                      <label htmlFor="current-saved" className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                        Current Saved
                      </label>
                      <motion.input
                        id="current-saved"
                        type="number"
                        step="0.01"
                        min="0"
                        value={formData.current_saved || ""}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            current_saved: parseFloat(e.target.value) || undefined,
                          })
                        }
                        variants={inputVariants}
                        whileFocus="focus"
                        className="w-full px-4 py-3 rounded-xl border-2 border-green-200 dark:border-green-700 bg-white/50 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-0 focus:border-green-400 dark:focus:border-green-500 focus:shadow-lg focus:shadow-green-100 dark:focus:shadow-green-900/50 transition-all duration-200"
                        placeholder="2500.00"
                      />
                    </div>
                  </div>
                  <div>
                    <label htmlFor="recipient" className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      <User className="w-4 h-4" aria-hidden="true" />
                      Recipient
                    </label>
                    <motion.input
                      id="recipient"
                      type="text"
                      value={formData.recipient || ""}
                      onChange={(e) =>
                        setFormData({ ...formData, recipient: e.target.value || undefined })
                      }
                      variants={inputVariants}
                      whileFocus="focus"
                      className="w-full px-4 py-3 rounded-xl border-2 border-green-200 dark:border-green-700 bg-white/50 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-0 focus:border-green-400 dark:focus:border-green-500 focus:shadow-lg focus:shadow-green-100 dark:focus:shadow-green-900/50 transition-all duration-200"
                      placeholder="Savings account, family member, etc."
                    />
                  </div>
                </motion.fieldset>
              )}

              {/* Submit buttons */}
              <div className="flex gap-3 pt-4">
                <motion.button
                  type="button"
                  onClick={handleClose}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex-1 px-6 py-3 rounded-xl border-2 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  Cancel
                </motion.button>
                <motion.button
                  type="submit"
                  disabled={createMutation.isPending}
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  className={cn(
                    "flex-1 px-6 py-3 rounded-xl font-semibold text-white shadow-lg transition-all duration-200",
                    "bg-gradient-to-r from-blue-500 to-indigo-600 hover:shadow-xl",
                    createMutation.isPending && "opacity-50 cursor-not-allowed"
                  )}
                >
                  {createMutation.isPending ? (
                    <motion.span
                      animate={{ opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      Adding...
                    </motion.span>
                  ) : (
                    `Add ${PAYMENT_MODE_LABELS[formData.payment_mode || "recurring"]} Payment`
                  )}
                </motion.button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
