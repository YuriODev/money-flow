import axios, { AxiosError } from "axios";

// API Version - update this when migrating to new versions
const API_VERSION = "v1";

// Use relative path for API calls - Next.js will proxy to backend
const API_URL = typeof window === 'undefined'
  ? process.env.BACKEND_URL || "http://backend:8000"
  : "";  // Empty string means relative path from browser

export const api = axios.create({
  baseURL: `${API_URL}/api/${API_VERSION}`,
  headers: {
    "Content-Type": "application/json",
    "X-API-Version": "1",
  },
});

// API Response envelope types (for new standardized format)
export interface APIErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface APIResponse<T = unknown> {
  success: boolean;
  data?: T;
  meta?: {
    request_id?: string;
    timestamp?: string;
  };
  error?: APIErrorDetail;
  message?: string;
}

// Custom error class for API errors
export class APIError extends Error {
  code: string;
  details?: Record<string, unknown>;
  requestId?: string;

  constructor(
    message: string,
    code: string = "UNKNOWN_ERROR",
    details?: Record<string, unknown>,
    requestId?: string
  ) {
    super(message);
    this.name = "APIError";
    this.code = code;
    this.details = details;
    this.requestId = requestId;
  }
}

// Response interceptor to handle both old and new API formats
api.interceptors.response.use(
  (response) => {
    // Check if response follows new envelope format
    const data = response.data;
    if (data && typeof data === "object" && "success" in data) {
      // New format: { success, data, meta, error }
      if (data.success === false && data.error) {
        // Convert to error
        const error = new APIError(
          data.error.message || "An error occurred",
          data.error.code || "UNKNOWN_ERROR",
          data.error.details,
          data.meta?.request_id
        );
        return Promise.reject(error);
      }
      // Success: return unwrapped data for backwards compatibility
      // Only unwrap if 'data' key exists, otherwise return as-is
      if ("data" in data && data.data !== undefined) {
        response.data = data.data;
      }
    }
    return response;
  },
  (error: AxiosError<APIResponse>) => {
    // Handle error responses with new format
    if (error.response?.data) {
      const data = error.response.data;

      // Check for new error format
      if (data.error) {
        return Promise.reject(
          new APIError(
            data.error.message || "An error occurred",
            data.error.code || "UNKNOWN_ERROR",
            data.error.details,
            data.meta?.request_id
          )
        );
      }

      // Check for old format with 'detail'
      if ("detail" in data) {
        const detail = (data as Record<string, unknown>).detail;
        return Promise.reject(
          new APIError(
            typeof detail === "string" ? detail : JSON.stringify(detail),
            "HTTP_ERROR"
          )
        );
      }
    }

    // Network or other errors
    return Promise.reject(
      new APIError(
        error.message || "Network error",
        "NETWORK_ERROR"
      )
    );
  }
);

// Payment type enum for Money Flow
export type PaymentType =
  | "subscription"
  | "housing"
  | "utility"
  | "professional_service"
  | "insurance"
  | "debt"
  | "savings"
  | "transfer"
  | "one_time";

// Payment type display names
export const PAYMENT_TYPE_LABELS: Record<PaymentType, string> = {
  subscription: "Subscription",
  housing: "Housing",
  utility: "Utility",
  professional_service: "Professional Service",
  insurance: "Insurance",
  debt: "Debt",
  savings: "Savings",
  transfer: "Transfer",
  one_time: "One-Time",
};

// Payment type icons (emoji for now, can be replaced with icons)
export const PAYMENT_TYPE_ICONS: Record<PaymentType, string> = {
  subscription: "📺",
  housing: "🏠",
  utility: "💡",
  professional_service: "👨‍⚕️",
  insurance: "🛡️",
  debt: "💳",
  savings: "🐷",
  transfer: "💸",
  one_time: "📌",
};

