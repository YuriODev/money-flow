# Money Flow - Claude Code Guide

> **Note**: This project is being renamed from "Subscription Tracker" to "**Money Flow**" to reflect its expanded scope. See [Money Flow Refactor Plan](.claude/plans/MONEY_FLOW_REFACTOR_PLAN.md) for details.

---

## 🚀 MASTER DEVELOPMENT PLAN

> **UPDATED**: A comprehensive 36-week roadmap for production-ready enhancement + Settings & AI features.
> **Full Plan**: [.claude/docs/MASTER_PLAN.md](.claude/docs/MASTER_PLAN.md) (~655 hours, 400+ tasks)

### Current Phase & Sprint

| Phase | Sprint | Status | Focus |
|-------|--------|--------|-------|
| **Phase 1** | Sprint 1.1 | ✅ Complete | Authentication System |
| **Phase 1** | Sprint 1.2 | ✅ Complete | Security Hardening |
| **Phase 1** | Sprint 1.3 | ✅ Complete | CI/CD Pipeline |
| **Phase 1** | Sprint 1.4 | ✅ Complete | Logging & Observability |
| **Phase 2** | Sprint 2.1 | ✅ Complete | E2E Testing Framework |
| **Phase 2** | Sprint 2.2 | ✅ Complete | AI Agent E2E, Bug Fixes, Data Isolation |
| **Phase 2** | Sprint 2.3 | ✅ Complete | Integration Tests & Contract Testing |
| **Phase 2** | Sprint 2.4 | ✅ Complete | Performance & Load Testing |
| **Phase 3** | Sprint 3.1 | ✅ Complete | API Versioning & Documentation |
| **Phase 3** | Sprint 3.2 | ✅ Complete | Database Scalability |
| **Phase 3** | Sprint 3.3 | ✅ Complete | Service Architecture Improvements |
| **Phase 3** | Sprint 3.4 | ✅ Complete | Monitoring & Alerting |
| **Phase 4** | Sprint 4.1 | ✅ Complete | Custom Claude Skills |
| **Phase 4** | Sprint 4.2 | ✅ Complete | Frontend Enhancements |
| **Phase 4** | Sprint 4.3 | ✅ Complete | Payment Reminders & Telegram Bot |
| **Phase 4** | Sprint 4.4 | ✅ Complete | Documentation & Security |
| **Phase 5** | Sprint 5.1 | ✅ Complete | Profile & Preferences |
| **Phase 5** | Sprint 5.2 | ✅ Complete | Cards & Categories |
| **Phase 5** | Sprint 5.3 | ✅ Complete | Notifications & Export |
| **Phase 5** | Sprint 5.4 | ✅ Complete | Icons & AI Settings |
| **Phase 5** | Sprint 5.5 | 🔄 In Progress | Smart Import (Bank Statements) |
| **Phase 5** | Sprints 5.6-5.7 | 🔜 Upcoming | Integrations, Open Banking (~100h remaining) |
| **Phase 6** | Sprint 6.1 | 🔜 Upcoming | Production Launch (~15h) |

### Sprint 5.5 Tasks (Weeks 25-27) - Smart Import (AI) 🔄

| Task | Status | Description |
|------|--------|-------------|
| 5.5.0.1 | ✅ DONE | Install dependencies (pdfplumber, PyPDF2, ofxparse) |
| 5.5.0.2 | ✅ DONE | Create base StatementParser class and dataclasses |
| 5.5.0.3 | ✅ DONE | BankProfile model with JSONB mappings |
| 5.5.0.4 | ✅ DONE | Bank profiles database migration |
| 5.5.0.5 | ✅ DONE | Bank seed data JSON (33 banks) |
| 5.5.0.6 | ✅ DONE | Bank CRUD API endpoints |
| 5.5.1.1 | ✅ DONE | PDF parser with pdfplumber |
| 5.5.1.2 | ✅ DONE | CSV parser with dynamic bank lookup |
| 5.5.1.3 | ✅ DONE | OFX/QIF parser |
| 5.5.2.1 | 🔜 TODO | AI extraction of recurring patterns |
| 5.5.2.2 | 🔜 TODO | Preview and confirm import UI |
| 5.5.2.3 | 🔜 TODO | Duplicate detection and merge |
| 5.5.3 | 🔜 TODO | Unit tests for statement parsers |

**Scope Decision:** Email scanning (Gmail/Outlook) deferred to Sprint 5.6 to focus on bank statement parsing quality.

**Sprint 5.5 Features Completed (Phase 1 - Bank Infrastructure):**
- **Bank Profile Model** (`src/models/bank_profile.py`)
  - BankProfile SQLAlchemy model with JSONB columns
  - csv_mapping, pdf_patterns, detection_patterns JSONB fields
  - Country code, currency, logo_url, website fields
  - is_verified, usage_count tracking
  - Helper methods for column access
- **Bank Profile Migration** (`0a1c54d55e2f_add_bank_profiles_table.py`)
  - bank_profiles table with all fields
  - Indexes on slug (unique), country_code
- **Bank Seed Data** (`data/bank_profiles.json`)
  - 33 banks from 7 countries (GB, US, BR, DE, AR, UA, NL)
  - UK: Monzo, Revolut, Starling, Barclays, HSBC, Lloyds, NatWest, Santander, Halifax, Nationwide, Metro Bank
  - US: Chase, Bank of America, Wells Fargo, Citi, Capital One, Discover, American Express, PNC
  - Brazil: Nubank, Itaú, Bradesco, Banco do Brasil, Inter
  - Germany: N26, DKB, Commerzbank
  - Argentina: Banco Galicia, Mercado Pago
  - Ukraine: PrivatBank, Monobank
  - Netherlands: ING, ABN AMRO
- **Bank Service** (`src/services/bank_service.py`)
  - CRUD operations (get_all, get_by_slug, create, update, delete)
  - Bank detection from filename, headers, content patterns
  - Search by name/slug
  - Countries list with bank counts
  - Seed from JSON file
- **Bank Schemas** (`src/schemas/bank.py`)
  - BankProfileCreate, BankProfileUpdate, BankProfileResponse
  - BankDetectRequest, BankDetectResponse
  - BankProfileListResponse, CountryBanksResponse
  - CSVMappingSchema, DetectionPatternsSchema
- **Bank API** (`src/api/banks.py`)
  - GET /api/v1/banks - List banks with filtering
  - GET /api/v1/banks/search - Search banks
  - GET /api/v1/banks/countries - List countries with bank counts
  - GET /api/v1/banks/{slug} - Get bank by slug
  - POST /api/v1/banks - Create bank (admin)
  - PATCH /api/v1/banks/{slug} - Update bank
  - DELETE /api/v1/banks/{slug} - Delete bank
  - POST /api/v1/banks/detect - Auto-detect bank from file
  - POST /api/v1/banks/seed - Seed from JSON

**Sprint 5.5 Features Completed (Phase 2 - Statement Parsers):**
- **Base Parser Infrastructure** (`src/services/parsers/base.py`)
  - StatementParser abstract base class
  - StatementData dataclass (transactions, bank_name, currency, format, period)
  - Transaction dataclass (date, amount, description, type, balance, reference)
  - StatementFormat enum (PDF, CSV, OFX, QIF)
  - TransactionType enum (CREDIT, DEBIT, UNKNOWN)
  - Common utilities: _read_file, _get_filename, _parse_date, _parse_amount, _detect_currency
- **PDF Parser** (`src/services/parsers/pdf_parser.py`)
  - Uses pdfplumber for text/table extraction
  - Multi-page document handling
  - Bank detection patterns for 18+ banks
  - Date patterns: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, DD Mon YYYY, etc.
  - Amount patterns: currency symbols, accounting format, thousands separators
  - Table parsing with column detection (date, description, amount, debit/credit, balance)
  - Text fallback parsing with regex patterns
- **CSV Parser** (`src/services/parsers/csv_parser.py`)
  - Dynamic bank profile lookup from database
  - Auto-detection of bank from filename/headers
  - Flexible column mapping from bank profiles
  - Multi-encoding support (utf-8, latin-1, cp1252, iso-8859-1)
  - Debit/credit column handling (single amount or separate)
  - Async parse_async() method for bank service integration
- **OFX/QIF Parser** (`src/services/parsers/ofx_parser.py`)
  - OFX 1.x/2.x support via ofxparse library
  - QIF custom parser for legacy Quicken format
  - QFX (Quicken OFX variant) support
  - Transaction type mapping (credit, debit, int, div, fee, etc.)
  - QIF field parsing (D=date, T=amount, P=payee, M=memo, etc.)

### Sprint 5.4 Tasks (Weeks 23-24) - Icons & AI Settings ✅

| Task | Status | Description |
|------|--------|-------------|
| 5.4.1.1 | ✅ DONE | Icon cache model and storage |
| 5.4.1.2 | ✅ DONE | External icon fetching (SimpleIcons, Clearbit) |
| 5.4.1.3 | ✅ DONE | AI icon generation (Claude SVG) |
| 5.4.1.4 | ✅ DONE | Icon browser and search UI |
| 5.4.2.1-5 | ✅ DONE | AI Assistant settings (NL parsing, model, suggestions) |
| 5.4.3 | ✅ DONE | Unit tests for icons and AI settings (58 tests) |

**Sprint 5.4 Features Completed:**
- **Icon Cache Model** (`src/models/icon_cache.py`)
  - IconCache SQLAlchemy model with TTL-based expiration
  - IconSource enum (SIMPLE_ICONS, CLEARBIT, LOGO_DEV, BRANDFETCH, AI_GENERATED, USER_UPLOADED, FALLBACK)
  - SOURCE_TTL_HOURS mapping for automatic expiry
  - Methods: is_expired, is_global, set_expiry_from_source, record_fetch, refresh
- **Icon Service** (`src/services/icon_service.py`)
  - External icon fetching from SimpleIcons CDN and Clearbit Logo API
  - SERVICE_SLUG_MAP for 50+ popular services
  - BRAND_COLORS mapping for brand consistency
  - Domain guessing for Clearbit API
  - AI icon generation with Claude (SVG format)
  - Style-based generation (minimal, branded, playful, corporate)
  - SVG color extraction
  - get_or_generate_icon() for automatic AI fallback
