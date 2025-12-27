# PDF Report Enhancement Plan

## Overview

This plan addresses issues with the current PDF report generation and outlines enhancements for a more comprehensive and accurate report system.

---

## Current Issues

### 1. Currency Handling Problems
- **No currency conversion**: Report shows raw amounts without converting to a unified currency
- **Wrong currency symbols**: Uses single hardcoded symbol (e.g., £) regardless of subscription's actual currency
- **Example bug**: A $100 USD subscription and a £100 GBP subscription both show as "£100" without conversion

### 2. Payment Data Issues
- **next_payment_date handling**: May not properly compute dates for overdue or distant payments
- **Missing payment history**: Doesn't include actual payment history from `payment_history` table
- **No debt/savings tracking**: Doesn't show debt progress or savings goals

### 3. Limited Report Options
- **No date range selection**: Always shows "next 30 days" for upcoming payments
- **No section toggles**: Can't exclude/include specific sections
- **No card breakdown**: Missing spending by payment card
- **Limited customization**: Fixed report structure

### 4. Missing Features
- **No charts/graphs**: Text-only, no visual representations
- **No comparison data**: No month-over-month or year-over-year comparisons
- **No budget tracking**: Doesn't show category budget usage
- **No payment mode grouping**: Doesn't separate recurring/debt/savings

---

## Enhancement Plan

### Phase 1: Fix Currency Handling (Priority: Critical)

**Goal**: Ensure all amounts are correctly converted and displayed.

#### Tasks:
1. **Inject CurrencyService into PDFReportService**
   - Pass `CurrencyService` instance to constructor
   - Use async `convert()` method for conversions

2. **Convert all amounts to report currency**
   - In `_build_summary()`: Convert each subscription amount before summing
   - In `_build_category_breakdown()`: Convert amounts during category grouping
   - In `_build_upcoming_payments()`: Convert displayed amounts
   - In `_build_payments_table()`: Show both original and converted amounts

3. **Show original currency info**
   - Display format: "£100.00 (≈ $127.00 USD)" for non-base currencies
   - Add "Currency" column to All Payments table

4. **Handle conversion errors gracefully**
   - Fallback to original amount if conversion fails
   - Add footnote indicating unconverted currencies

#### Files to Modify:
- `src/services/pdf_report_service.py` - Add currency conversion
- `src/api/subscriptions.py` - Pass currency service to report generation

---

### Phase 2: Fix Payment Data (Priority: High)

**Goal**: Accurately pull and display payment information.

#### Tasks:
1. **Proper next_payment_date calculation**
   - Use `subscription_service.calculate_next_payment_date()` if available
   - Handle overdue payments (show as "Overdue" instead of negative days)

2. **Include payment history**
   - New section: "Recent Payment History" (last 30 days)
   - Show: date, subscription name, amount, status (completed/failed)

3. **Add debt/savings progress**
   - For debt: Show total_owed, remaining_balance, paid percentage
   - For savings: Show target_amount, current_saved, progress percentage
   - Include progress bars in PDF

4. **Payment status accuracy**
   - Check if payment was recorded for current period
   - Show "Paid" / "Pending" / "Overdue" status

#### Files to Modify:
- `src/services/pdf_report_service.py` - Add new sections, fix date handling
- `src/api/subscriptions.py` - Fetch payment history for report

---

### Phase 3: Report Configuration Options (Priority: Medium)

**Goal**: Allow users to customize report content.

#### New Report Configuration Model:
```python
class ReportConfig:
    # Date Range
    date_range_days: int = 30  # For upcoming payments
    history_days: int = 30     # For payment history

    # Currency
    target_currency: str = "GBP"
    show_original_currency: bool = True

    # Sections to Include
    include_summary: bool = True
    include_category_breakdown: bool = True
    include_card_breakdown: bool = True
    include_upcoming_payments: bool = True
    include_payment_history: bool = True
    include_debt_progress: bool = True
    include_savings_progress: bool = True
    include_all_payments_table: bool = True
    include_budget_status: bool = True

    # Grouping
    group_by_payment_mode: bool = True  # recurring, debt, savings
    group_by_category: bool = True
    group_by_card: bool = False

    # Filtering
    payment_modes: list[str] | None = None  # None = all
    categories: list[str] | None = None
    cards: list[str] | None = None
    include_inactive: bool = False

    # Visual Options
    include_charts: bool = True
    color_scheme: str = "default"  # default, monochrome, high-contrast
    page_size: str = "a4"
```

