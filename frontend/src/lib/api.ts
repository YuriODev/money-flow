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

      // Handle plain text error responses (e.g., "Internal Server Error")
      if (typeof data === "string") {
        return Promise.reject(
          new APIError(
            data || `HTTP ${error.response.status} Error`,
            "HTTP_ERROR"
          )
        );
      }

      // Check for new error format
      if (data && typeof data === "object" && data.error) {
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
      if (data && typeof data === "object" && "detail" in data) {
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

// Payment type enum for Money Flow (DEPRECATED - use PaymentMode for filtering)
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

// Payment mode enum for Money Flow (NEW - for filtering and categorization)
export type PaymentMode = "recurring" | "one_time" | "debt" | "savings";

// Payment mode display names
export const PAYMENT_MODE_LABELS: Record<PaymentMode, string> = {
  recurring: "Recurring",
  one_time: "One-Time",
  debt: "Debt",
  savings: "Savings",
};

// Payment mode icons
export const PAYMENT_MODE_ICONS: Record<PaymentMode, string> = {
  recurring: "🔄",
  one_time: "📌",
  debt: "💳",
  savings: "🐷",
};

// Payment type display names (DEPRECATED)
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

// Payment type icons (emoji for now, can be replaced with icons) (DEPRECATED)
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
  // Payment type classification (DEPRECATED - use payment_mode)
  payment_type: PaymentType;
  // Payment mode classification (NEW)
  payment_mode: PaymentMode;
  category: string | null;
  category_id: string | null;
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
  // Payment type classification (DEPRECATED - use payment_mode)
  payment_type?: PaymentType;
  // Payment mode classification (NEW)
  payment_mode?: PaymentMode;
  category?: string;
  category_id?: string | null;
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
  by_payment_mode: Record<string, number>;
  upcoming_week: Subscription[];
  currency: string;
  // Debt and savings totals (Money Flow)
  total_debt: number;
  total_savings_target: number;
  total_current_saved: number;
}

export const subscriptionApi = {
  getAll: async (paymentMode?: PaymentMode, paymentType?: PaymentType): Promise<Subscription[]> => {
    const params: Record<string, string> = {};
    if (paymentMode) params.payment_mode = paymentMode;
    if (paymentType) params.payment_type = paymentType;
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
  payment_mode: PaymentMode;
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
  payment_mode: string;
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

// PDF Report Section Options
export interface PdfSections {
  categoryBreakdown: boolean;
  oneTimePayments: boolean;
  charts: boolean;
  upcomingPayments: boolean;
  paymentHistory: boolean;
  allPayments: boolean;
}

// PDF Report Config for advanced export
export interface PdfReportConfig {
  includeInactive: boolean;
  sections: PdfSections;
  pageSize?: "a4" | "letter";
  targetCurrency?: string;
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

  exportPdf: async (includeInactive = false, pageSize = "a4", includeCharts = true): Promise<Blob> => {
    const response = await api.get("/subscriptions/export/pdf", {
      params: { include_inactive: includeInactive, page_size: pageSize, include_charts: includeCharts },
      responseType: "blob",
    });
    return response.data;
  },

  // Advanced PDF export with section configuration
  exportPdfAdvanced: async (config: PdfReportConfig): Promise<Blob> => {
    const response = await api.post(
      "/subscriptions/export/pdf",
      {
        page_size: config.pageSize || "a4",
        target_currency: config.targetCurrency,
        sections: {
          summary: true, // Always include summary
          category_breakdown: config.sections.categoryBreakdown,
          one_time_payments: config.sections.oneTimePayments,
          charts: config.sections.charts,
          upcoming_payments: config.sections.upcomingPayments,
          payment_history: config.sections.paymentHistory,
          all_payments: config.sections.allPayments,
        },
        filters: {
          include_inactive: config.includeInactive,
        },
      },
      { responseType: "blob" }
    );
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

// Notification Preferences types
export interface TelegramStatus {
  enabled: boolean;
  verified: boolean;
  username: string | null;
  linked: boolean;
}

export interface NotificationPreferences {
  id: string;
  user_id: string;
  reminder_enabled: boolean;
  reminder_days_before: number;
  reminder_time: string;
  overdue_alerts: boolean;
  daily_digest: boolean;
  weekly_digest: boolean;
  weekly_digest_day: number;
  quiet_hours_enabled: boolean;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  telegram: TelegramStatus;
}

export interface NotificationPreferencesUpdate {
  reminder_enabled?: boolean;
  reminder_days_before?: number;
  reminder_time?: string;
  overdue_alerts?: boolean;
  daily_digest?: boolean;
  weekly_digest?: boolean;
  weekly_digest_day?: number;
  quiet_hours_enabled?: boolean;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
}

export interface TelegramLinkResponse {
  verification_code: string;
  bot_username: string;
  bot_link: string;
  expires_in_minutes: number;
  instructions: string;
}

export const notificationApi = {
  getPreferences: async (): Promise<NotificationPreferences> => {
    const { data } = await api.get("/notifications/preferences");
    return data;
  },

  updatePreferences: async (prefs: NotificationPreferencesUpdate): Promise<NotificationPreferences> => {
    const { data } = await api.put("/notifications/preferences", prefs);
    return data;
  },

  getTelegramStatus: async (): Promise<TelegramStatus> => {
    const { data } = await api.get("/notifications/telegram/status");
    return data;
  },

  initiateTelegramLink: async (): Promise<TelegramLinkResponse> => {
    const { data } = await api.post("/notifications/telegram/link");
    return data;
  },

  unlinkTelegram: async (): Promise<{ success: boolean; message: string }> => {
    const { data } = await api.delete("/notifications/telegram/unlink");
    return data;
  },

  sendTestNotification: async (): Promise<{ success: boolean; message: string; channel: string }> => {
    const { data } = await api.post("/notifications/test");
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

  // iCal Feed endpoints (Sprint 5.6)
  getICalFeedUrl: async (): Promise<ICalFeedResponse> => {
    const { data } = await api.get("/calendar/ical/feed-url");
    return data;
  },

  previewICalEvents: async (daysAhead: number = 30): Promise<ICalPreviewResponse> => {
    const { data } = await api.get("/calendar/ical/preview", {
      params: { days_ahead: daysAhead },
    });
    return data;
  },

  // Google Calendar OAuth endpoints (Sprint 5.6)
  getGoogleCalendarStatus: async (): Promise<GoogleCalendarStatus> => {
    const { data } = await api.get("/calendar/google/status");
    return data;
  },

  connectGoogleCalendar: async (): Promise<GoogleCalendarConnectResponse> => {
    const { data } = await api.get("/calendar/google/connect");
    return data;
  },

  disconnectGoogleCalendar: async (): Promise<void> => {
    await api.delete("/calendar/google/disconnect");
  },

  syncToGoogleCalendar: async (calendarId: string = "primary"): Promise<GoogleCalendarSyncResponse> => {
    const { data } = await api.post("/calendar/google/sync", null, {
      params: { calendar_id: calendarId },
    });
    return data;
  },

  listGoogleCalendars: async (): Promise<GoogleCalendarListResponse> => {
    const { data } = await api.get("/calendar/google/calendars");
    return data;
  },
};

// iCal Feed types (Sprint 5.6)
export interface ICalFeedResponse {
  feed_url: string;
  webcal_url: string;
  token: string;
  feed_path: string;
  instructions: {
    google_calendar: string;
    apple_calendar: string;
    outlook: string;
    one_click: string;
  };
}

export interface ICalPreviewEvent {
  id: string;
  title: string;
  date: string | null;
  amount: number;
  currency: string;
  frequency: string;
  payment_type: string | null;
}

export interface ICalPreviewResponse {
  events: ICalPreviewEvent[];
  total: number;
  days_ahead: number;
  generated_at: string;
}

// Google Calendar OAuth types (Sprint 5.6)
export interface GoogleCalendarStatus {
  connected: boolean;
  status: "connected" | "disconnected" | "token_expired" | "error" | "not_connected";
  calendar_id: string | null;
  sync_enabled: boolean | null;
  last_sync_at: string | null;
  last_error: string | null;
}

export interface GoogleCalendarConnectResponse {
  authorization_url: string;
  state: string;
}

export interface GoogleCalendarSyncResponse {
  created: number;
  failed: number;
  total: number;
}

export interface GoogleCalendarListResponse {
  calendars: {
    id: string;
    summary: string;
    primary: boolean;
  }[];
}

// User Profile types
export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  role: "user" | "admin";
  is_active: boolean;
  is_verified: boolean;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserProfileUpdate {
  full_name?: string;
  avatar_url?: string;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

// User Preferences types
export type Currency = "GBP" | "USD" | "EUR" | "UAH" | "CAD" | "AUD" | "JPY" | "CHF" | "CNY" | "INR";
export type DateFormat = "DD/MM/YYYY" | "MM/DD/YYYY" | "YYYY-MM-DD";
export type DefaultView = "list" | "calendar" | "cards" | "agent";
export type ThemePreference = "light" | "dark" | "system";
export type WeekStart = "sunday" | "monday";
export type NumberFormat = "1,234.56" | "1.234,56";

export interface UserPreferences {
  currency: Currency;
  date_format: DateFormat;
  number_format: NumberFormat;
  theme: ThemePreference;
  default_view: DefaultView;
  compact_mode: boolean;
  week_start: WeekStart;
  timezone: string;
  language: string;
  show_currency_symbol: boolean;
  default_card_id: string | null;
  default_category_id: string | null;
}

export interface UserPreferencesUpdate {
  currency?: Currency;
  date_format?: DateFormat;
  number_format?: NumberFormat;
  theme?: ThemePreference;
  default_view?: DefaultView;
  compact_mode?: boolean;
  week_start?: WeekStart;
  timezone?: string;
  language?: string;
  show_currency_symbol?: boolean;
  default_card_id?: string | null;
  default_category_id?: string | null;
}

export const userApi = {
  // Get current user profile
  getProfile: async (): Promise<UserProfile> => {
    const { data } = await api.get("/auth/me");
    return data;
  },

  // Update user profile
  updateProfile: async (profile: UserProfileUpdate): Promise<UserProfile> => {
    const { data } = await api.put("/auth/me", profile);
    return data;
  },

  // Change password
  changePassword: async (request: PasswordChangeRequest): Promise<void> => {
    await api.post("/auth/change-password", request);
  },

  // Get user preferences
  getPreferences: async (): Promise<UserPreferences> => {
    const { data } = await api.get("/users/preferences");
    return data;
  },

  // Update user preferences
  updatePreferences: async (prefs: UserPreferencesUpdate): Promise<UserPreferences> => {
    const { data } = await api.put("/users/preferences", prefs);
    return data;
  },
};

// Category types
export interface Category {
  id: string;
  name: string;
  description: string | null;
  color: string;
  icon: string | null;
  budget_amount: string | null;
  budget_currency: string;
  sort_order: number;
  is_active: boolean;
  is_system: boolean;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface CategoryWithStats extends Category {
  subscription_count: number;
  total_monthly: string;
  budget_used_percentage: number | null;
  is_over_budget: boolean | null;
}

export interface CategoryCreate {
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  budget_amount?: number;
  budget_currency?: string;
  sort_order?: number;
}

export interface CategoryUpdate {
  name?: string;
  description?: string;
  color?: string;
  icon?: string;
  budget_amount?: number | null;
  budget_currency?: string;
  is_active?: boolean;
  sort_order?: number;
}

export interface CategoryBudgetSummary {
  categories: CategoryWithStats[];
  total_budgeted: string;
  total_spent: string;
  categories_over_budget: number;
}

export const categoriesApi = {
  // Get all categories
  getAll: async (includeInactive = false): Promise<Category[]> => {
    const { data } = await api.get("/categories", {
      params: { include_inactive: includeInactive },
    });
    return data;
  },

  // Get categories with stats
  getWithStats: async (currency = "GBP", includeInactive = false): Promise<CategoryWithStats[]> => {
    const { data } = await api.get("/categories/with-stats", {
      params: { currency, include_inactive: includeInactive },
    });
    return data;
  },

  // Get budget summary
  getBudgetSummary: async (currency = "GBP"): Promise<CategoryBudgetSummary> => {
    const { data } = await api.get("/categories/budget-summary", {
      params: { currency },
    });
    return data;
  },

  // Get category by ID
  getById: async (id: string): Promise<Category> => {
    const { data } = await api.get(`/categories/${id}`);
    return data;
  },

  // Create category
  create: async (category: CategoryCreate): Promise<Category> => {
    const { data } = await api.post("/categories", category);
    return data;
  },

  // Create default categories
  createDefaults: async (): Promise<Category[]> => {
    const { data } = await api.post("/categories/defaults");
    return data;
  },

  // Update category
  update: async (id: string, category: CategoryUpdate): Promise<Category> => {
    const { data } = await api.patch(`/categories/${id}`, category);
    return data;
  },

  // Delete category
  delete: async (id: string): Promise<void> => {
    await api.delete(`/categories/${id}`);
  },

  // Assign subscription to category
  assignSubscription: async (subscriptionId: string, categoryId: string | null): Promise<void> => {
    await api.post("/categories/assign", {
      subscription_id: subscriptionId,
      category_id: categoryId,
    });
  },

  // Bulk assign subscriptions to category
  bulkAssign: async (subscriptionIds: string[], categoryId: string | null): Promise<{ updated: number }> => {
    const { data } = await api.post("/categories/bulk-assign", {
      subscription_ids: subscriptionIds,
      category_id: categoryId,
    });
    return data;
  },
};

// Icon types
export type IconSource = "simple_icons" | "clearbit" | "logo_dev" | "brandfetch" | "ai_generated" | "user_uploaded" | "fallback";
export type IconStyle = "minimal" | "branded" | "playful" | "corporate";

export interface Icon {
  id: string;
  service_name: string;
  display_name: string | null;
  source: IconSource;
  icon_url: string | null;
  brand_color: string | null;
  secondary_color: string | null;
  category: string | null;
  width: number | null;
  height: number | null;
  format: string | null;
  is_verified: boolean;
  created_at: string;
  expires_at: string | null;
}

export interface IconSearchRequest {
  query: string;
  include_ai?: boolean;
  category?: string | null;
}

export interface IconSearchResponse {
  icons: Icon[];
  total: number;
  from_cache: boolean;
}

export interface IconGenerateRequest {
  service_name: string;
  description?: string | null;
  style?: IconStyle;
  size?: number;
  brand_color?: string | null;
}

export interface IconBulkRequest {
  service_names: string[];
  sources?: IconSource[];
}

export interface IconBulkResponse {
  icons: Record<string, Icon | null>;
  found: number;
  missing: string[];
}

export interface IconStats {
  total_icons: number;
  by_source: Record<string, number>;
  expired_count: number;
  ai_generated_count: number;
  user_uploaded_count: number;
}

// Icon API
export const iconApi = {
  // Get icon for a service
  getIcon: async (serviceName: string, forceRefresh = false): Promise<Icon | null> => {
    const { data } = await api.get(`/icons/${encodeURIComponent(serviceName)}`, {
      params: { force_refresh: forceRefresh },
    });
    return data;
  },

  // Search for icons
  search: async (request: IconSearchRequest): Promise<IconSearchResponse> => {
    const { data } = await api.post("/icons/search", request);
    return data;
  },

  // Generate icon with AI
  generate: async (request: IconGenerateRequest): Promise<Icon | null> => {
    const { data } = await api.post("/icons/generate", request);
    return data;
  },

  // Bulk fetch icons
  bulkFetch: async (request: IconBulkRequest): Promise<IconBulkResponse> => {
    const { data } = await api.post("/icons/bulk", request);
    return data;
  },

  // Get icon cache stats
  getStats: async (): Promise<IconStats> => {
    const { data } = await api.get("/icons/stats");
    return data;
  },
};

// ============================================================================
// Statement Import Types (Bank Statement Import - Sprint 5.5)
// ============================================================================

export type ImportJobStatus = "pending" | "processing" | "ready" | "completed" | "failed" | "cancelled";
export type DetectionStatus = "pending" | "imported" | "skipped" | "duplicate";
export type StatementFileType = "pdf" | "csv" | "ofx" | "qfx" | "qif";

export interface BankProfile {
  id: string;
  name: string;
  slug: string;
  country_code: string;
  currency: string;
  logo_url: string | null;
  website: string | null;
  is_verified: boolean;
}

export interface ImportJob {
  id: string;
  filename: string;
  file_type: StatementFileType;
  file_size: number | null;
  bank_id: string | null;
  bank_name: string | null;
  currency: string;
  status: ImportJobStatus;
  error_message: string | null;
  total_transactions: number;
  detected_count: number;
  imported_count: number;
  skipped_count: number;
  duplicate_count: number;
  period_start: string | null;
  period_end: string | null;
  created_at: string;
  processing_started_at: string | null;
  completed_at: string | null;
}

export interface DetectedSubscription {
  id: string;
  job_id: string;
  name: string;
  normalized_name: string;
  amount: string;
  currency: string;
  frequency: string;
  payment_type: string;
  confidence: number;
  amount_variance: number;
  transaction_count: number;
  first_seen: string | null;
  last_seen: string | null;
  status: DetectionStatus;
  is_selected: boolean;
  duplicate_of_id: string | null;
  duplicate_similarity: number | null;
  sample_descriptions: string[] | null;
  created_at: string;
}

export interface ImportPreviewSummary {
  total_detected: number;
  selected_count: number;
  duplicate_count: number;
  high_confidence_count: number;
  low_confidence_count: number;
  total_monthly_amount: string;
  currencies: string[];
  payment_types: Record<string, number>;
  frequencies: Record<string, number>;
}

export interface ImportPreview {
  job: ImportJob;
  detected_subscriptions: DetectedSubscription[];
  summary: ImportPreviewSummary;
}

export interface StatementUploadResponse {
  job_id: string;
  filename: string;
  file_type: string;
  status: string;
  message: string;
}

export interface ImportJobStatusResponse {
  id: string;
  status: ImportJobStatus;
  detected_count: number;
  error_message: string | null;
  is_ready: boolean;
}

export interface ConfirmImportRequest {
  subscription_ids?: string[];
  card_id?: string | null;
  category_id?: string | null;
}

export interface ConfirmImportResponse {
  job_id: string;
  imported_count: number;
  skipped_count: number;
  duplicate_count: number;
  created_subscription_ids: string[];
}

export interface DuplicateMatch {
  detected_id: string;
  detected_name: string;
  existing_id: string;
  existing_name: string;
  similarity: number;
  match_reasons: string[];
}

export interface DetectedSubscriptionUpdate {
  is_selected?: boolean;
  status?: string;
  name?: string;
  amount?: number;
  frequency?: string;
  payment_type?: string;
}

// Statement Import API
export const statementImportApi = {
  // Upload a bank statement file
  uploadStatement: async (
    file: File,
    options?: {
      bank_id?: string;
      currency?: string;
      use_ai?: boolean;
      min_confidence?: number;
    }
  ): Promise<StatementUploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    if (options?.bank_id) formData.append("bank_id", options.bank_id);
    if (options?.currency) formData.append("currency", options.currency);
    if (options?.use_ai !== undefined) formData.append("use_ai", String(options.use_ai));
    if (options?.min_confidence !== undefined) formData.append("min_confidence", String(options.min_confidence));

    const { data } = await api.post("/import/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  // Get job status (for polling)
  getJobStatus: async (jobId: string): Promise<ImportJobStatusResponse> => {
    const { data } = await api.get(`/import/jobs/${jobId}/status`);
    return data;
  },

  // Get import preview with detected subscriptions
  getPreview: async (jobId: string): Promise<ImportPreview> => {
    const { data } = await api.get(`/import/jobs/${jobId}/preview`);
    return data;
  },

  // Get import job details
  getJob: async (jobId: string): Promise<ImportJob> => {
    const { data } = await api.get(`/import/jobs/${jobId}`);
    return data;
  },

  // List all import jobs
  listJobs: async (limit = 20, offset = 0): Promise<{ jobs: ImportJob[]; total: number }> => {
    const { data } = await api.get("/import/jobs", { params: { limit, offset } });
    return data;
  },

  // Update a detected subscription
  updateDetected: async (
    detectedId: string,
    update: DetectedSubscriptionUpdate
  ): Promise<DetectedSubscription> => {
    const { data } = await api.patch(`/import/detected/${detectedId}`, update);
    return data;
  },

  // Bulk update detected subscriptions
  bulkUpdateDetected: async (
    subscriptionIds: string[],
    update: { is_selected?: boolean; status?: string }
  ): Promise<{ updated_count: number; subscription_ids: string[] }> => {
    const { data } = await api.post("/import/detected/bulk-update", {
      subscription_ids: subscriptionIds,
      ...update,
    });
    return data;
  },

  // Confirm import of selected subscriptions
  confirmImport: async (
    jobId: string,
    request?: ConfirmImportRequest
  ): Promise<ConfirmImportResponse> => {
    const { data } = await api.post(`/import/jobs/${jobId}/confirm`, request || {});
    return data;
  },

  // Cancel an import job
  cancelJob: async (jobId: string): Promise<{ message: string; job_id: string }> => {
    const { data } = await api.delete(`/import/jobs/${jobId}`);
    return data;
  },

  // Get duplicates for a job
  getDuplicates: async (jobId: string): Promise<{ duplicates: DuplicateMatch[]; total_matches: number }> => {
    const { data } = await api.get(`/import/jobs/${jobId}/duplicates`);
    return data;
  },
};

// Bank Profiles API
export const banksApi = {
  // Get all bank profiles
  getAll: async (country?: string): Promise<BankProfile[]> => {
    const { data } = await api.get("/banks", { params: country ? { country_code: country } : {} });
    return data;
  },

  // Search banks
  search: async (query: string): Promise<BankProfile[]> => {
    const { data } = await api.get("/banks/search", { params: { q: query } });
    return data;
  },

  // Get popular banks
  getPopular: async (): Promise<BankProfile[]> => {
    const { data } = await api.get("/banks/popular");
    return data;
  },

  // Get bank by slug
  getBySlug: async (slug: string): Promise<BankProfile> => {
    const { data } = await api.get(`/banks/${slug}`);
    return data;
  },
};