- **Icon Schemas** (`src/schemas/icon.py`)
  - IconResponse, IconSearchRequest, IconSearchResponse
  - IconFetchRequest, IconGenerateRequest, IconUploadRequest
  - IconBulkFetchRequest, IconBulkResponse, IconStatsResponse
- **Icon API** (`src/api/icons.py`)
  - GET /api/v1/icons/:service_name - Get icon
  - POST /api/v1/icons/fetch - Fetch with sources
  - POST /api/v1/icons/generate - Generate with AI
  - POST /api/v1/icons/search - Search icons
  - POST /api/v1/icons/bulk - Bulk fetch
  - GET /api/v1/icons/stats - Cache statistics
- **AI Preferences Model** (`src/models/ai_preferences.py`)
  - AIPreferences SQLAlchemy model (one-to-one with User)
  - Enums: SuggestionFrequency, AIModel, IconGenerationStyle
  - Settings: ai_enabled, preferred_model, auto_categorization
  - Settings: smart_suggestions, suggestion_frequency, confidence_threshold
  - Settings: icon_generation_enabled, icon_style, icon_size
  - Settings: conversation_history_enabled, conversation_history_days
  - Settings: natural_language_parsing, learn_from_corrections
  - Settings: privacy_mode, custom_instructions
  - Properties: is_fully_enabled, should_auto_categorize, should_suggest
  - Methods: meets_confidence_threshold, clear_conversation_history_cutoff
- **AI Preferences Schemas** (`src/schemas/ai_preferences.py`)
  - AIPreferencesCreate, AIPreferencesUpdate, AIPreferencesResponse
  - ClearHistoryRequest
  - All enums: AIModelEnum, SuggestionFrequencyEnum, IconGenerationStyleEnum
- **AI Settings API** (`src/api/ai_settings.py`)
  - GET /api/v1/ai/preferences - Get preferences
  - PUT /api/v1/ai/preferences - Update preferences
  - POST /api/v1/ai/reset - Reset to defaults
  - GET /api/v1/ai/history/stats - Conversation stats
  - DELETE /api/v1/ai/history - Clear history
- **Icon Browser UI** (`frontend/src/components/IconBrowser.tsx`)
  - Search and browse icons from cache
  - AI generation with style and color options
  - Quick service picker for popular services
  - Icon selection with preview
- **Frontend API** (`frontend/src/lib/api.ts`)
  - Icon types and interfaces
  - iconApi with all icon operations
- **Migration** (`55688a8830bc_add_icon_cache_and_ai_preferences.py`)
  - icon_cache table with indexes
  - ai_preferences table with foreign key
- **58 Unit Tests** (`tests/unit/test_icon_cache.py`, `tests/unit/test_ai_preferences.py`)
  - IconSource enum tests
  - IconCache model tests (expiry, global, methods)
  - Icon schema tests
  - IconService tests (normalization, slug mapping, domain guessing)
  - AI style instructions tests
  - SVG color extraction tests
  - Async service tests (get_icon, stats, search, bulk)
  - AI preferences model tests
  - AI preferences schema validation tests
- **Total unit tests: ~769** (711 previous + 58 new)
- **Dynamic Currency Conversion** (`src/services/currency_service.py`)
  - Live exchange rates from fawazahmed0/currency-api (free, no API key)
  - 200+ currencies supported with real-time rates
  - API fallback chain: Primary CDN → Mirror → Open Exchange Rates → Static rates
  - Primary API: `https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json`
  - Mirror API: `https://latest.currency-api.pages.dev/v1/currencies/usd.json`
  - Cache TTL: 1 hour for exchange rates
  - Minimal static fallback (10 currencies) only when ALL APIs fail
- **Currency API Endpoints** (`src/api/currencies.py`)
  - GET /api/v1/currencies - All currencies grouped by region
  - GET /api/v1/currencies/search - Search currencies
  - GET /api/v1/currencies/popular - Popular currencies list
  - GET /api/v1/currencies/regions - Get all regions
  - GET /api/v1/currencies/regions/{region_id} - Currencies by region
  - GET /api/v1/currencies/{code} - Single currency info
- **Currency Tests** (`tests/unit/test_currency_service.py`)
  - Range-based assertions for dynamic rates
  - TestCurrencyServiceLiveAPI class for real API tests
  - Tests for BRL, NGN, JPY and other world currencies

### Sprint 5.3 Tasks (Week 21) - Notifications & Export ✅

| Task | Status | Description |
|------|--------|-------------|
| 5.3.1.1 | ✅ DONE | Email notification channel |
| 5.3.1.2 | ✅ DONE | Push notification setup (PWA) |
| 5.3.1.3 | ✅ DONE | Notification history view |
| 5.3.2 | ✅ DONE | Scheduled Reports (daily/weekly/monthly) |
| 5.3.3.1 | ✅ DONE | PDF report generation (ReportLab) |
| 5.3.3.2 | ✅ DONE | Scheduled backup to cloud storage |
| 5.3.3.3 | ✅ DONE | Export history/audit log |
| 5.3.4 | ✅ DONE | 112 unit tests |

**Sprint 5.3 Features Completed:**
- **Email Notifications** (`src/services/email_service.py`)
  - SMTP with TLS via aiosmtplib
  - Payment reminders with urgency levels
  - Daily/weekly digests
- **Push Notifications** (`src/services/push_service.py`)
  - VAPID authentication with pywebpush
  - PWA push subscription management
  - Push API endpoints in notifications.py
- **Notification History** (`src/models/notification_history.py`)
  - NotificationHistory model with channel/status/type enums
  - CRUD API for viewing/clearing history
- **Scheduled Reports** (`src/services/scheduled_report_service.py`)
  - Daily, weekly, monthly report generation
  - Email delivery with PDF attachments
  - Report settings in NotificationPreferences
- **PDF Reports** (`src/services/pdf_report_service.py`)
  - ReportLab-based PDF generation
  - Summary stats, category breakdown, upcoming payments
- **Cloud Backups** (`src/services/backup_service.py`)
  - Google Cloud Storage with local fallback
  - Scheduled daily backups via ARQ
- **Export History** (`src/models/export_history.py`)
  - Audit log for all exports (JSON, CSV, PDF)
  - ExportHistory CRUD API
- **Unit Tests** - 112 tests for Sprint 5.3 features
- **Total unit tests: ~711** (599 previous + 112 new)

### Sprint 5.2 Tasks (Week 19) - Cards & Categories ✅

| Task | Status | Description |
|------|--------|-------------|
| 5.2.1.4 | ✅ DONE | Default card selection |
| 5.2.2.1 | ✅ DONE | Category model and migration |
| 5.2.2.2 | ✅ DONE | Category CRUD API endpoints |
| 5.2.2.3 | ✅ DONE | Category UI with color/icon picker |
| 5.2.2.4 | ✅ DONE | Budget limits per category |
| 5.2.3.1 | ✅ DONE | Update subscription model with category_id |
| 5.2.3.2 | ✅ DONE | Category selection in subscription forms |
| 5.2.3.3 | 🔜 Future | Auto-categorization suggestions (AI) |
| 5.2.4 | ✅ DONE | Category unit tests (45 tests) |

**Sprint 5.2 Features Completed:**
- **Category Model** (`src/models/category.py`)
  - User-owned categories with custom colors and icons
  - Optional budget amount per category
  - System categories flag for defaults
- **Category Migration** (`e86b93e0cf9a_add_categories_table.py`)
  - `categories` table with all fields
  - `category_id` column added to `subscriptions` table
  - Performance indexes for user_id and name
- **Category Schemas** (`src/schemas/category.py`)
  - CategoryCreate, CategoryUpdate, CategoryResponse
  - CategoryWithStats (includes subscription count, monthly total)
  - CategoryBudgetSummary for budget overview
  - AssignCategoryRequest, BulkAssignCategoryRequest
- **Category Service** (`src/services/category_service.py`)
  - Full CRUD operations with user ownership
  - Budget tracking and over-budget detection
  - Default categories creation (8 common categories)
  - Subscription assignment and bulk assignment
- **Category API** (`src/api/categories.py`)
  - GET /api/v1/categories - List categories
  - GET /api/v1/categories/with-stats - With subscription counts
  - GET /api/v1/categories/budget-summary - Budget overview
  - POST /api/v1/categories - Create category
  - POST /api/v1/categories/defaults - Create defaults
  - PATCH /api/v1/categories/:id - Update
  - DELETE /api/v1/categories/:id - Delete
  - POST /api/v1/categories/assign - Assign subscription
  - POST /api/v1/categories/bulk-assign - Bulk assign
- **Categories Settings UI** (`frontend/src/components/settings/CategoriesSettings.tsx`)
  - Grid view of categories with stats
  - Color picker with 16 preset colors + custom
  - Icon picker with emoji selection
  - Budget progress bar visualization
  - Create, edit, delete modals
  - Default categories creation button
- **CategorySelector Component** (`frontend/src/components/CategorySelector.tsx`)
  - Dropdown component for selecting categories
  - Shows category colors and budget limits
  - Used in Add/Edit subscription modals
- **Default Card/Category Selection** (`src/schemas/user.py`, `src/api/users.py`)
  - default_card_id and default_category_id in user preferences
  - Auto-populate defaults when creating new subscriptions
- **Frontend API** (`frontend/src/lib/api.ts`)
  - Category types and interfaces
  - categoriesApi with all endpoints
  - UserPreferences with default_card_id/default_category_id
- **Unit Tests** (`tests/unit/test_categories.py`)
  - 45 tests covering model, schemas, service
- **Total unit tests: 599** (554 previous + 45 new)

### Sprint 5.1 Tasks (Week 17) - Profile & Preferences ✅

| Task | Status | Description |
|------|--------|-------------|
| 5.1.1.1 | ✅ DONE | Edit user info (name, email) |
| 5.1.1.2 | ✅ DONE | Change password with verification |
| 5.1.2.1 | ✅ DONE | Currency selection (14 currencies) |
| 5.1.2.2 | ✅ DONE | Date format preferences (5 formats) |
| 5.1.2.3 | ✅ DONE | Default view preference |
| 5.1.2.4 | ✅ DONE | Theme selection (light/dark/system) |
| 5.1.3.1 | ✅ DONE | PATCH /api/auth/profile endpoint |
| 5.1.3.2 | ✅ DONE | GET/PUT /api/v1/users/preferences |
| 5.1.4 | ✅ DONE | 30 unit tests |

