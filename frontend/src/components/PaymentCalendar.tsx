"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  format as formatDate,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  addMonths,
  subMonths,
  startOfWeek,
  endOfWeek,
  isToday as isTodayFn,
} from "date-fns";
import {
  ChevronLeft,
  ChevronRight,
  Calendar,
  TrendingUp,
  Coins,
  Sparkles,
  X,
  Check,
  Loader2,
  CreditCard,
} from "lucide-react";
import { calendarApi, CalendarEvent } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useCurrencyFormat } from "@/hooks/useCurrencyFormat";
import { findService, getIconUrl } from "@/lib/service-icons";

interface PaymentCalendarProps {
  onDateClick?: (date: Date, events: CalendarEvent[]) => void;
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.02,
    },
  },
};

const dayVariants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      type: "spring" as const,
      stiffness: 300,
      damping: 24,
    },
  },
};

export function PaymentCalendar({ onDateClick }: PaymentCalendarProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [noCardWarning, setNoCardWarning] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(currentMonth);
  const nextMonthStart = startOfMonth(addMonths(currentMonth, 1));
  const nextMonthEnd = endOfMonth(addMonths(currentMonth, 1));

  // Get currency formatting and conversion functions (must be before queries that use it)
  const { format: formatCurrency, convert, displayCurrency } = useCurrencyFormat();

  // Fetch calendar events for the current viewed month
  const { data: events = [], isLoading, dataUpdatedAt } = useQuery({
    queryKey: ["calendar-events", formatDate(monthStart, "yyyy-MM-dd"), formatDate(monthEnd, "yyyy-MM-dd")],
    queryFn: async () => {
      const startDate = formatDate(monthStart, "yyyy-MM-dd");
      const endDate = formatDate(monthEnd, "yyyy-MM-dd");
      console.log(`[Calendar] Fetching events for ${startDate} to ${endDate}`);
      const result = await calendarApi.getEvents(startDate, endDate);
      console.log(`[Calendar] Received ${result.length} events:`);
      result.forEach(e => {
        console.log(`  - ${e.payment_date}: ${e.name}, is_paid=${e.is_paid}, id=${e.id}`);
      });
      return result;
    },
    staleTime: 0, // Always consider data stale
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  });

  // Fetch calendar events for the NEXT month (relative to viewed month)
  const { data: nextMonthEvents = [] } = useQuery({
    queryKey: ["calendar-events", formatDate(nextMonthStart, "yyyy-MM-dd"), formatDate(nextMonthEnd, "yyyy-MM-dd")],
    queryFn: async () => {
      const startDate = formatDate(nextMonthStart, "yyyy-MM-dd");
      const endDate = formatDate(nextMonthEnd, "yyyy-MM-dd");
      return await calendarApi.getEvents(startDate, endDate);
    },
    staleTime: 0,
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  });

  // Log when events data changes
  console.log(`[Calendar] Query state: events=${events.length}, dataUpdatedAt=${dataUpdatedAt}, isLoading=${isLoading}`);

  // Group events by date
  const eventsByDate = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    events.forEach((event) => {
      const dateKey = event.payment_date;
      const existing = map.get(dateKey) || [];
      map.set(dateKey, [...existing, event]);
    });
    return map;
  }, [events]);

  // Get days to display (including padding for week alignment)
  const calendarDays = useMemo(() => {
    const start = startOfWeek(monthStart, { weekStartsOn: 1 }); // Monday
    const end = endOfWeek(monthEnd, { weekStartsOn: 1 });
    return eachDayOfInterval({ start, end });
  }, [monthStart, monthEnd]);

  const handlePrevMonth = () => setCurrentMonth(subMonths(currentMonth, 1));
  const handleNextMonth = () => setCurrentMonth(addMonths(currentMonth, 1));
  const handleToday = () => setCurrentMonth(new Date());

  // Calculate current viewed month total with proper currency conversion
  const monthlyTotal = useMemo(() => {
    return events.reduce((sum, event) => {
      const convertedAmount = convert(Number(event.amount), event.currency);
      return sum + convertedAmount;
    }, 0);
  }, [events, convert]);

  // Calculate next month total (relative to viewed month)
  const nextMonthTotal = useMemo(() => {
    return nextMonthEvents.reduce((sum, event) => {
      const convertedAmount = convert(Number(event.amount), event.currency);
      return sum + convertedAmount;
    }, 0);
  }, [nextMonthEvents, convert]);

  // Status counts
  const statusCounts = useMemo(() => {
    return events.reduce(
      (acc, event) => {
        acc[event.status] = (acc[event.status] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>
    );
  }, [events]);

  // Get events for the selected date from fresh query data
  const selectedDayEvents = useMemo(() => {
    if (!selectedDate) return [];
    const dateKey = formatDate(selectedDate, "yyyy-MM-dd");
    const dayEvents = eventsByDate.get(dateKey) || [];
    console.log(`[Calendar] Selected date ${dateKey} events:`, dayEvents.map(e => ({
      name: e.name,
      is_paid: e.is_paid,
      id: e.id
    })));
    return dayEvents;
  }, [selectedDate, eventsByDate]);

  // Mutation for recording a payment
  const recordPaymentMutation = useMutation({
    mutationFn: async ({ subscriptionId, paymentDate, amount }: { subscriptionId: string; paymentDate: string; amount: number }) => {
      console.log(`[Calendar] Recording payment: subscription=${subscriptionId}, date=${paymentDate}, amount=${amount}`);
      const result = await calendarApi.recordPayment(subscriptionId, {
        payment_date: paymentDate,
        amount,
        status: "completed",
      });
      console.log(`[Calendar] Payment recorded successfully:`, result);
      return result;
    },
    onSuccess: () => {
      console.log(`[Calendar] Mutation success - invalidating queries`);
      // Invalidate queries to refresh data (is_paid will come from API)
      queryClient.invalidateQueries({ queryKey: ["calendar-events"] });
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
      queryClient.invalidateQueries({ queryKey: ["cards"] });
      queryClient.invalidateQueries({ queryKey: ["payments-summary"] });
    },
    onError: (error) => {
      console.error(`[Calendar] Mutation error:`, error);
    },
  });

  // Mutation for deleting a payment (unmark as paid)
  const deletePaymentMutation = useMutation({
    mutationFn: async ({ subscriptionId, paymentDate }: { subscriptionId: string; paymentDate: string }) => {
      console.log(`[Calendar] Deleting payment: subscription=${subscriptionId}, date=${paymentDate}`);
      await calendarApi.deletePayment(subscriptionId, paymentDate);
      console.log(`[Calendar] Payment deleted successfully`);
    },
    onSuccess: () => {
      console.log(`[Calendar] Delete mutation success - invalidating queries`);
      queryClient.invalidateQueries({ queryKey: ["calendar-events"] });
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
      queryClient.invalidateQueries({ queryKey: ["cards"] });
      queryClient.invalidateQueries({ queryKey: ["payments-summary"] });
    },
    onError: (error) => {
      console.error(`[Calendar] Delete mutation error:`, error);
    },
  });

  // Handle toggling payment status
  const handleTogglePayment = (event: CalendarEvent) => {
    if (event.is_paid) {
      // Unmark as paid
      deletePaymentMutation.mutate({
        subscriptionId: event.id,
        paymentDate: event.payment_date,
      });
    } else {
      // Mark as paid - check if payment has a card assigned
      if (!event.card_id) {
        setNoCardWarning(event.id);
        setTimeout(() => setNoCardWarning(null), 3000);
        return;
      }
      recordPaymentMutation.mutate({
        subscriptionId: event.id,
        paymentDate: event.payment_date,
        amount: Number(event.amount),
      });
    }
  };

  return (
    <div className="glass-card rounded-3xl p-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8">
        <div className="flex items-center gap-4">
          <motion.div
            whileHover={{ scale: 1.05, rotate: 5 }}
            className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg"
          >
            <Calendar className="w-7 h-7 text-white" />
          </motion.div>
          <div>
            <motion.h2
              key={formatDate(currentMonth, "MMMM yyyy")}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-2xl font-bold text-gray-900"
            >
              {formatDate(currentMonth, "MMMM yyyy")}
            </motion.h2>
            <p className="text-sm text-gray-500">
              {events.length} payment{events.length !== 1 ? "s" : ""} scheduled
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <motion.button
            onClick={handlePrevMonth}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="p-2.5 rounded-xl glass-card-subtle hover:bg-white/80 transition-colors"
            aria-label="Previous month"
          >
            <ChevronLeft className="w-5 h-5 text-gray-600" />
          </motion.button>
          <motion.button
            onClick={handleToday}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="px-4 py-2 text-sm font-semibold rounded-xl bg-gradient-to-r from-purple-500 to-indigo-500 text-white shadow-md hover:shadow-lg transition-shadow"
          >
            Today
          </motion.button>
          <motion.button
            onClick={handleNextMonth}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="p-2.5 rounded-xl glass-card-subtle hover:bg-white/80 transition-colors"
            aria-label="Next month"
          >
            <ChevronRight className="w-5 h-5 text-gray-600" />
          </motion.button>
        </div>
      </div>

      {/* Monthly Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="p-4 rounded-2xl bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-100"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-500">
              <Coins className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-xs text-purple-600 font-medium">
                Total for {formatDate(currentMonth, "MMMM")}
              </p>
              <p className="text-xl font-bold text-purple-700">
                {formatCurrency(monthlyTotal, displayCurrency)}
              </p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="p-4 rounded-2xl bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-100"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-xs text-blue-600 font-medium">
                Due in {formatDate(addMonths(currentMonth, 1), "MMMM")}
              </p>
              <p className="text-xl font-bold text-blue-700">
                {formatCurrency(nextMonthTotal, displayCurrency)}
              </p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="p-4 rounded-2xl bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-100"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-xs text-amber-600 font-medium">Due Soon</p>
              <p className="text-xl font-bold text-amber-700">
                {statusCounts.due_soon || 0} payments
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Day Labels */}
      <div className="grid grid-cols-7 gap-2 mb-3">
        {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day, index) => (
          <motion.div
            key={day}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.03 }}
            className={cn(
              "text-center text-xs font-semibold py-2 rounded-lg",
              index >= 5 ? "text-purple-400 bg-purple-50/50" : "text-gray-400"
            )}
          >
            {day}
          </motion.div>
        ))}
      </div>

      {/* Calendar Grid */}
      {isLoading ? (
        <div className="grid grid-cols-7 gap-2">
          {Array.from({ length: 35 }).map((_, i) => (
            <div key={i} className="aspect-square rounded-2xl shimmer" />
          ))}
        </div>
      ) : (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-7 gap-2"
        >
          {calendarDays.map((date) => {
            const dateKey = formatDate(date, "yyyy-MM-dd");
            const dayEvents = eventsByDate.get(dateKey) || [];
            const isToday = isTodayFn(date);
            const isCurrentMonth = date.getMonth() === currentMonth.getMonth();

            return (
              <CalendarDay
                key={dateKey}
                date={date}
                events={dayEvents}
                isToday={isToday}
                isCurrentMonth={isCurrentMonth}
                onClick={() => {
                  if (dayEvents.length > 0) {
                    setSelectedDate(date);
                  }
                  onDateClick?.(date, dayEvents);
                }}
              />
            );
          })}
        </motion.div>
      )}

      {/* Legend */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-8 flex flex-wrap gap-6 justify-center"
      >
        <LegendItem color="from-emerald-400 to-emerald-500" label="Completed" />
        <LegendItem color="from-blue-400 to-blue-500" label="Upcoming" />
        <LegendItem color="from-amber-400 to-amber-500" label="Due Soon" />
        <LegendItem color="from-red-400 to-red-500" label="Overdue" />
      </motion.div>

      {/* Day Details Modal - Clean Modern Design */}
      <AnimatePresence>
        {selectedDate && selectedDayEvents.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
            onClick={() => setSelectedDate(null)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ type: "spring", damping: 30, stiffness: 400 }}
              className="bg-white rounded-2xl shadow-xl max-w-sm w-full overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Minimal Header */}
              <div className="px-5 pt-5 pb-4 border-b border-gray-100">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">
                      {formatDate(selectedDate, "EEEE")}
                    </p>
                    <h3 className="text-lg font-semibold text-gray-900 mt-0.5">
                      {formatDate(selectedDate, "MMMM d")}
                    </h3>
                  </div>
                  <button
                    onClick={() => setSelectedDate(null)}
                    className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <X className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              </div>

              {/* Payment List */}
              <div className="px-5 py-4 max-h-[50vh] overflow-y-auto">
                <div className="space-y-3">
                  {selectedDayEvents.map((event, index) => {
                    const serviceInfo = findService(event.name);
                    const brandColor = serviceInfo?.color || "#6366F1";
                    const iconUrl = serviceInfo?.iconUrl || (serviceInfo?.icon ? getIconUrl(serviceInfo.icon) : null);
                    const isPaid = event.is_paid;
                    const isRecording = recordPaymentMutation.isPending &&
                      recordPaymentMutation.variables?.subscriptionId === event.id &&
                      recordPaymentMutation.variables?.paymentDate === event.payment_date;
                    const isDeleting = deletePaymentMutation.isPending &&
                      deletePaymentMutation.variables?.subscriptionId === event.id &&
                      deletePaymentMutation.variables?.paymentDate === event.payment_date;
                    const isLoading = isRecording || isDeleting;
                    const hasNoCard = !event.card_id;
                    const showNoCardWarning = noCardWarning === event.id;

                    return (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.04 }}
                        className="relative"
                      >
                        <div className={cn(
                          "flex items-center gap-3",
                          isPaid && "opacity-60"
                        )}>
                          {/* Icon Container */}
                          <div
                            className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 overflow-hidden"
                            style={{ backgroundColor: iconUrl ? "#f8f9fa" : brandColor }}
                          >
                            {iconUrl ? (
                              <img
                                src={iconUrl}
                                alt={event.name}
                                className="w-5 h-5 object-contain"
                                onError={(e) => {
                                  const target = e.target as HTMLImageElement;
                                  target.style.display = "none";
                                  const parent = target.parentElement;
                                  if (parent) {
                                    parent.style.backgroundColor = brandColor;
                                    parent.innerHTML = `<span class="text-white font-medium text-sm">${event.name.charAt(0).toUpperCase()}</span>`;
                                  }
                                }}
                              />
                            ) : (
                              <span className="text-white font-medium text-sm">
                                {event.name.charAt(0).toUpperCase()}
                              </span>
                            )}
                          </div>

                          {/* Details */}
                          <div className="flex-1 min-w-0">
                            <p className={cn(
                              "text-sm font-medium truncate",
                              isPaid ? "text-gray-500 line-through" : "text-gray-900"
                            )}>{event.name}</p>
                            <p className="text-xs text-gray-400">
                              {event.is_installment && event.installment_number && event.total_installments
                                ? `${event.installment_number} of ${event.total_installments} payments`
                                : (serviceInfo?.category || "Subscription").charAt(0).toUpperCase() + (serviceInfo?.category || "subscription").slice(1)}
                            </p>
                          </div>

                          {/* Amount */}
                          <div className="text-right flex-shrink-0">
                            <p className={cn(
                              "text-sm font-semibold",
                              isPaid ? "text-gray-500 line-through" : "text-gray-900"
                            )}>
                              {formatCurrency(Number(event.amount), event.currency)}
                            </p>
                            <p className={cn(
                              "text-xs font-medium",
                              isPaid ? "text-emerald-600" :
                              event.status === "overdue" ? "text-red-500" :
                              isTodayFn(selectedDate) ? "text-amber-600" :
                              event.status === "due_soon" ? "text-amber-500" : "text-emerald-500"
                            )}>
                              {isPaid ? "Paid" :
                               event.status === "overdue" ? "Overdue" :
                               isTodayFn(selectedDate) ? "Due today" :
                               event.status === "due_soon" ? "Due soon" : "Upcoming"}
                            </p>
                          </div>

                          {/* Mark as Paid Checkbox - Right side */}
                          <motion.button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (!isLoading) {
                                handleTogglePayment(event);
                              }
                            }}
                            disabled={isLoading}
                            whileHover={!isLoading ? { scale: 1.1 } : {}}
                            whileTap={!isLoading ? { scale: 0.9 } : {}}
                            className={cn(
                              "w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 transition-all duration-200 border-2 ml-2",
                              isPaid
                                ? "bg-emerald-500 border-emerald-500 text-white hover:bg-emerald-600 hover:border-emerald-600"
                                : isLoading
                                  ? "bg-gray-100 border-gray-300"
                                  : hasNoCard
                                    ? "bg-gray-50 border-gray-200 hover:border-amber-400 hover:bg-amber-50"
                                    : "bg-white border-gray-200 hover:border-emerald-400 hover:bg-emerald-50"
                            )}
                            title={isPaid ? "Click to unmark as paid" : hasNoCard ? "Assign a card first" : "Mark as paid"}
                          >
                            {isLoading ? (
                              <Loader2 className="w-3.5 h-3.5 text-gray-400 animate-spin" />
                            ) : isPaid ? (
                              <Check className="w-3.5 h-3.5" />
                            ) : hasNoCard ? (
                              <CreditCard className="w-3.5 h-3.5 text-gray-400" />
                            ) : null}
                          </motion.button>
                        </div>

                        {/* No Card Warning */}
                        <AnimatePresence>
                          {showNoCardWarning && (
                            <motion.div
                              initial={{ opacity: 0, y: -5, height: 0 }}
                              animate={{ opacity: 1, y: 0, height: "auto" }}
                              exit={{ opacity: 0, y: -5, height: 0 }}
                              className="mt-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg"
                            >
                              <p className="text-xs text-amber-700 flex items-center gap-1.5">
                                <CreditCard className="w-3.5 h-3.5" />
                                Assign a payment card to mark as paid
                              </p>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </motion.div>
                    );
                  })}
                </div>
              </div>

              {/* Footer with Total */}
              <div className="px-5 py-4 bg-gray-50 border-t border-gray-100">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Total due</span>
                  <span className="text-base font-semibold text-gray-900">
                    {formatCurrency(
                      selectedDayEvents.reduce((sum, e) => sum + convert(Number(e.amount), e.currency), 0),
                      displayCurrency
                    )}
                  </span>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