#### New API Endpoint:
```
POST /api/v1/subscriptions/export/pdf
{
  "date_range_days": 60,
  "target_currency": "USD",
  "sections": ["summary", "category_breakdown", "upcoming_payments"],
  "group_by": "category",
  "include_inactive": false
}
```

#### Files to Create/Modify:
- `src/schemas/report.py` - ReportConfig schema
- `src/services/pdf_report_service.py` - Accept config, conditional sections
- `src/api/subscriptions.py` - Accept POST with config body

---

### Phase 4: New Report Sections (Priority: Medium)

**Goal**: Add valuable new sections to reports.

#### 4.1 Card Breakdown Section
```
+-----------------------------------------------+
| Spending by Payment Card                      |
+------------------+------------+---------------+
| Card             | Monthly    | Yearly        |
+------------------+------------+---------------+
| Chase Sapphire   | £450.00    | £5,400.00     |
| Monzo Personal   | £125.00    | £1,500.00     |
| Unassigned       | £50.00     | £600.00       |
+------------------+------------+---------------+
| TOTAL            | £625.00    | £7,500.00     |
+------------------+------------+---------------+
```

#### 4.2 Debt Progress Section
```
+-----------------------------------------------+
| Debt Tracker                                  |
+------------------+----------+--------+--------+
| Debt Name        | Total    | Paid   | Left   |
+------------------+----------+--------+--------+
| Credit Card      | £5,000   | £2,500 | £2,500 |
| Student Loan     | £20,000  | £5,000 | £15,000|
+------------------+----------+--------+--------+
| Progress: [========>----------] 32%           |
+-----------------------------------------------+
```

#### 4.3 Savings Goals Section
```
+-----------------------------------------------+
| Savings Goals                                 |
+------------------+----------+--------+--------+
| Goal Name        | Target   | Saved  | Left   |
+------------------+----------+--------+--------+
| Emergency Fund   | £10,000  | £6,500 | £3,500 |
| Vacation 2025    | £3,000   | £1,800 | £1,200 |
+------------------+----------+--------+--------+
| Progress: [============>------] 65%           |
+-----------------------------------------------+
```

#### 4.4 Budget Status Section
```
+-----------------------------------------------+
| Budget Status (This Month)                    |
+------------------+----------+--------+--------+
| Category         | Budget   | Spent  | Status |
+------------------+----------+--------+--------+
| Entertainment    | £100     | £85    | ✓ OK   |
| Utilities        | £150     | £175   | ⚠ OVER |
| Subscriptions    | £50      | £45    | ✓ OK   |
+------------------+----------+--------+--------+
```

#### 4.5 Payment History Section
```
+-----------------------------------------------+
| Recent Payments (Last 30 Days)                |
+------------------+------------+--------+------+
| Date             | Payment    | Amount | Stat |
+------------------+------------+--------+------+
| Dec 15, 2025     | Netflix    | £15.99 | ✓    |
| Dec 12, 2025     | Spotify    | £10.99 | ✓    |
| Dec 10, 2025     | Rent       | £1,200 | ✓    |
+------------------+------------+--------+------+
```

---

### Phase 5: Visual Enhancements (Priority: Low)

**Goal**: Add charts and improve visual design.

#### Tasks:
1. **Pie Chart**: Spending by category
2. **Bar Chart**: Monthly spending trend (last 6 months)
3. **Progress Bars**: For debt payoff and savings goals
4. **Color Coding**:
   - Green for on-track/paid
   - Yellow for due soon
   - Red for overdue/over-budget

#### Libraries to Consider:
- `reportlab.graphics.charts` - Built-in ReportLab charts
- `matplotlib` - Generate chart images to embed

---

## Implementation Order

### Sprint A: Critical Fixes (4h) ✅ COMPLETE
1. ✅ Fix currency conversion in all sections
2. ✅ Fix currency symbol display
3. ✅ Add original currency column to All Payments table

**Completed 2025-12-20:**
- Added `currency_service` parameter to PDFReportService
- Added `_convert_amount()` method for currency conversion
- Added `_get_amount_display()` for formatting with original amount
- Updated `_build_summary()` to convert amounts before summing
- Updated `_build_category_breakdown()` to use converted amounts
- Updated `_build_upcoming_payments()` to show converted+original amounts
- Updated `_build_payments_table()` with new Currency column
- Added `target_currency` query parameter to API endpoint
- Added async `generate_report_async()` method
- Added 14 new tests for currency conversion (49 total tests)

### Sprint B: Payment Data Fixes (3h) ✅ COMPLETE
1. ✅ Fix next_payment_date handling (overdue detection)
2. ✅ Add overdue payments detection and display with red highlighting
3. ✅ Add payment history section to report