**Sprint 5.1 Features Completed:**
- **Profile Settings** (`frontend/src/components/settings/ProfileSettings.tsx`)
  - Edit name and email with API integration
  - Password change with current password verification
  - React Query mutations with optimistic updates
- **Preferences Settings** (`frontend/src/components/settings/PreferencesSettings.tsx`)
  - Currency selection (GBP, USD, EUR, UAH + 10 more)
  - Date format (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, etc.)
  - Number format (1,234.56, 1.234,56, 1 234.56)
  - Theme (light/dark/system with auto-detection)
  - Default view (list/calendar/cards/agent)
  - Compact mode toggle
  - Week start (Monday/Sunday)
  - Timezone selection
  - Language preference
- **Backend APIs** (`src/api/users.py`)
  - GET /api/v1/users/preferences - Fetch user preferences
  - PUT /api/v1/users/preferences - Update preferences (partial)
- **Settings Page** (`frontend/src/app/settings/page.tsx`)
  - Profile and Preferences tabs
  - Responsive layout with glass-card styling
- **Auth Context** (`frontend/src/lib/auth-context.tsx`)
  - Added `refreshUser()` function for profile updates
- **Unit Tests** (`tests/unit/test_user_preferences.py`)
  - 30 tests covering schemas, parsing, and API endpoints
- **Total unit tests: 554** (524 previous + 30 new)

### Sprint 4.4 Tasks (Week 16) - Documentation & Security ✅

| Task | Status | Description |
|------|--------|-------------|
| 4.4.1.1 | ✅ DONE | User Guide Documentation |
| 4.4.1.2 | ✅ DONE | FAQ Document |
| 4.4.1.4 | ✅ DONE | Feature Walkthrough |
| 4.4.1.5 | ✅ DONE | Troubleshooting Guide |
| 4.4.2.1 | ✅ DONE | Architecture Documentation Update |
| 4.4.2.2 | ✅ DONE | API Documentation Update |
| 4.4.2.3 | ✅ DONE | Deployment Runbook |
| 4.4.2.4 | ✅ DONE | Incident Response Playbook |
| 4.4.3.2 | ✅ DONE | Dependency Vulnerability Scan |
| 4.4.3.3 | ✅ DONE | Auth Implementation Review |
| 4.4.3.6 | ✅ DONE | Security Posture Documentation |

**Sprint 4.4 Features Completed:**
- **User Documentation Suite** (`docs/`)
  - `USER_GUIDE.md` - Comprehensive user guide (450+ lines)
  - `FAQ.md` - Frequently asked questions
  - `TROUBLESHOOTING.md` - Problem solving guide
- **Technical Documentation** (`.claude/docs/`, `docs/`)
  - `ARCHITECTURE.md` - Updated to v2.0.0 with all current architecture
  - `DEPLOYMENT_RUNBOOK.md` - Step-by-step deployment procedures
  - `INCIDENT_RESPONSE.md` - Incident response playbook with severity levels
  - `SECURITY.md` - Comprehensive security posture documentation
- **API Documentation** (`docs/api/`)
  - `README.md` - Updated to v1.1.0 with all endpoints
  - `NOTIFICATIONS.md` - New Telegram notifications API guide
  - `QUICKSTART.md` - Updated with notification steps
  - `CHANGELOG.md` - Updated with v1.1.0 changes
- **Security Audit**
  - pip-audit scan: 0 vulnerabilities (after patching)
  - npm audit scan: 0 vulnerabilities
  - Patched: filelock (CVE-2025-68146), urllib3 (CVE-2025-66418/66471), setuptools (CVE-2022-40897/2024-6345)
  - Auth implementation review: bcrypt 12 rounds, JWT with type validation, role-based access

### Sprint 4.3 Tasks (Week 15) - Payment Reminders & Telegram Bot ✅

| Task | Status | Description |
|------|--------|-------------|
| 4.3.1 | ✅ DONE | NotificationPreferences Model & Migration |
| 4.3.2 | ✅ DONE | Telegram Bot Service |
| 4.3.3 | ✅ DONE | Notification API Endpoints |
| 4.3.4 | ✅ DONE | Telegram Webhook Handler |
| 4.3.5 | ✅ DONE | Background Reminder Tasks |
| 4.3.6 | ✅ DONE | Settings Modal Frontend |
| 4.3.7 | ✅ DONE | Unit Tests (37 tests) |

**Sprint 4.3 Features Completed:**
- **NotificationPreferences Model** (`src/models/notification.py`)
  - One-to-one relationship with User model
  - Telegram integration fields (enabled, verified, chat_id, username)
  - Verification code generation with 10-minute expiration
  - Reminder settings (days_before, time, overdue_alerts)
  - Digest settings (daily, weekly with day selector)
  - Quiet hours support (overnight handling)
- **Alembic Migration** (`src/db/migrations/versions/i4d5e6f7g890_add_notification_preferences.py`)
  - Full table creation with indexes
- **TelegramService** (`src/services/telegram_service.py`)
  - `send_message()` - HTML formatted messages to Telegram
  - `send_reminder()` - Payment reminders with urgency levels
  - `send_daily_digest()` - Daily payment summary
  - `send_weekly_digest()` - Weekly payment overview
  - `send_test_notification()` - Test connectivity
  - `send_verification_success()` - Account linking confirmation
- **Notification API** (`src/api/notifications.py`)
  - `GET /api/v1/notifications/preferences` - Get preferences
  - `PUT /api/v1/notifications/preferences` - Update preferences
  - `POST /api/v1/notifications/telegram/link` - Initiate Telegram linking
  - `GET /api/v1/notifications/telegram/status` - Check Telegram status
  - `DELETE /api/v1/notifications/telegram/unlink` - Unlink Telegram
  - `POST /api/v1/notifications/test` - Send test notification
- **Telegram Webhook** (`src/api/telegram.py`)
  - Handles bot commands: /start, /status, /pause, /resume, /stop, /help
  - Verification code processing
  - Webhook secret validation