export interface Subscription {
  id: string;
  name: string;
  amount: string;
  currency: string;
  frequency: string;
  frequency_interval: number;
  start_date: string;
  next_payment_date: string;
  last_payment_date: string | null;
  // Payment type classification (Money Flow)
  payment_type: PaymentType;
  category: string | null;
  is_active: boolean;
  notes: string | null;
  payment_method: string | null;
  reminder_days: number;
  icon_url: string | null;
  color: string;
  auto_renew: boolean;
  is_installment: boolean;
  total_installments: number | null;
  completed_installments: number;
  installment_start_date: string | null;
  installment_end_date: string | null;
  days_until_payment: number;
  payment_status_label: string;
  installments_remaining: number | null;
  // Debt-specific fields (for payment_type === "debt")
  total_owed: string | null;
  remaining_balance: string | null;
  creditor: string | null;
  // Savings-specific fields (for payment_type === "savings" or "transfer")
  target_amount: string | null;
  current_saved: string | null;
  recipient: string | null;
  // Computed progress fields
  debt_paid_percentage: number | null;
  savings_progress_percentage: number | null;
  // Payment card link
  card_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionCreate {
  name: string;
  amount: number;
  currency?: string;
  frequency: string;
  frequency_interval?: number;
  start_date: string;
  // Payment type classification (Money Flow)
  payment_type?: PaymentType;
  category?: string;
  notes?: string;
  // Debt-specific fields
  total_owed?: number;
  remaining_balance?: number;
  creditor?: string;
  // Savings-specific fields
  target_amount?: number;
  current_saved?: number;
  recipient?: string;
  // Payment card link
  card_id?: string | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AgentResponse {
  success: boolean;
  message: string;
  data?: any;
}

export interface SubscriptionSummary {
  total_monthly: number;
  total_yearly: number;
  active_count: number;
  by_category: Record<string, number>;
  by_payment_type: Record<string, number>;
  upcoming_week: Subscription[];
  currency: string;
  // Debt and savings totals (Money Flow)
  total_debt: number;
  total_savings_target: number;
  total_current_saved: number;
}

export const subscriptionApi = {
  getAll: async (paymentType?: PaymentType): Promise<Subscription[]> => {
    const params = paymentType ? { payment_type: paymentType } : {};
    const { data } = await api.get("/subscriptions", { params });
    return data;
  },

  getById: async (id: string): Promise<Subscription> => {
    const { data } = await api.get(`/subscriptions/${id}`);
    return data;
  },

  create: async (subscription: SubscriptionCreate): Promise<Subscription> => {
    const { data } = await api.post("/subscriptions", subscription);
    return data;
  },

  update: async (id: string, subscription: Partial<SubscriptionCreate>): Promise<Subscription> => {
    const { data } = await api.put(`/subscriptions/${id}`, subscription);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/subscriptions/${id}`);
  },

  getSummary: async (): Promise<SubscriptionSummary> => {
    const { data } = await api.get("/subscriptions/summary");
    return data;
  },
};

export const agentApi = {
  execute: async (command: string, history: ChatMessage[] = []): Promise<AgentResponse> => {
    const { data } = await api.post("/agent/execute", { command, history });
    return data;
  },
};

// Calendar types
export interface CalendarEvent {
  id: string;
  name: string;
  amount: string;
  currency: string;
  payment_date: string;
  payment_type: PaymentType;
  color: string;
  icon_url: string | null;
  category: string | null;
  is_installment: boolean;
  installment_number: number | null;
  total_installments: number | null;
  status: "upcoming" | "due_soon" | "overdue";
  card_id: string | null;
  is_paid: boolean;
}

export interface PaymentHistory {
  id: string;
  subscription_id: string;
  payment_date: string;
  amount: string;
  currency: string;
  status: "completed" | "pending" | "failed" | "cancelled";
  payment_method: string | null;
  installment_number: number | null;
  notes: string | null;
  created_at: string;
}

export interface MonthlySummary {
  year: number;
  month: number;
  total_paid: number;
  total_pending: number;
  total_failed: number;
  payment_count: number;
  completed_count: number;
  pending_count: number;
  failed_count: number;
}

// Unified monthly payments summary for Calendar and Cards dashboard
export interface MonthlyPaymentsSummary {
  current_month_total: string;
  current_month_paid: string;
  current_month_remaining: string;
  next_month_total: string;
  payment_count_this_month: number;
  payment_count_next_month: number;
  currency: string;
}

export interface RecordPaymentRequest {
  payment_date: string;
  amount: number;
  status?: "completed" | "pending" | "failed" | "cancelled";
  payment_method?: string;
  notes?: string;
}

// Import/Export types
export interface ExportData {
  version: string;
  exported_at: string;
  subscription_count: number;
  subscriptions: SubscriptionExport[];
}

export interface SubscriptionExport {
  name: string;
  amount: string;
  currency: string;
  frequency: string;
  frequency_interval: number;
  start_date: string;
  next_payment_date: string;
  payment_type: string;
  category: string | null;
  notes: string | null;
  is_active: boolean;
  payment_method: string | null;
  reminder_days: number;
  icon_url: string | null;
  color: string;
  auto_renew: boolean;
  is_installment: boolean;
  total_installments: number | null;
  completed_installments: number;
  // Debt-specific fields (Money Flow)
  total_owed: string | null;
  remaining_balance: string | null;
  creditor: string | null;
  // Savings-specific fields (Money Flow)
  target_amount: string | null;
  current_saved: string | null;
  recipient: string | null;
}

export interface ImportResult {
  total: number;
  imported: number;
  skipped: number;
  failed: number;
  errors: string[];
}

export const importExportApi = {
  exportJson: async (includeInactive = true): Promise<ExportData> => {
    const { data } = await api.get("/subscriptions/export/json", {
      params: { include_inactive: includeInactive },
    });
    return data;
  },

  exportCsv: async (includeInactive = true): Promise<Blob> => {
    const response = await api.get("/subscriptions/export/csv", {
      params: { include_inactive: includeInactive },
      responseType: "blob",
    });
    return response.data;
  },

  importJson: async (file: File, skipDuplicates = true): Promise<ImportResult> => {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await api.post("/subscriptions/import/json", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      params: { skip_duplicates: skipDuplicates },
    });
    return data;
  },

  importCsv: async (file: File, skipDuplicates = true): Promise<ImportResult> => {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await api.post("/subscriptions/import/csv", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      params: { skip_duplicates: skipDuplicates },
    });
    return data;
  },
};

// Payment Cards types
export type CardType = "debit" | "credit" | "prepaid" | "bank_account";

export interface FundingCardInfo {
  id: string;
  name: string;
  color: string;
  icon_url: string | null;
}

export interface PaymentCard {
  id: string;
  name: string;
  card_type: CardType;
  last_four: string | null;
  bank_name: string;
  currency: string;
  color: string;
  icon_url: string | null;
  is_active: boolean;
  notes: string | null;
  sort_order: number;
  funding_card_id: string | null;
  funding_card: FundingCardInfo | null;
  created_at: string;
  updated_at: string;
}

export interface PaymentCardCreate {
  name: string;
  card_type?: CardType;
  last_four?: string;
  bank_name: string;
  currency?: string;
  color?: string;
  icon_url?: string;
  notes?: string;
  sort_order?: number;
  funding_card_id?: string | null;
}

export interface CardBalanceSummary {
  card_id: string;
  card_name: string;
  bank_name: string;
  color: string;
  icon_url: string | null;
  currency: string;
  total_this_month: string;
  funded_this_month: string;
  paid_this_month: string;
  remaining_this_month: string;
  total_next_month: string;
  funded_next_month: string;
  subscription_count: number;
  funded_subscription_count: number;
  subscriptions: string[];
  funded_subscriptions: string[];
}

export interface AllCardsBalanceSummary {
  cards: CardBalanceSummary[];
  total_all_cards_this_month: string;
  total_paid_this_month: string;
  total_remaining_this_month: string;
  total_all_cards_next_month: string;
  unassigned_count: number;
  unassigned_total: string;
}

export const cardsApi = {
  getAll: async (): Promise<PaymentCard[]> => {
    const { data } = await api.get("/cards");
    return data;
  },

  getById: async (id: string): Promise<PaymentCard> => {
    const { data } = await api.get(`/cards/${id}`);
    return data;
  },

  create: async (card: PaymentCardCreate): Promise<PaymentCard> => {
    const { data } = await api.post("/cards", card);
    return data;
  },

  update: async (id: string, card: Partial<PaymentCardCreate>): Promise<PaymentCard> => {
    const { data } = await api.patch(`/cards/${id}`, card);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/cards/${id}`);
  },

  getBalanceSummary: async (currency: string = "GBP"): Promise<AllCardsBalanceSummary> => {
    const { data } = await api.get("/cards/balance-summary", {
      params: { currency },
    });
    return data;
  },
};

export const calendarApi = {
  getEvents: async (startDate: string, endDate: string): Promise<CalendarEvent[]> => {
    const { data } = await api.get("/calendar/events", {
      params: { start_date: startDate, end_date: endDate },
    });
    return data;
  },

  getMonthlySummary: async (year: number, month: number): Promise<MonthlySummary> => {
    const { data } = await api.get("/calendar/monthly-summary", {
      params: { year, month },
    });
    return data;
  },

  // Unified payments summary for current and next month (used by Calendar and Cards)
  getPaymentsSummary: async (currency: string = "GBP"): Promise<MonthlyPaymentsSummary> => {
    const { data } = await api.get("/calendar/payments-summary", {
      params: { currency },
    });
    return data;
  },

  getPaymentHistory: async (subscriptionId: string, limit = 50): Promise<PaymentHistory[]> => {
    const { data } = await api.get(`/calendar/payments/${subscriptionId}`, {
      params: { limit },
    });
    return data;
  },

  recordPayment: async (subscriptionId: string, payment: RecordPaymentRequest): Promise<PaymentHistory> => {
    const { data } = await api.post(`/calendar/payments/${subscriptionId}`, payment);
    return data;
  },

  deletePayment: async (subscriptionId: string, paymentDate: string): Promise<void> => {
    await api.delete(`/calendar/payments/${subscriptionId}/${paymentDate}`);
  },
};