**Completed 2025-12-20:**
- Renamed section to "Upcoming & Overdue Payments"
- Added overdue detection (negative days_until)
- Overdue payments shown first, highlighted in red (#fee2e2 background)
- Status column shows "X days overdue", "Due Today", "Tomorrow", "In Xd"
- Overdue count summary at bottom of section
- New `_build_payment_history()` method added
- Shows last 30 days of payments from payment_history relationship
- Status symbols: ✓ completed, ⋯ pending, ✗ failed, — cancelled
- Color-coded status: green for completed, red for failed
- Summary shows total payments, completed count, failed count
- Added 14 new tests (5 overdue, 9 payment history)
- Total tests: 63 (49 previous + 14 new)

### Sprint C: Report Configuration (4h) ✅ COMPLETE
1. ✅ Create ReportConfig schema
2. ✅ Update API endpoint to accept config (POST /api/v1/subscriptions/export/pdf)
3. ✅ Implement conditional section rendering

**Completed 2025-12-20:**
- Created `src/schemas/report.py` with comprehensive configuration models:
  - `PageSize` enum (A4, Letter)
  - `ColorScheme` enum (default, monochrome, high_contrast)
  - `ReportSections` model (9 toggle options)
  - `ReportFilters` model (payment_modes, categories, cards, include_inactive)
  - `ReportOptions` model (show_original_currency, include_charts, color_scheme)
  - `ReportConfig` model with date_range_days, history_days, target_currency
- Updated `src/services/pdf_report_service.py`:
  - Constructor accepts optional `ReportConfig` parameter
  - Config values override individual constructor parameters
  - Conditional section rendering based on config.sections
  - Configurable date_range_days for upcoming payments
- Added POST endpoint in `src/api/subscriptions.py`:
  - `POST /api/v1/subscriptions/export/pdf` accepts ReportConfig body
  - GET endpoint preserved for backward compatibility
- Added 15 new tests (9 TestReportConfig, 6 TestReportConfigSchema)
- Total tests: 78 (63 previous + 15 new)

### Sprint D: New Sections (4h) ✅ COMPLETE
1. ✅ Add Card Breakdown section
2. ✅ Add Debt Progress section
3. ✅ Add Savings Goals section
4. ✅ Add Budget Status section

**Completed 2025-12-20:**
- **Card Breakdown Section** (`_build_card_breakdown`):
  - Groups payments by assigned payment card
  - Shows monthly and yearly totals per card
  - "Unassigned" category for payments without cards
  - Currency conversion for multi-currency reports
- **Debt Progress Section** (`_build_debt_progress`):
  - Filters to DEBT payment mode/type
  - Shows total_owed, paid, remaining for each debt
  - Text-based progress bar visualization (█░)
  - Creditor name display
  - Purple header theme for distinction
- **Savings Goals Section** (`_build_savings_progress`):
  - Filters to SAVINGS payment mode/type
  - Shows target, saved, remaining for each goal
  - Text-based progress bar (caps at 100% for display)
  - Recipient display for transfers
  - Green header theme (goal achievement)
- **Budget Status Section** (`_build_budget_status`):
  - Shows spending vs budget for categories with budgets
  - Status indicators: ✓ OK (<90%), ⚡ WARNING (90-100%), ⚠ OVER (>100%)
  - Color-coded rows (red for over, yellow for warning)
  - Blue header theme
  - Summary of over-budget categories
- **Section toggle support**: All new sections controlled by ReportConfig.sections
- **24 new tests** for new sections (5 card, 5 debt, 6 savings, 6 budget, 2 integration)
- Total tests: 102 (78 previous + 24 new)

### Sprint E: Visual Enhancements (2h) ✅ COMPLETE
1. ✅ Add progress bars for debt/savings (text-based: █░)
2. ✅ Add category pie chart
3. ✅ Color-code payment statuses

**Completed 2025-12-21:**
- **Category Pie Chart** (`_build_category_pie_chart`)
  - Added `CHART_COLORS` constant with 10 visually distinct colors
  - Pie chart with percentage labels for each category
  - Limited to 8 slices, excess categories grouped into "Other"
  - Enabled via `ReportConfig.options.include_charts=True`
  - Drawing size: 400x200px with "Monthly Spending Distribution" title
- **Enhanced Payment Status Color-Coding**
  - Overdue: ⚠ symbol, red background (#fee2e2), red text (#dc2626)
  - Due Today: ⚡ symbol, orange background (#ffedd5), orange text (#ea580c)
  - Tomorrow: ⚡ symbol, light orange background (#fff7ed), orange text
  - Within 3 days: ○ symbol, light yellow background (#fefce8), amber text (#ca8a04)
  - Within 7 days: ○ symbol, light blue background (#eff6ff), blue text (#2563eb)
  - 7+ days away: green text (#16a34a)
- **All Payments Table Status Enhancement**
  - Active: ✓ Active (green #16a34a)
  - Inactive: ○ Inactive (gray #9ca3af)
  - Inactive rows have muted text for other columns
- **20 new tests** (8 pie chart, 10 color-coding, 3 chart colors)
- Total tests: 122 (102 previous + 20 new)

---

## API Changes

### Current API:
```
GET /api/v1/subscriptions/export/pdf?include_inactive=false&page_size=a4
```

### Enhanced API:
```
POST /api/v1/subscriptions/export/pdf
Content-Type: application/json

{
  "page_size": "a4",
  "target_currency": "GBP",
  "date_range_days": 60,
  "history_days": 30,
  "sections": {
    "summary": true,
    "category_breakdown": true,
    "card_breakdown": true,
    "upcoming_payments": true,
    "payment_history": true,
    "debt_progress": true,
    "savings_progress": true,
    "budget_status": true,
    "all_payments": true
  },
  "filters": {
    "payment_modes": ["recurring", "debt"],
    "categories": null,
    "cards": null,
    "include_inactive": false
  },
  "options": {
    "show_original_currency": true,
    "include_charts": true,
    "color_scheme": "default"
  }
}
```

---

## Frontend UI Changes

### Current Modal:
- Single "Generate PDF Report" button
- Include inactive checkbox

### Enhanced Modal:
```
+-----------------------------------------------+
| Generate Report                               |
+-----------------------------------------------+
| Currency: [GBP ▼]        Page Size: [A4 ▼]    |
+-----------------------------------------------+
| Date Range                                    |
| Upcoming: [30 days ▼]   History: [30 days ▼]  |
+-----------------------------------------------+
| Sections to Include                           |
| ☑ Summary Statistics                          |
| ☑ Spending by Category                        |
| ☑ Spending by Card                            |
| ☑ Upcoming Payments                           |
| ☑ Recent Payment History                      |
| ☑ Debt Progress                               |
| ☑ Savings Goals                               |
| ☑ Budget Status                               |
| ☑ All Payments Table                          |
+-----------------------------------------------+
| Filters                                       |
| Payment Types: [All ▼]                        |
| Categories: [All ▼]                           |
| Cards: [All ▼]                                |
| ☐ Include inactive                            |
+-----------------------------------------------+
| Options                                       |
| ☑ Show original currencies                    |
| ☑ Include charts                              |
+-----------------------------------------------+
| [Cancel]              [Generate Report]       |
+-----------------------------------------------+
```

---

## Files to Create/Modify

### Backend:
- `src/schemas/report.py` (NEW) - Report configuration schemas
- `src/services/pdf_report_service.py` (MODIFY) - Major refactor
- `src/api/subscriptions.py` (MODIFY) - New POST endpoint

### Frontend:
- `frontend/src/components/ReportConfigModal.tsx` (NEW) - Report configuration UI
- `frontend/src/lib/api.ts` (MODIFY) - Add report config types

---

## Success Criteria

1. ✅ All amounts correctly converted to target currency (Sprint A)
2. ✅ Original currency shown alongside converted amount (Sprint A)
3. ✅ Proper handling of overdue payments (Sprint B)
4. ✅ Payment history section with recent transactions (Sprint B)
5. ✅ Debt and savings progress visible (Sprint D)
6. ✅ Budget status per category (Sprint D)
7. ✅ Card breakdown available (Sprint D)
8. ✅ Configurable sections via API (Sprint C)
9. ✅ Visual charts for spending breakdown (Sprint E)
10. 🔜 Frontend UI for report customization (future sprint)

---

## Estimated Effort

| Phase | Description | Hours |
|-------|-------------|-------|
| A | Critical currency fixes | 4h |
| B | Payment data fixes | 3h |
| C | Report configuration | 4h |
| D | New sections | 4h |
| E | Visual enhancements | 2h |
| **Total** | | **17h** |

---

## Notes

- Phase A should be implemented first as it fixes critical bugs
- Phase B and C can be done in parallel
- Phase D depends on B for payment history data
- Phase E is nice-to-have and can be deferred

**🎉 ALL BACKEND SPRINTS COMPLETE! (A, B, C, D, E)**
- Total tests: 122 (35 original + 87 new)
- All success criteria met (9/10, with frontend UI deferred)

Last Updated: 2025-12-21