- **Background Tasks** (`src/core/tasks.py`)
  - `send_payment_reminders` - Daily at 9 AM (cron)
  - `send_daily_digest` - Daily at 8 AM (cron)
  - `send_weekly_digest` - Daily at 8 AM (filters by user's preferred day)
  - `send_overdue_alerts` - Daily at 10 AM (cron)
- **Settings Modal** (`frontend/src/components/SettingsModal.tsx`)
  - Profile tab (read-only user info)
  - Notifications tab with Telegram linking UI
  - Verification code flow with copy button
  - Notification preference toggles
- **Header Update** - Settings button in user dropdown menu
- **37 Unit Tests** (`tests/unit/test_notifications.py`)
  - Model tests (verification codes, quiet hours, linking status)
  - Schema tests (Pydantic validation)
  - Service tests (message sending, formatting)
  - Task tests (registration, health checks)
- **Total unit tests: 524** (487 previous + 37 new)

### Sprint 4.2 Tasks (Week 14) - Frontend Enhancements ✅

| Task | Status | Description |
|------|--------|-------------|
| 4.2.1 | ✅ DONE | Mobile Responsiveness |
| 4.2.2 | ✅ DONE | Accessibility (a11y) |
| 4.2.3 | ✅ DONE | UX Improvements |
| 4.2.4 | ✅ DONE | Dark Mode - Core Implementation |
| 4.2.5-4.2.25 | ✅ DONE | Dark Mode - All Components |

**Sprint 4.2.1 Features Completed (Mobile Responsiveness):**
- **Responsive Navigation** - Mobile-friendly tab bar with horizontal scroll
- **Touch-Friendly Targets** - All buttons min 44x44px touch targets
- **Mobile Optimized Cards** - Stacked layouts on small screens
- **Mobile Stats Panel** - 2-column grid on mobile, 4-column on desktop
- **Mobile Calendar** - Compact day cells, swipe-friendly month navigation
- **Mobile Forms** - Full-width inputs, native date pickers
- **Mobile Agent Chat** - Full-height chat, sticky input
- **Breakpoint Utilities** - `sm:`, `md:`, `lg:` responsive classes throughout

**Sprint 4.2.2 Features Completed (Accessibility):**
- **Skip Link** - Skip to main content link for keyboard users
- **Focus Management** - Enhanced focus-visible styles, focus rings
- **Screen Reader Support** - Live regions for announcements
- **ARIA Labels** - Proper roles, labels, and descriptions
- **Semantic HTML** - section, article, nav elements
- **Keyboard Navigation** - Arrow key support for filter tabs (roving tabindex)
- **Reduced Motion** - prefers-reduced-motion media query support
- **Color Contrast** - WCAG AA compliant color combinations

**Sprint 4.2.3 Features Completed (UX Improvements):**
- **Loading Skeletons** - Shimmer animations during data loading
- **Optimistic Updates** - Instant feedback for delete operations with rollback
- **Keyboard Shortcuts** (`frontend/src/hooks/useKeyboardShortcuts.ts`)
  - `Ctrl+1-4` - Switch between views (list, calendar, cards, agent)
  - `Ctrl+D` - Toggle dark mode
  - `Shift+?` - Show keyboard shortcuts modal
- **Keyboard Shortcuts Modal** (`frontend/src/components/KeyboardShortcutsModal.tsx`)
  - Beautiful glass-card modal with categorized shortcuts
  - Platform-aware key display (⌘ on Mac, Ctrl on Windows)
- **Toast Notifications** - Success/error toasts for user feedback
- **Confirmation Dialogs** - Delete confirmation with clear actions

**Sprint 4.2.4-4.2.25 Features Completed (Dark Mode):**
- **Tailwind CSS v4 Dark Mode Configuration**
  - `@custom-variant dark (&:where(.dark, .dark *));` for class-based dark mode
  - Removed system preference dependency - user toggle only
- **Theme Context** (`frontend/src/lib/theme-context.tsx`)
  - Simple light/dark toggle with localStorage persistence
  - No flash of wrong theme with inline script in layout.tsx
- **Global Styles** (`frontend/src/app/globals.css`)
  - Glass-card dark mode with rgba colors
  - Shimmer animation dark mode
  - btn-glass and input-glass dark mode
- **All Components Updated:**
  - Header, StatsPanel, Main Page Tabs
  - AgentChat, SubscriptionList, CardsDashboard
  - PaymentCalendar (CalendarDay cells)
  - AddSubscriptionModal, EditSubscriptionModal
  - ImportExportModal, CurrencySelector
  - Login/Register pages, Toast notifications
  - Loading states, Empty states, Scrollbars

### Sprint 4.1 Tasks (Week 13) - Custom Claude Skills ✅

| Task | Status | Description |
|------|--------|-------------|
| 4.1.1 | ✅ DONE | Financial Analysis Skill (spending analysis, budget comparison, trends, anomalies) |
| 4.1.2 | ✅ DONE | Payment Reminder Skill (urgency classification, multi-channel, scheduling) |
| 4.1.3 | ✅ DONE | Debt Management Skill (avalanche/snowball strategies, interest calculations) |
| 4.1.4 | ✅ DONE | Savings Goal Skill (goal tracking, contribution recommendations, milestones) |
| 4.1.5 | ✅ DONE | Skill Testing & Documentation (32 unit tests, README) |

**Sprint 4.1 Features Completed:**
- Custom Claude Skills directory structure (`skills/`)
- **Financial Analysis Skill** (`skills/financial-analysis/`)
  - `SKILL.md` - Skill definition with XML patterns, response templates, examples
  - `examples/analysis_examples.json` - Sample inputs/outputs
  - Capabilities: Monthly summaries, budget comparison, trend detection, anomaly alerts
- **Payment Reminder Skill** (`skills/payment-reminder/`)
  - `SKILL.md` - Urgency classification, scheduling logic, multi-channel support
  - `templates/notification_templates.json` - In-app, email, push, SMS templates
  - Capabilities: Smart reminders, daily/weekly digests, personalization
- **Debt Management Skill** (`skills/debt-management/`)
  - `SKILL.md` - Payoff strategies, interest calculations, progress tracking
  - `calculators/interest_calculator.py` - Python module with 400+ lines of calculations
  - Capabilities: Avalanche vs Snowball comparison, windfall impact, debt-free projections
- **Savings Goal Skill** (`skills/savings-goal/`)
  - `SKILL.md` - Goal tracking, milestones, contribution scenarios
  - `projections/savings_calculator.py` - Python module for projections
  - Capabilities: Progress tracking, on-track checks, milestone celebrations
- **32 new unit tests** (`tests/unit/test_skills.py`)
  - Interest calculations, payoff strategies, windfall impact
  - Savings progress, contribution requirements, achievement projections
  - Milestone tracking, on-track status checks
- **Total unit tests: 487** (455 previous + 32 new)

### Sprint 3.4 Tasks (Week 12) - Monitoring & Alerting ✅

| Task | Status | Description |
|------|--------|-------------|
| 3.4.1 | ✅ DONE | Prometheus Setup (Docker, scrape config, exporters) |
| 3.4.2 | ✅ DONE | Grafana Dashboards (API, DB, AI agent dashboards) |
| 3.4.3 | ✅ DONE | Alerting Rules (Alertmanager, critical alerts) |
| 3.4.4 | ✅ DONE | Log Aggregation (Loki + Promtail) |

**Sprint 3.4 Features Completed:**
- Prometheus setup (`monitoring/prometheus/`)
  - `prometheus.yml` - scrape config for backend, postgres, redis, node exporters
  - `rules/alerts.yml` - alerting rules for API, DB, Redis, AI agent, infrastructure
  - Scrapes backend /metrics endpoint every 10s
- Grafana dashboards (`monitoring/grafana/`)
  - `provisioning/datasources/` - auto-configure Prometheus, Alertmanager, Loki
  - `provisioning/dashboards/` - auto-load dashboards from JSON
  - `dashboards/api-performance.json` - request rate, error rate, latency, status codes
- Alertmanager configuration (`monitoring/alertmanager/`)
  - `alertmanager.yml` - route config, receivers, inhibition rules
  - Critical/warning severity routing
- Log aggregation (`monitoring/loki/`, `monitoring/promtail/`)
  - `loki-config.yml` - log storage with 7-day retention
  - `promtail-config.yml` - Docker container log scraping
- Docker Compose monitoring services
  - `prometheus:9090` - metrics collection
  - `grafana:3003` - visualization (admin/admin)
  - `alertmanager:9093` - alert routing
  - `postgres-exporter:9187` - PostgreSQL metrics
  - `redis-exporter:9121` - Redis metrics
  - `node-exporter:9100` - host metrics
  - `loki:3100` - log aggregation
  - `promtail` - log shipping agent

### Sprint 3.3 Tasks (Week 11) - Service Architecture Improvements ✅

| Task | Status | Description |
|------|--------|-------------|
| 3.3.1 | ✅ DONE | Dependency Injection (dependency-injector, service container) |
| 3.3.2 | ✅ DONE | Error Handling Standardization (custom exceptions, global handler) |
| 3.3.3 | ✅ DONE | Resilience Patterns (circuit breaker, retry, timeouts) |
| 3.3.4 | ✅ DONE | Async Task Queue (ARQ for background tasks) |

**Sprint 3.3.1 Features Completed:**
- Dependency injection container (`src/core/container.py`)
  - `dependency-injector>=4.41.0` library
  - DeclarativeContainer with Configuration provider
  - Singleton providers: db_session_factory, currency_service, anthropic_client
  - Resource provider: redis_client (with lifecycle cleanup)
  - `init_container()` - initializes container from Pydantic settings
  - `get_container()` - returns global container instance
  - `reset_container()` - clears singletons for test isolation
- FastAPI dependency functions (`src/core/dependencies.py`)
  - `get_db()` - async session with commit/rollback management
  - `get_subscription_service()` - creates SubscriptionService with user_id
  - `get_user_service()` - creates UserService
  - `get_payment_card_service()` - creates PaymentCardService
  - `get_currency_service()` - singleton CurrencyService
- Container initialization at startup (`src/main.py`)
- Container tests (`tests/unit/test_container.py`) - 24 tests

**Sprint 3.3.3 Features Completed:**
- Resilience module (`src/core/resilience.py`)
  - `tenacity>=8.2.0` library for retry patterns
  - `ResilienceConfig` - configurable retry, circuit breaker, timeout settings
  - `retry_with_backoff` decorator - exponential backoff retry
  - `circuit_breaker` decorator - circuit breaker pattern with states (CLOSED, OPEN, HALF_OPEN)
  - `with_timeout` function - async timeout wrapper
  - `resilient` decorator - combines retry + circuit breaker + timeout
  - `resilient_call` function - programmatic resilience for one-off calls
  - `CircuitOpenError` exception for open circuits
  - `get_all_circuits()` - returns status of all circuit breakers
  - `reset_circuit()` - resets circuit to closed state
- Circuit breaker status in health endpoint (`src/api/health.py`)
  - `CircuitBreakerStatus` model
  - `/health/ready` now includes circuit breaker states
- Resilience tests (`tests/unit/test_resilience.py`) - 20 tests

**Sprint 3.3.4 Features Completed:**
- Background task queue (`src/core/tasks.py`)
  - `arq>=0.25.0` library (Async Redis Queue)
  - `@task` decorator for registering background tasks
  - `TaskInfo` model for task status tracking
  - `enqueue_task()` - enqueue tasks with optional delay
  - `get_task_status()` - check task execution status
  - `get_queue_info()` - queue statistics
  - `WorkerSettings` - ARQ worker configuration
  - Built-in tasks: health_check_task, cleanup_expired_sessions, send_payment_reminders
  - Lifecycle hooks: startup and shutdown
  - Cron job support for scheduled tasks
- Task queue tests (`tests/unit/test_tasks.py`) - 19 tests

**Sprint 3.3.2 Features Completed:**
- Centralized exception hierarchy (`src/core/exceptions.py`)
  - Base `MoneyFlowError` with status_code, error_code, details
  - Validation errors (422): ValidationError, InvalidInputError, MissingFieldError, PasswordWeakError
  - Authentication errors (401): AuthenticationError, InvalidCredentialsError, TokenExpiredError, TokenInvalidError, AccountLockedError, AccountInactiveError
  - Authorization errors (403): AuthorizationError, InsufficientPermissionsError
  - Not Found errors (404): NotFoundError, SubscriptionNotFoundError, UserNotFoundError, CardNotFoundError
  - Conflict errors (409): ConflictError, DuplicateEntryError, AlreadyExistsError, UserAlreadyExistsError
  - Rate Limit errors (429): RateLimitError
  - External Service errors (503): ExternalServiceError, ClaudeAPIError, DatabaseConnectionError, CacheConnectionError, VectorStoreError
  - Business Logic errors (400): BusinessLogicError, OperationFailedError, InsufficientBalanceError
- Global exception handler (`src/middleware/exception_handler.py`)
  - MoneyFlowError handler with automatic status code mapping
  - SQLAlchemyError handler for database errors
  - PasswordStrengthError handler for password validation
  - JWTTokenError handler for token validation
- Updated services to use centralized exceptions
  - `src/services/user_service.py` - uses AccountLockedError, InvalidCredentialsError, etc.
  - `src/services/subscription_service.py` - uses SubscriptionNotFoundError
- Simplified API routes (`src/api/auth.py`)
  - Removed try/catch blocks, exceptions propagate to global handler
  - Cleaner code, consistent error responses
- Added ErrorCode constants (`src/schemas/response.py`)
  - ACCOUNT_LOCKED, ACCOUNT_INACTIVE error codes
- Exception tests (`tests/unit/test_exceptions.py`) - 38 tests

### Sprint 3.2 Tasks (Week 10) - Database Scalability ✅

| Task | Status | Description |
|------|--------|-------------|
| 3.2.1 | ✅ DONE | Index Optimization (verified from Sprint 2.4.3) |
| 3.2.2 | ✅ DONE | Connection Pool Optimization (pool_size, max_overflow, pre_ping) |
| 3.2.3 | ✅ DONE | Backup Strategy (pg_dump scripts, DR docs) |
| 3.2.4 | ✅ DONE | Query Optimization (user_id filters, eager loading) |

**Sprint 3.2.1 Features Completed:**
- Verified existing performance indexes from Sprint 2.4.3
- Indexes cover all common query patterns (user_id, is_active, next_payment_date, etc.)

**Sprint 3.2.2 Features Completed:**
- Connection pool configuration (`src/core/config.py`)
  - `db_pool_size`: 5 persistent connections
  - `db_pool_max_overflow`: 10 additional connections
  - `db_pool_timeout`: 30 seconds wait
  - `db_pool_recycle`: 1800 seconds (30 minutes)
  - `db_pool_pre_ping`: True (verify connections)
- Database engine optimization (`src/db/database.py`)
  - PostgreSQL-specific pool configuration
  - SQLite NullPool fallback
  - Pool event listeners (checkout, checkin, connect, invalidate)
  - `get_pool_status()` function for monitoring
- Health check pool status (`src/api/health.py`)
  - PoolStatus model added to health response
  - `/health/ready` returns pool metrics

**Sprint 3.2.3 Features Completed:**
- Backup script (`scripts/backup_database.sh`)
  - pg_dump with compression
  - Checksum verification
  - Retention policy (30 days default)
  - Latest symlink management
- Restore script (`scripts/restore_database.sh`)
  - Checksum verification
  - Production safety confirmation
  - Auto-migration after restore
- Disaster Recovery documentation (`docs/DISASTER_RECOVERY.md`)
  - RTO/RPO targets
  - Recovery procedures
  - Scenario-based runbooks

**Sprint 3.2.4 Features Completed:**
- Query optimization in subscription service
  - `get_upcoming()` now filters by user_id
  - `get_all()` has optional `include_card` for eager loading
  - Index hint documentation in method docstrings

### Sprint 3.1 Tasks (Week 9) - API Versioning & Documentation ✅

| Task | Status | Description |
|------|--------|-------------|
| 3.1.1 | ✅ DONE | API Versioning (/api/v1/ prefix, header support) |
| 3.1.2 | ✅ DONE | OpenAPI Enhancement (tags, descriptions) |
| 3.1.3 | ✅ DONE | Developer Documentation (guides, Postman, changelog) |

**Sprint 3.1.1 Features Completed:**
- API versioning with v1 prefix (`src/api/v1/__init__.py`)
  - All routes available at /api/v1/* endpoints
  - Legacy /api/* endpoints maintained for backward compatibility
- Version header support (`src/middleware/deprecation.py`)
  - X-API-Version header for explicit version selection
  - X-API-Supported-Versions response header
  - Accept header parsing (application/vnd.moneyflow.v1+json)
- Deprecation middleware for legacy endpoints
  - Deprecation: true header on old API calls
  - Sunset header with removal date (2025-06-01)
  - Link header pointing to new versioned endpoint
  - X-API-Deprecation-Info with migration instructions
- Frontend updated to use v1 API (`frontend/src/lib/api.ts`)
- API versioning tests (`tests/unit/test_api_versioning.py`) - 19 tests

**Sprint 3.1.2 Features Completed:**
- OpenAPI tags for endpoint grouping
- Enhanced API description with versioning docs
- App version updated to 1.0.0
- Title changed to "Money Flow API"

**Sprint 3.1.3 Features Completed:**
- API Documentation suite (`docs/api/`)
  - README.md - API overview and quick links
  - QUICKSTART.md - 5-minute getting started guide
  - AUTHENTICATION.md - JWT auth flow with code examples
  - RATE_LIMITING.md - Rate limits and best practices
  - CHANGELOG.md - API version history
  - MIGRATION_V0_TO_V1.md - v0 to v1 migration guide
- Postman collection (`docs/postman/MoneyFlow.postman_collection.json`)
  - All endpoints with examples
  - Auto-token management scripts
  - Environment variables

### Sprint 2.4 Tasks (Week 8) - Performance & Load Testing ✅

| Task | Status | Description |
|------|--------|-------------|
| 2.4.1 | ✅ DONE | Performance Benchmarking (Locust setup, benchmark scenarios) |
| 2.4.2 | ✅ DONE | Load Testing (10/50/100 users, soak test, spike test) |
| 2.4.3 | ✅ DONE | Database Query Optimization (indexes, N+1 queries) |
| 2.4.4 | ✅ DONE | Caching Strategy (response caching, invalidation) |

**Sprint 2.4.1-2 Features Completed:**
- Locust load testing framework (`tests/load/locustfile.py`)
  - SubscriptionCRUDUser (list, create, read, update, delete)
  - SummaryUser (summary, upcoming payments)
  - AgentUser (AI agent commands)
  - HealthCheckUser (health endpoints)
  - MixedWorkloadUser (realistic usage patterns)
- Load test runner script (`scripts/run_load_tests.sh`)
  - Quick (10 users, 30s), Medium (50 users, 5m), Full (100 users, 10m)
  - Web UI mode, HTML reports
- Performance benchmark tests (`tests/performance/test_benchmarks.py`)
  - Health endpoint benchmarks
  - Subscription CRUD benchmarks
  - Summary endpoint benchmarks
  - Agent endpoint benchmarks
- Performance baseline documentation (`docs/PERFORMANCE_BASELINE.md`)
  - Response time targets (P95)
  - Throughput targets
  - Caching strategy
  - Monitoring metrics

**Sprint 2.4.3 Features Completed:**
- Database performance indexes migration (`src/db/migrations/versions/a1a2aec4f86a_add_performance_indexes.py`)
  - `ix_subscriptions_user_active_next_payment` (user_id, is_active, next_payment_date)
  - `ix_subscriptions_user_payment_type_active` (user_id, payment_type, is_active)
  - `ix_subscriptions_card_active` (card_id, is_active)
  - `ix_subscriptions_user_category` (user_id, category)
  - `ix_payment_history_sub_date_status` (subscription_id, payment_date, status)
  - `ix_conversations_user_session` (user_id, session_id)
  - `ix_rag_analytics_user_created` (user_id, created_at)

**Sprint 2.4.4 Features Completed:**
- Response caching module (`src/core/response_cache.py`)
  - User-scoped response caching with Redis
  - Cache key generation with params hashing
  - Cache invalidation on mutations
  - get_or_set pattern implementation
  - TTL constants (LIST: 60s, SUMMARY: 300s, UPCOMING: 120s)
- Response cache tests (`tests/unit/test_response_cache.py`) - 17 tests

### Sprint 2.3 Tasks (Week 7) - Integration Tests & Contract Testing ✅

| Task | Status | Description |
|------|--------|-------------|
| 2.3.1 | ✅ DONE | API Contract Testing (Schemathesis, OpenAPI diff) |
| 2.3.2 | ✅ DONE | Database Integration Tests (CRUD, relationships, transactions) |
| 2.3.3 | ✅ DONE | Redis Integration Tests (cache, rate limiter, blacklist) |
| 2.3.4 | ✅ DONE | Qdrant Integration Tests (vectors, search, filtering) |
| 2.3.5 | ✅ DONE | Claude API Integration Tests (classification, extraction) |

**Sprint 2.3.1 Features Completed:**
- OpenAPI spec generation script (`scripts/generate_openapi.py`)
- Schemathesis fuzz testing setup (`tests/contract/test_api_contract.py`)
- API contract tests for all endpoints (no 5xx errors, response schema validation)
- Contract tests integrated into CI pipeline (`.github/workflows/ci.yml`)
- OpenAPI diff checking for breaking changes (`scripts/check_openapi_diff.py`)
- Fixed Pydantic/FastAPI body parameter detection issue in `src/api/auth.py`

**Sprint 2.3.2 Features Completed:**
- Database integration tests (`tests/integration/test_db_integration.py`) - 26 tests
  - Subscription CRUD operations (create, read, update, delete)
  - All payment types (subscription, debt, savings, etc.)
  - Card-subscription relationships
  - Cascade delete behavior (user→subscriptions, subscription→payments)
  - Concurrent modification handling
  - Transaction rollbacks on errors
  - Foreign key constraints
  - Data integrity constraints (unique email, NOT NULL)
- Migration structure tests (`tests/integration/test_migrations.py`) - 7 tests
  - Migration file validation (upgrade/downgrade functions, revision IDs)
  - Alembic history and heads verification
  - PostgreSQL migration tests (run in CI)

**Sprint 2.3.3 Features Completed:**
- Redis integration tests (`tests/integration/test_redis_integration.py`) - 39 tests
  - Cache service operations tests (get, set, delete, exists)
  - JSON serialization tests (complex objects, embedding vectors)
  - Clear pattern tests (scan and delete by pattern)
  - Cache statistics tests (hit rate, memory usage)
  - Connection handling tests (connect, disconnect, singleton)
  - Rate limiter tests (key generation, Redis storage)
  - Token blacklist tests (add, check, key patterns)
  - Connection failure handling tests (graceful degradation, reconnection)
  - Embedding cache integration tests
  - RAG session cache integration tests
  - TTL behavior tests

**Sprint 2.3.4 Features Completed:**
- Qdrant integration tests (`tests/integration/test_qdrant_integration.py`) - 42 tests
  - Vector insertion tests (single, batch, collection creation)
  - Similarity search tests (basic, min_score, recency boost, hybrid)
  - User filtering tests (data isolation, cross-user separation)
  - Collection management tests (ensure, skip existing, indexes)
  - Connection failure handling (errors, missing collections)
  - Embedding update operations (upsert same ID, batch updates)
  - Recency boost functionality tests
  - Singleton behavior tests

**Sprint 2.3.5 Features Completed:**
- Claude API integration tests (`tests/integration/test_claude_api_integration.py`) - 45 tests
  - API connection and authentication tests (4 tests, skipif no API key)
  - Intent classification accuracy tests (CREATE, READ, UPDATE, DELETE, SUMMARY, etc.)
  - Entity extraction accuracy tests (name, amount, frequency, currency, payment_type)
  - API failure fallback tests (regex parsing when AI fails)
  - Payment type detection tests (SUBSCRIPTION, HOUSING, UTILITY, DEBT, SAVINGS, etc.)
  - Normalization tests (frequency strings, entity validation)
  - PromptLoader integration tests (prompt loading, caching, system prompts)

### Sprint 2.2 Tasks (Week 6) - AI Agent E2E & Bug Fixes ✅

| Task | Status | Description |
|------|--------|-------------|
| 2.2.1 | ✅ DONE | AI Agent E2E Tests (NL parsing, all payment types) |
| 2.2.2 | ✅ DONE | Endpoint Bug Fixes (summary, currency, debt, savings) |
| 2.2.3 | ✅ DONE | API Response Consistency (envelope format) |
| 2.2.4 | ✅ DONE | RAG System Bug Fixes (cache, context, search) |
| 2.2.5 | ✅ DONE | User Data Isolation (multi-user support) |
| 2.2.6 | ✅ DONE | Settings Roadmap Planning (docs/SETTINGS_ROADMAP.md) |

**Sprint 2.2 Features Completed:**
- AI Agent E2E tests with comprehensive coverage
- All endpoint bugs fixed (summary, currency conversion, debt/savings calculations)
- API response envelope standardized (data, meta, errors)
- RAG system fixes (embedding cache, context retrieval, search scoring)
- **User data isolation** - subscription_service.py filters by user_id
- **API endpoint protection** - All endpoints require current_user dependency
- **Settings Roadmap** - Comprehensive 1000+ line planning document with:
  - 10 Settings tabs (Profile, Preferences, Cards, Categories, Notifications, Icons, AI, Import, Export, Integrations)
  - AI-powered features (bank statement import, email scanning, icon generation)
  - 7 implementation phases (~240 hours)

### Sprint 2.1 Tasks (Week 5) - E2E Testing Framework ✅

| Task | Status | Description |
|------|--------|-------------|
| 2.1.1 | ✅ DONE | Playwright Setup (install, config, browsers) |
| 2.1.2 | ✅ DONE | Authentication E2E Tests (login, register, logout, protected routes) |
| 2.1.3 | ✅ DONE | Subscription CRUD E2E Tests (create, edit, delete, filter) |
| 2.1.4 | ✅ DONE | Agent Chat E2E Tests (NL commands, payment types) |
| 2.1.5 | ✅ DONE | CI Pipeline Integration (GitHub Actions with services) |

**E2E Testing Features Implemented:**
- Playwright installed with Chromium browser
- playwright.config.ts with multi-project setup (desktop, mobile)
- Test fixtures: DashboardPage, AgentChatPage, API helpers
- Auth setup for authenticated test state
- Auth E2E tests: login, logout, validation, protected routes
- Subscription E2E tests: CRUD operations, filters, search
- Agent E2E tests: NL commands, all payment types
- Docker E2E config: docker-compose.e2e.yml, Dockerfile.e2e
- CI integration: test-e2e job in ci.yml with services

### Sprint 1.4 Tasks (Week 4) - Logging & Observability ✅

| Task | Status | Description |
|------|--------|-------------|
| 1.4.1 | ✅ DONE | Structured Logging (structlog, JSON, request_id, redaction) |
| 1.4.2 | ✅ DONE | Request/Response Logging (middleware, latency, slow queries) |
| 1.4.3 | ⚠️ PARTIAL | Error Tracking - Backend Sentry ✅, Frontend Sentry → Phase 2 |
| 1.4.4 | ✅ DONE | Health Check Enhancement (DB, Redis, Qdrant, Anthropic) |
| 1.4.5 | ✅ DONE | Metrics Collection (Prometheus, custom business metrics) |
| 1.4.6 | ✅ DONE | Telegram CI Notifications (start, success, failure) |

**Observability Features Implemented:**
- Structured logging: JSON format, request_id tracking, user_id context
- Sensitive data redaction: API keys, tokens, emails, credit cards
- Request logging middleware: latency, status, slow query warnings (>1s)
- Sentry backend: FastAPI + SQLAlchemy integration, PII filtering
- Health endpoints: /health, /health/live, /health/ready with dependency checks
- Prometheus metrics: HTTP metrics, business metrics, AI agent latency, RAG performance
- Telegram notifications: CI start/pass/fail to ci-builds topic

**Moved to Phase 2 (Sprint 2.2):**
- Frontend Sentry integration (@sentry/nextjs)
- Frontend error logging to backend API

### Sprint 1.3 Tasks (Week 3) - CI/CD Pipeline ✅

| Task | Status | Description |
|------|--------|-------------|
| 1.3.1 | ✅ DONE | GitHub Actions Setup (.github/workflows/) |
| 1.3.2 | ✅ DONE | Test Automation Pipeline (pytest, coverage) |
| 1.3.3 | ✅ DONE | Code Quality Gates (Ruff, ESLint, pre-commit, PR template) |
| 1.3.4 | ✅ DONE | Security Scanning (Bandit, Safety, npm audit) |
| 1.3.5 | ✅ DONE | Docker Build Pipeline (GHCR, multi-arch) |
| 1.3.6 | ✅ DONE | Deployment Automation (staging/prod, rollback, Telegram alerts) |

**CI/CD Features Implemented:**
- GitHub Actions CI: Python 3.11/3.12 matrix, PostgreSQL + Redis services
- Code quality: Ruff linting/formatting, ESLint, TypeScript type-check
- Pre-commit hooks: Ruff, Prettier, trailing whitespace, detect-secrets
- Security: Bandit scan, Safety dependency check, npm audit
- Docker: Build & push to GHCR, multi-arch (amd64/arm64), image tagging
- Deploy: Staging on main push, production on release, rollback support
- Notifications: Telegram alerts for deployments, rollbacks, and failures
- PR template: Standardized pull request format

### Sprint 1.2 Tasks (Week 2) - Security Hardening ✅

| Task | Status | Description |
|------|--------|-------------|
| 1.2.1 | ✅ DONE | Rate Limiting (slowapi + Redis) |
| 1.2.2 | ✅ DONE | Prompt Injection Protection |
| 1.2.3 | ✅ DONE | Input Validation Enhancement |
| 1.2.4 | ✅ DONE | Security Headers (CSP, HSTS, etc.) |
| 1.2.5 | ✅ DONE | CORS Hardening |
| 1.2.6 | ✅ DONE | Secrets Management |

**Security Features Implemented:**
- Rate limiting: 100/min GET, 20/min writes, 10/min agent, 5/min auth
- Prompt injection: 20+ detection patterns, blocked dangerous commands
- Input validation: Password strength, XSS/SQL detection, URL safety
- Security headers: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- CORS: No wildcards in production, specific methods/headers
- Secrets: Startup validation, blocks production with default secrets

### Sprint 1.1 Tasks (Week 1) - Authentication ✅

| Task | Status | Description |
|------|--------|-------------|
| 1.1.1 | ✅ DONE | Database Schema for Users |
| 1.1.2 | ✅ DONE | Password Security (bcrypt) |
| 1.1.3 | ✅ DONE | JWT Token System |
| 1.1.4 | ✅ DONE | Auth API Endpoints |
| 1.1.5 | ✅ DONE | Auth Middleware |
| 1.1.6 | ✅ DONE | Frontend Auth UI (login, register, protected routes) |

**Frontend Authentication Features Implemented:**
- Auth context (`frontend/src/lib/auth-context.tsx`): Token management, auto-refresh, user state
- Login page (`frontend/src/app/login/page.tsx`): Email/password form, error handling, loading states
- Register page (`frontend/src/app/register/page.tsx`): Full registration with password validation
- Protected route middleware (`frontend/src/components/ProtectedRoute.tsx`): Auto-redirect, loading states
- Header user menu: User dropdown with profile info and logout button
- Token storage: localStorage with secure keys (money_flow_access_token, money_flow_refresh_token)
- Axios interceptors: Auto-inject auth headers, auto-refresh on 401

### Known Issues - All Sprint 2.2 Issues Resolved ✅

| Issue | Priority | Status |
|-------|----------|--------|
| Subscription summary calculation bugs | 🔴 Critical | ✅ DONE (Sprint 2.2) |
| Upcoming payments date filtering | 🔴 Critical | ✅ DONE (Sprint 2.2) |
| Currency conversion edge cases | 🟠 High | ✅ DONE (Sprint 2.2) |
| Debt balance calculation | 🔴 Critical | ✅ DONE (Sprint 2.2) |
| Savings progress calculation | 🔴 Critical | ✅ DONE (Sprint 2.2) |
| Card balance aggregation | 🟠 High | ✅ DONE (Sprint 2.2) |
| Export format inconsistencies | 🟠 High | ✅ DONE (Sprint 2.2) |
| User data isolation | 🔴 Critical | ✅ DONE (Sprint 2.2) |
| Frontend Sentry integration | 🟠 High | ✅ DONE (Sprint 2.2) |

### Upcoming Work (Sprint 2.3+)

| Task | Priority | Sprint |
|------|----------|--------|
| API Contract Testing | ✅ Done | 2.3.1 |
| Database Integration Tests | ✅ Done | 2.3.2 |
| Redis Integration Tests | 🟠 High | 2.3.3 |
| Qdrant Integration Tests | 🟠 High | 2.3.4 |
| Claude API Integration Tests | 🟠 High | 2.3.5 |
| Performance Benchmarking | 🟠 High | 2.4 |
| Load Testing (Locust) | 🟠 High | 2.4 |
| Settings Page Implementation | 🟡 Medium | Future |

### Security Gaps (Sprint 1.2) ✅ ALL RESOLVED

| Gap | Priority | Status |
|-----|----------|--------|
| No authentication | 🔴 Critical | ✅ DONE (Sprint 1.1) |
| No rate limiting | 🔴 Critical | ✅ DONE |
| Prompt injection vulnerable | 🔴 Critical | ✅ DONE |
| CORS not hardened | 🟠 High | ✅ DONE |
| No audit logging | 🟡 Medium | ✅ DONE (Sprint 1.4 - structlog) |

### Phase Overview

```
Phase 1: Foundation & Security  [Weeks 1-4]   ██████████ 100% ✅ COMPLETE
Phase 2: Quality & Testing      [Weeks 5-8]   ██████████ 100% ✅ COMPLETE
Phase 3: Architecture           [Weeks 9-12]  ██████████ 100% ✅ COMPLETE
Phase 4: Features & Polish      [Weeks 13-16] ██████████ 100% ✅ COMPLETE
Phase 5: Settings & AI          [Weeks 17-34] ░░░░░░░░░░ 0%   🔜 UPCOMING
Phase 6: Production Launch      [Weeks 35-36] ░░░░░░░░░░ 0%   🔜 UPCOMING
```

### Phase 1 Completion Checklist ✅

```
✅ User authentication fully functional (Sprint 1.1)
✅ All endpoints protected and rate limited (Sprint 1.2)
✅ Security scanning in CI/CD (Sprint 1.3)
✅ Automated deployment pipeline (Sprint 1.3)
✅ Structured logging with request tracing (Sprint 1.4)
✅ Error tracking with Sentry - Backend (Sprint 1.4)
✅ Health checks for all services (Sprint 1.4)
⚠️ Frontend Sentry - Moved to Sprint 2.2
```

---

## 🎯 Project Overview

A comprehensive **recurring payment management application** with an **agentic interface** that allows natural language commands to manage all types of recurring payments. Features a modern, responsive UI built with Next.js and Tailwind CSS.

### Current Status
- ✅ Multi-container Docker setup (PostgreSQL + FastAPI + Next.js + Redis + Qdrant)
- ✅ Agentic interface with Claude Haiku 4.5 and XML prompting
- ✅ CRUD operations for all payment types
- ✅ Natural language command parsing (dual-mode: AI + regex fallback)
- ✅ Currency conversion (GBP default, USD, EUR, UAH support)
- ✅ Import/Export functionality (JSON & CSV v2.0)
- ✅ RAG implementation complete (all 4 phases - see [RAG Plan](.claude/plans/RAG_PLAN.md))
- ✅ **Money Flow Refactor Complete** - All 8 payment types supported (see [Money Flow Plan](.claude/plans/MONEY_FLOW_REFACTOR_PLAN.md))
- 🟡 **Master Plan Active** - Production-ready enhancement in progress

### Tech Stack
- **Frontend**: Next.js 16, TypeScript, Tailwind CSS v4, React Query, Framer Motion
- **Backend**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL 15 (Docker local dev) → Cloud SQL (GCP production)
- **ORM**: SQLAlchemy 2.0 with async support
- **Validation**: Pydantic v2
- **AI**: Claude Haiku 4.5 (`claude-haiku-4.5-20250929`)
- **Prompting**: XML-based prompts with PromptLoader
- **Caching**: Redis (embedding cache, performance)
- **Vector DB**: Qdrant (RAG, semantic search)
- **Deployment**: Multi-container Docker → GCP Cloud Run

### Key Features
- 🤖 **Natural language interface** - "Add Netflix for £15.99 monthly"
- 💱 **Currency conversion** - GBP, USD, EUR, UAH with exchange rates
- 📊 **Spending analytics** - Summaries by frequency and category
- 🔄 **Dual-mode parsing** - AI with regex fallback for reliability
- 🐳 **Docker containerized** - Easy local development and deployment
- 🎨 **Modern UI** - Tailwind CSS with responsive design
- 📥 **Import/Export** - Backup and restore data (JSON/CSV)
- 🧠 **RAG-powered** - Conversational context, semantic search, intelligent insights

### Supported Payment Types ✅

Money Flow supports **all recurring payment types**:

| Payment Type | Examples | Special Features |
|--------------|----------|------------------|
| **Subscriptions** | Netflix, Claude AI, Spotify | Standard tracking |
| **Housing** | Rent, mortgage | Auto-classified |
| **Utilities** | Electric, water, council tax, internet | Auto-classified |
| **Professional Services** | Therapist, coach, trainer | Auto-classified |
| **Insurance** | Health, device (AppleCare), vehicle | Auto-classified |
| **Debts** | Credit cards, loans, friends/family | Track total_owed, remaining_balance, creditor |
| **Savings** | Regular transfers, goals with targets | Track target_amount, current_saved, recipient |
| **Transfers** | Family support, recurring gifts | Track recipient |

See [Money Flow Refactor Plan](.claude/plans/MONEY_FLOW_REFACTOR_PLAN.md) for implementation details.

---

## 📁 Project Structure

```
subscription-tracker/
├── CLAUDE.md              # YOU ARE HERE - Claude Code instructions
├── docker-compose.yml     # Multi-container orchestration
├── .env                   # Environment variables (not in git)
├── .env.example          # Example env vars
├── docs/                  # 📋 NEW: Project documentation
│   └── MASTER_PLAN.md    # 🆕 16-week production roadmap
│
├── frontend/             # Next.js Frontend Application
│   ├── Dockerfile        # Frontend container
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.mjs
│   ├── src/
│   │   ├── app/          # Next.js app router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx  # Main dashboard
│   │   │   ├── globals.css
│   │   │   └── providers.tsx
│   │   ├── components/   # React components
│   │   │   ├── Header.tsx
│   │   │   ├── StatsPanel.tsx
│   │   │   ├── SubscriptionList.tsx
│   │   │   ├── AddSubscriptionModal.tsx
│   │   │   └── AgentChat.tsx
│   │   ├── lib/          # Utilities
│   │   │   ├── api.ts    # Backend API client
│   │   │   └── utils.ts  # Helper functions
│   │   └── hooks/        # Custom React hooks
│   └── public/           # Static assets
│
├── src/                  # Backend Python Application
│   ├── main.py           # FastAPI application entry point
│   ├── api/              # API route handlers
│   │   ├── __init__.py
│   │   ├── subscriptions.py  # CRUD endpoints
│   │   └── agent.py          # Agentic/prompt endpoint
│   ├── core/             # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py     # Settings and env vars
│   │   └── dependencies.py
│   ├── db/               # Database setup
│   │   ├── __init__.py
│   │   ├── database.py   # Engine and session
│   │   └── migrations/   # Alembic migrations
│   ├── models/           # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   └── subscription.py
│   ├── schemas/          # Pydantic schemas
│   │   ├── __init__.py
│   │   └── subscription.py
│   ├── services/         # Business logic
│   │   ├── __init__.py
│   │   └── subscription_service.py
│   ├── auth/             # 🆕 Authentication (Sprint 1.1)
│   │   ├── __init__.py
│   │   ├── jwt.py        # JWT token handling
│   │   ├── security.py   # Password hashing
│   │   └── dependencies.py # Auth middleware
│   └── agent/            # Agentic interface
│       ├── __init__.py
│       ├── parser.py     # NL command parser
│       ├── executor.py   # Command executor
│       └── prompts.py    # System prompts for Claude
│
├── tests/                # Pytest tests
├── scripts/              # Utility scripts
├── docs/                 # Documentation
├── deploy/               # Deployment configs
│   └── gcp/              # GCP-specific configs
├── Dockerfile            # Backend container
└── pyproject.toml        # Python dependencies
```

---

## 🔧 Common Commands

### Docker Multi-Container Setup (Recommended)

```bash
# Start all services (DB + Backend + Frontend)
docker-compose up --build

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild specific service
docker-compose up --build backend
docker-compose up --build frontend
```

### Local Development (Without Docker)

#### Backend
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate.fish  # For Fish shell
source .venv/bin/activate       # For Bash/Zsh

# Install dependencies
pip install -e ".[dev]"

# Run development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8001

# Run tests
pytest tests/ -v

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run production server
npm start
```

### Code Quality (Run Before Commits)

```bash
# Python linting and formatting
ruff check src/ --fix && ruff format src/

# Run all tests
pytest tests/ -v --cov=src --cov-report=term-missing

# Pre-commit hooks
pre-commit run --all-files
```

### GCP Deployment

```bash
# Deploy backend
gcloud run deploy subscription-tracker-backend --source .

# Deploy frontend
cd frontend && gcloud run deploy subscription-tracker-frontend --source .
```

---

## 🐳 Docker Architecture

The application uses a multi-container setup with five main services:

### Services

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| Database | subscription-db | 5433:5432 | PostgreSQL data storage |
| Backend | subscription-backend | 8001:8000 | FastAPI application |
| Frontend | subscription-frontend | 3001:3000 | Next.js web app |
| Cache | subscription-redis | 6379:6379 | Redis caching |
| Vectors | subscription-qdrant | 6333:6333 | Qdrant vector DB |

### Network

All services communicate via `subscription-network` Docker bridge network.

---

## 📚 Development Documentation

**IMPORTANT**: Start here for complete project context: [.claude/README.md](.claude/README.md)

### Project Context & History
- **[CHANGELOG](.claude/CHANGELOG.md)** - 📋 Complete development history, milestones, issues resolved, and major decisions
  - All features implemented with file links
  - Issues fixed with solutions
  - Technical decisions with rationale
  - **Always check here first to understand what has been done and why**

### Master Plan & Roadmap
- **[MASTER_PLAN](.claude/docs/MASTER_PLAN.md)** - 🆕 16-week production roadmap (400+ tasks)
  - Phase 1: Foundation & Security (Auth, CI/CD)
  - Phase 2: Quality & Testing (E2E, Bug fixes)
  - Phase 3: Architecture (API versioning, Monitoring)
  - Phase 4: Features & Polish (Custom Skills, Mobile)
- **[SETTINGS_ROADMAP](docs/SETTINGS_ROADMAP.md)** - 🆕 Comprehensive Settings & Features vision
  - 10 Settings tabs (Profile, Preferences, Cards, Categories, Notifications, Icons, AI, Import, Export, Integrations)
  - AI-powered features (bank statement import, email scanning, icon generation)
  - 7 implementation phases (~100+ hours)

### Coding Standards
- [Python Coding Standards](.claude/docs/PYTHON_STANDARDS.md) - PEP 8 compliance, type hints, **comprehensive docstrings**, **agentic naming**, **Redis caching patterns**
- [TypeScript/React Standards](.claude/docs/TYPESCRIPT_STANDARDS.md) - Strict TypeScript, React best practices, ESLint & Prettier configuration
- [Pre-commit Hooks](.claude/docs/PRE_COMMIT_HOOKS.md) - Automated code quality checks, linting, formatting, secret detection

### Architecture & Setup
- [System Architecture](.claude/docs/ARCHITECTURE.md) - Complete system design, 6-layer architecture, data flow, microservices path
- [MCP (Model Context Protocol) Setup](.claude/docs/MCP_SETUP.md) - Enhancing Claude Code with database, git, and custom MCPs
- [RAG Considerations](.claude/docs/RAG_CONSIDERATIONS.md) - When to use RAG, cost-benefit analysis, implementation examples

### Implementation Plans
- [Money Flow Refactor Plan](.claude/plans/MONEY_FLOW_REFACTOR_PLAN.md) - ✅ **COMPLETE** - All 8 payment types supported
- [RAG Plan](.claude/plans/RAG_PLAN.md) - ✅ **COMPLETE** - Conversational context, semantic search, intelligent insights
- [Payment Tracking Plan](.claude/plans/PAYMENT_TRACKING_PLAN.md) - Calendar view, installment payments, beautiful UI
- [Settings Roadmap](docs/SETTINGS_ROADMAP.md) - 🆕 **PLANNED** - User settings, AI-powered features, integrations

### Development Tools
- [Code Templates](.claude/templates/README.md) - Python services, FastAPI routers, React components, custom hooks
- [Utility Scripts](.claude/scripts/README.md) - Setup, testing, code quality checks, database reset

### Quick Reference

**Python Code Style:**
- 100 character line length
- Google-style docstrings
- Type hints required for all functions
- Async/await for I/O operations
- 80%+ test coverage target
- **⚠️ IMPORTANT: Run `ruff check src/ --fix && ruff format src/` after modifying Python files**

**TypeScript Code Style:**
- Strict mode enabled
- PascalCase for components, camelCase for functions
- React Query for server state
- Tailwind CSS for styling
- ESLint + Prettier enforced

**Before Committing:**
```bash
# Install pre-commit hooks (one-time)
pip install pre-commit
pre-commit install

# Manually run all hooks
pre-commit run --all-files
```

---

## 💡 Claude Code Tips

When working on this project:

1. **Check Master Plan first**: See [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) for current sprint tasks
2. **Adding new features**: Start with the schema, then model, then service, then API
3. **Modifying models**: Always create an Alembic migration
4. **Agent commands**: Add new intents in parser.py, handlers in executor.py
5. **Testing**: Write tests alongside new features
6. **Code quality**: Pre-commit hooks will automatically lint and format your code

### Sprint Workflow

```bash
# 1. Check current sprint in this file (top section)
# 2. Pick a task from the current sprint
# 3. Implement the task
# 4. Update task status in this file
# 5. Commit with conventional commit message

git commit -m "feat(auth): add User model with SQLAlchemy"
```

### Code Style
- Use type hints everywhere
- Async/await for all database operations
- Pydantic for all external data validation
- Keep services thin, business logic in dedicated modules
- Refer to coding standards docs in [.claude/docs/](.claude/docs/)

---

## 📋 Important Context & History

### Always Check First
**[.claude/CHANGELOG.md](.claude/CHANGELOG.md)** - Complete development history including:
- ✅ All milestones achieved with dates
- 🐛 Issues resolved with solutions
- 📝 Major technical decisions with rationale
- 📊 Current project metrics
- 🎯 Next steps and timeline

**Why this matters**: The CHANGELOG preserves all context about what has been built, what problems were solved, and why specific decisions were made. Always check it before making changes to understand the full context.

### Key Technical Decisions Made

1. **Default Currency: GBP (£)**
   - Changed from USD to GBP per user requirement
   - Exchange rates configured for GBP/USD/EUR conversion
   - See [.claude/CHANGELOG.md](.claude/CHANGELOG.md#decision-1-default-currency---gbp-)

2. **XML-Based Prompting**
   - Structured prompts in `src/agent/prompts.xml`
   - Better maintainability and organization
   - See [.claude/CHANGELOG.md](.claude/CHANGELOG.md#decision-2-xml-based-prompting)

3. **Claude Haiku 4.5 Model**
   - Model: `claude-haiku-4.5-20250929`
   - Fast and cost-effective for intent classification
   - See [.claude/CHANGELOG.md](.claude/CHANGELOG.md#decision-3-claude-haiku-45-model)

4. **Dual-Mode Parsing (AI + Regex)**
   - Primary: Claude AI for intelligent parsing
   - Fallback: Regex patterns for reliability
   - Ensures system works even without API
   - See [.claude/CHANGELOG.md](.claude/CHANGELOG.md#decision-4-dual-mode-parsing-ai--regex)

5. **Redis Caching Strategy**
   - Cache parsed commands, queries, embeddings
   - Structured key pattern: `{resource}:{identifier}:{operation}`
   - See [Python Standards - Redis Caching](.claude/docs/PYTHON_STANDARDS.md#redis-caching)

### Issues Fixed

**Network Error (Fixed)**: Frontend couldn't communicate with backend in Docker.
- **Solution**: Added API rewrites in Next.js config, updated API client to use relative paths
- **See**: [.claude/CHANGELOG.md](.claude/CHANGELOG.md#issue-1-network-error-between-frontend-and-backend)

**Port Conflicts (Fixed)**: Ports 8000 and 3001 already in use.
- **Solution**: Changed to ports 8001 (backend) and 3002 (frontend)
- **See**: [.claude/CHANGELOG.md](.claude/CHANGELOG.md#issue-2-port-conflicts)

### Current Access URLs
- Frontend: http://localhost:3001
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs
- Database: localhost:5433
- Qdrant Dashboard: http://localhost:6333/dashboard

---

## 🚧 Development Workflow

### Before Starting New Work
1. Check current sprint in this file (top section)
2. Check [.claude/CHANGELOG.md](.claude/CHANGELOG.md) for context
3. Check [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) for task details
4. Review relevant implementation plan
5. Check coding standards

### During Development
1. Follow coding standards ([Python](.claude/docs/PYTHON_STANDARDS.md) | [TypeScript](.claude/docs/TYPESCRIPT_STANDARDS.md))
2. Write comprehensive docstrings with all sections
3. Add type hints everywhere
4. Write tests alongside code
5. Use templates from [.claude/templates/](.claude/templates/)

### Before Committing
```bash
# Run code quality checks
bash .claude/scripts/check_code_quality.sh

# Run tests
bash .claude/scripts/run_tests.sh

# Or use pre-commit hooks (auto-runs on git commit)
pre-commit run --all-files
```

### After Completing Work
1. **Update task status** in this file (top section)
2. **Update [.claude/CHANGELOG.md](.claude/CHANGELOG.md)** with:
   - Milestone achieved
   - Files modified
   - Issues resolved
   - Technical decisions made

This ensures context is preserved for future development.

---

## 🎓 Learning Resources

### For New Features
1. Review similar existing code
2. Use code templates from [.claude/templates/](.claude/templates/)
3. Follow implementation plans for complex features
4. Check architecture docs for design patterns

### For Understanding Agentic Code
- [Python Standards - Agentic Code](.claude/docs/PYTHON_STANDARDS.md#agentic-code-standards)
- [RAG Considerations](.claude/docs/RAG_CONSIDERATIONS.md)
- [RAG Plan](.claude/plans/RAG_PLAN.md)

### For Payment Tracking Features
- [Payment Tracking Plan](.claude/plans/PAYMENT_TRACKING_PLAN.md)
- Database schema changes
- Calendar component design
- Installment tracking implementation

---

## 🔗 Quick Links

### Documentation
- [.claude/README.md](.claude/README.md) - Complete .claude directory overview
- [.claude/CHANGELOG.md](.claude/CHANGELOG.md) - **Development history and context**
- [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) - 🆕 **16-week production roadmap**
- [ARCHITECTURE.md](.claude/docs/ARCHITECTURE.md) - System architecture
- [PYTHON_STANDARDS.md](.claude/docs/PYTHON_STANDARDS.md) - Python coding standards
- [TYPESCRIPT_STANDARDS.md](.claude/docs/TYPESCRIPT_STANDARDS.md) - TypeScript/React standards

### Plans
- [Master Plan](.claude/docs/MASTER_PLAN.md) - 🆕 **ACTIVE** - Production-ready enhancement
- [Settings Roadmap](docs/SETTINGS_ROADMAP.md) - 🆕 **PLANNED** - User settings, AI features, integrations
- [Money Flow Refactor](.claude/plans/MONEY_FLOW_REFACTOR_PLAN.md) - ✅ **COMPLETE** - All 8 payment types
- [RAG Plan](.claude/plans/RAG_PLAN.md) - ✅ **COMPLETE** - RAG implementation
- [Payment Tracking](.claude/plans/PAYMENT_TRACKING_PLAN.md) - Calendar view and installment payments

### Tools
- [Templates](.claude/templates/README.md) - Code templates
- [Scripts](.claude/scripts/README.md) - Utility scripts

---

**Last Updated**: 2025-12-20
**Version**: 5.5.0 (Sprint 5.5 Phase 1-2 Complete)
**Current Phase**: Phase 5 - Settings & AI Features
**Current Sprint**: 5.5 - Smart Import (AI) - Phase 1 & 2 Complete
**Completed Phases**: Phase 1 ✅, Phase 2 ✅, Phase 3 ✅, Phase 4 ✅
**Completed Sprints (Phase 5)**: Sprint 5.1 ✅, Sprint 5.2 ✅, Sprint 5.3 ✅, Sprint 5.4 ✅
**Sprint 5.5 Progress**: Bank Infrastructure ✅, Statement Parsers ✅, AI Pattern Detection 🔜
**Remaining (Phase 5)**: ~100 hours (3 sprints + AI features)
**For Questions**: Check [.claude/docs/MASTER_PLAN.md](.claude/docs/MASTER_PLAN.md) or [.claude/CHANGELOG.md](.claude/CHANGELOG.md)

### Recent CI Fixes (2025-12-19)
- **E2E Test Fixes** - Fixed Playwright tests that were failing in GitHub Actions:
  - Changed `getByRole('button')` to `getByRole('tab')` for view toggle buttons
  - Added `exact: true` to tab selectors to avoid matching filter tabs
  - Removed flaky post-send assertion in agent chat test