interface CalendarDayProps {
  date: Date;
  events: CalendarEvent[];
  isToday: boolean;
  isCurrentMonth: boolean;
  onClick: () => void;
}

function CalendarDay({ date, events, isToday, isCurrentMonth, onClick }: CalendarDayProps) {
  const hasPayments = events.length > 0;
  const { format: formatCurrency, convert, displayCurrency } = useCurrencyFormat();

  // Convert all amounts to display currency before summing
  const totalAmount = useMemo(() => {
    return events.reduce((sum, e) => sum + convert(Number(e.amount), e.currency), 0);
  }, [events, convert]);

  // Check if all payments are completed
  const allPaid = useMemo(() => {
    const result = events.length > 0 && events.every((e) => e.is_paid);
    if (events.length > 0) {
      const dateKey = formatDate(date, "yyyy-MM-dd");
      console.log(`[CalendarDay] ${dateKey}: ${events.length} events, allPaid=${result}`,
        events.map(e => ({ name: e.name, is_paid: e.is_paid })));
    }
    return result;
  }, [events, date]);

  // Determine the dominant status for coloring
  const dominantStatus = useMemo(() => {
    if (allPaid) return "completed";
    if (events.some((e) => e.status === "overdue" && !e.is_paid)) return "overdue";
    if (events.some((e) => e.status === "due_soon" && !e.is_paid)) return "due_soon";
    return "upcoming";
  }, [events, allPaid]);

  const statusColors: Record<string, string> = {
    completed: "from-emerald-400 to-emerald-500",
    upcoming: "from-blue-400 to-blue-500",
    due_soon: "from-amber-400 to-amber-500",
    overdue: "from-red-400 to-red-500",
  };

  return (
    <motion.div
      variants={dayVariants}
      onClick={onClick}
      className={cn(
        "relative aspect-square p-2 rounded-2xl cursor-pointer transition-all duration-300",
        !isCurrentMonth && "opacity-30",
        isCurrentMonth && !isToday && "hover:shadow-lg hover:bg-white/90",
        hasPayments && isCurrentMonth && "hover:scale-105",
        isToday && "ring-2 ring-purple-500 ring-offset-2 shadow-lg"
      )}
      style={{
        background: isToday
          ? "linear-gradient(135deg, rgba(147, 51, 234, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%)"
          : isCurrentMonth
            ? hasPayments
              ? "rgba(255, 255, 255, 0.95)"
              : "rgba(255, 255, 255, 0.6)"
            : "rgba(255, 255, 255, 0.2)",
      }}
    >
      {/* Today indicator glow */}
      {isToday && (
        <motion.div
          className="absolute inset-0 rounded-2xl bg-gradient-to-br from-purple-400/20 to-indigo-400/20"
          animate={{ opacity: [0.5, 0.8, 0.5] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        />
      )}

      {/* Date number */}
      <div className="relative z-10">
        {isToday ? (
          <div className="flex items-center justify-center w-7 h-7 -ml-0.5 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 text-white text-sm font-bold shadow-md">
            {formatDate(date, "d")}
          </div>
        ) : (
          <div
            className={cn(
              "text-sm font-semibold mb-1",
              isCurrentMonth ? "text-gray-700" : "text-gray-400"
            )}
          >
            {formatDate(date, "d")}
          </div>
        )}
      </div>

      {/* Payment indicators */}
      {hasPayments && isCurrentMonth && (
        <AnimatePresence>
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className={cn("space-y-1 relative z-10", isToday && "mt-1")}
          >
            {/* Event dots */}
            <div className="flex gap-0.5 flex-wrap">
              {events.slice(0, 3).map((event, index) => (
                <motion.div
                  key={index}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: index * 0.05 }}
                  className={cn(
                    "w-2 h-2 rounded-full bg-gradient-to-r shadow-sm",
                    event.is_paid ? statusColors.completed : statusColors[event.status]
                  )}
                />
              ))}
              {events.length > 3 && (
                <span className="text-[10px] text-gray-500 ml-1">+{events.length - 3}</span>
              )}
            </div>

            {/* Total amount badge */}
            <div
              className={cn(
                "text-[10px] font-bold px-1.5 py-0.5 rounded-md",
                "bg-gradient-to-r text-white truncate shadow-sm",
                statusColors[dominantStatus]
              )}
            >
              {formatCurrency(totalAmount, displayCurrency)}
            </div>
          </motion.div>
        </AnimatePresence>
      )}
    </motion.div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className={cn("w-3 h-3 rounded-full bg-gradient-to-r", color)} />
      <span className="text-xs text-gray-600 font-medium">{label}</span>
    </div>
  );
}
