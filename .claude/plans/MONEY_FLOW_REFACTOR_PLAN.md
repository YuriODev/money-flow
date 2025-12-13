# Money Flow Refactor Plan

**Status**: Phase 1 - Backend Complete ✅ | Phase 2 - Frontend Complete ✅ | Phase 3 - AI Agent Complete ✅
**Duration**: 3 Phases
**Priority**: High
**Last Updated**: 2025-12-03

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Target Architecture](#target-architecture)
4. [Data Model Changes](#data-model-changes)
5. [Phase Plan](#phase-plan)
6. [Milestone Tracker](#milestone-tracker)
7. [Migration Strategy](#migration-strategy)
8. [Risk Assessment](#risk-assessment)

---

## Executive Summary

### What is This Refactor?

Transform "Subscription Tracker" into "**Money Flow**" - a comprehensive recurring payment management app that handles not just subscriptions, but all types of recurring financial outflows:

- **Subscriptions** - Digital services (Netflix, Claude AI, etc.)
- **Housing** - Rent, mortgage payments
- **Utilities** - Electricity, water, council tax, internet
- **Professional Services** - Therapist, coach, trainer
- **Insurance** - Health, device, vehicle
- **Debts** - Credit cards, loans, money owed to friends/family
- **Savings** - Regular transfers to savings accounts, goals
- **Transfers** - Family support, recurring gifts

### Why We Need It

| Current Limitation | Money Flow Solution |
|-------------------|---------------------|
| Only tracks subscriptions | Tracks all recurring payments |
| No debt tracking | Track total owed + remaining balance |
| No savings goals | Track progress toward targets |
| Single category level | Two-tier: payment_type + subcategory |
| App name too narrow | "Money Flow" reflects full capability |

### User's Financial Overview

| Category | Items | Monthly Impact |
|----------|-------|----------------|
| **Housing** | Rent (£1,137.50) | £1,137.50 |
| **Utilities** | EDF (£70+£100), Thames Water (biannual), Council Tax | ~£200/month |
| **Subscriptions** | 29 current items | ~£500/month |
| **Professional** | Therapist (4000 UAH/wk), Coach (6000 UAH/mo) | ~£300/month equiv |
| **Debts** | Credit cards, friends/family, collector (final payment Dec) | Variable |
| **Savings** | Daughter's account, personal savings, GF transfers | TBD |

---

## Current State Analysis

### Existing Data Model

```python
# src/models/subscription.py
class Subscription(Base):
    id: UUID
    name: str
    amount: Decimal
    currency: str  # GBP, USD, EUR, UAH
    frequency: Frequency  # daily, weekly, biweekly, monthly, quarterly, yearly
    frequency_interval: int
    start_date: date
    next_payment_date: date
    last_payment_date: date | None
    category: str | None  # Entertainment, Health, etc.
    is_active: bool
    notes: str | None
    payment_method: str | None
    reminder_days: int
    icon_url: str | None
    color: str
    auto_renew: bool
    # Installment fields (already exist)
    is_installment: bool
    total_installments: int | None
    completed_installments: int
    installment_start_date: date | None
    installment_end_date: date | None
```

### What Already Exists (Can Be Reused)

- ✅ Installment tracking (total/completed) - perfect for debt payments
- ✅ Multiple currencies (GBP, USD, EUR, UAH)
- ✅ Flexible frequency (daily to yearly)
- ✅ Notes field for context
- ✅ Payment history tracking
- ✅ Import/Export functionality
- ✅ AI agent with natural language

### What's Missing

- ❌ Payment type classification (subscription vs debt vs savings)
- ❌ Total debt amount tracking
- ❌ Remaining balance for debts
- ❌ Savings goal/target amount
- ❌ Current saved progress
- ❌ Creditor/recipient field
- ❌ UI for different payment types
- ❌ App rebrand to "Money Flow"

---

## Target Architecture

### New Payment Type Enum

```python
class PaymentType(str, Enum):
    """Top-level payment classification."""
    subscription = "subscription"      # Digital services, streaming
    housing = "housing"                # Rent, mortgage
    utility = "utility"                # Electric, gas, water, internet, council tax
    professional_service = "professional_service"  # Therapist, coach, trainer
    insurance = "insurance"            # Health, device, vehicle
    debt = "debt"                      # Credit cards, loans, personal debts
    savings = "savings"                # Regular savings transfers, goals
    transfer = "transfer"              # Family support, recurring gifts
```

### Enhanced Payment Model

```python
class Payment(Base):  # Renamed from Subscription
    """Unified recurring payment model."""

    # ===== Existing Fields (unchanged) =====
    id: UUID
    name: str
    amount: Decimal
    currency: str
    frequency: Frequency
    frequency_interval: int
    start_date: date
    next_payment_date: date
    last_payment_date: date | None
    category: str | None  # Now subcategory (Entertainment, Electric, etc.)
    is_active: bool
    notes: str | None
    payment_method: str | None
    reminder_days: int
    icon_url: str | None
    color: str
    auto_renew: bool
    is_installment: bool
    total_installments: int | None
    completed_installments: int
    installment_start_date: date | None
    installment_end_date: date | None
    created_at: datetime
    updated_at: datetime

    # ===== NEW Fields =====
    payment_type: PaymentType = PaymentType.subscription  # NEW: Top-level type

    # Debt-specific fields
    total_owed: Decimal | None = None      # NEW: Original debt amount
    remaining_balance: Decimal | None = None  # NEW: What's left to pay
    creditor: str | None = None            # NEW: Who you owe (bank, friend name, etc.)

    # Savings-specific fields
    target_amount: Decimal | None = None   # NEW: Savings goal
    current_saved: Decimal | None = None   # NEW: Progress toward goal
    recipient: str | None = None           # NEW: Who receives (daughter's account, GF, etc.)
```

### Category Mapping

| Payment Type | Suggested Subcategories (category field) |
|--------------|------------------------------------------|
| subscription | Entertainment, Productivity, Storage, Communication, Business |
| housing | Rent, Mortgage, Property Insurance, Ground Rent |
| utility | Electric, Gas, Water, Internet, Mobile, Council Tax |
| professional_service | Therapist, Coach, Trainer, Tutor, Cleaner |
| insurance | Health, Device (AppleCare), Vehicle, Life, Travel |
| debt | Credit Card, Personal Loan, Student Loan, Friends/Family, Collector |
| savings | Emergency Fund, Child Account, Investment, Holiday, Retirement |
| transfer | Family Support, Partner, Charity, Gifts |

---

## Data Model Changes

### Database Migration Plan

**Migration 1: Add payment_type column**
```sql
ALTER TABLE subscriptions
ADD COLUMN payment_type VARCHAR(50) DEFAULT 'subscription';
```

**Migration 2: Add debt tracking fields**
```sql
ALTER TABLE subscriptions
ADD COLUMN total_owed DECIMAL(12,2),
ADD COLUMN remaining_balance DECIMAL(12,2),
ADD COLUMN creditor VARCHAR(255);
```

**Migration 3: Add savings fields**
```sql
ALTER TABLE subscriptions
ADD COLUMN target_amount DECIMAL(12,2),
ADD COLUMN current_saved DECIMAL(12,2),
ADD COLUMN recipient VARCHAR(255);
```

**Migration 4: Rename table (optional, for clarity)**
```sql
ALTER TABLE subscriptions RENAME TO payments;
```

### Backward Compatibility

- All existing subscriptions get `payment_type = 'subscription'`
- New fields are nullable - existing data unaffected
- API maintains `/api/subscriptions` alongside new `/api/payments` (deprecation period)
- Export format version bumped to "2.0" with new fields

---

## Phase Plan

### Phase 1: Data Model & Backend (Core)

**Goal**: Add new fields, create migration, update services

| Task | Description | Files |
|------|-------------|-------|
| 1.1 | Add PaymentType enum | `src/models/subscription.py` |
| 1.2 | Add new fields to model | `src/models/subscription.py` |
| 1.3 | Create Alembic migration | `alembic/versions/xxx_add_payment_type.py` |
| 1.4 | Update Pydantic schemas | `src/schemas/subscription.py` |
| 1.5 | Update service layer | `src/services/subscription_service.py` |
| 1.6 | Add payment_type filter to API | `src/api/subscriptions.py` |
| 1.7 | Update import/export for new fields | `src/api/subscriptions.py` |
| 1.8 | Update summary endpoint | `src/api/subscriptions.py` |
| 1.9 | Write unit tests | `tests/unit/test_payment_types.py` |
| 1.10 | Write integration tests | `tests/integration/test_payments_api.py` |

**Deliverables**:
- New PaymentType enum
- Enhanced database model
- Updated API with payment_type filter
- All existing tests passing
- New tests for payment types

---

### Phase 2: Frontend & UI

**Goal**: Update UI to support payment types, rebrand to "Money Flow"

| Task | Description | Files |
|------|-------------|-------|
| 2.1 | Rename app to "Money Flow" | `frontend/src/components/Header.tsx` |
| 2.2 | Update TypeScript types | `frontend/src/lib/api.ts` |
| 2.3 | Add payment type selector | `frontend/src/components/AddPaymentModal.tsx` |
| 2.4 | Add payment type filter tabs | `frontend/src/components/PaymentList.tsx` |
| 2.5 | Add debt-specific fields to form | `frontend/src/components/AddPaymentModal.tsx` |
| 2.6 | Add savings-specific fields to form | `frontend/src/components/AddPaymentModal.tsx` |
| 2.7 | Create debt progress display | `frontend/src/components/DebtProgress.tsx` |
| 2.8 | Create savings progress display | `frontend/src/components/SavingsProgress.tsx` |
| 2.9 | Update stats panel | `frontend/src/components/StatsPanel.tsx` |
| 2.10 | Update page title and metadata | `frontend/src/app/layout.tsx` |

**Deliverables**:
- App rebranded as "Money Flow"
- Payment type selector in add form
- Conditional fields for debt/savings
- Tab filtering by payment type
- Progress indicators for debts and savings

---

### Phase 3: AI Agent & Polish

**Goal**: Update AI agent for new payment types, final polish

| Task | Description | Files |
|------|-------------|-------|
| 3.1 | Update system prompts | `src/agent/prompts.xml` |
| 3.2 | Add payment type to parser | `src/agent/parser.py` |
| 3.3 | Update executor for new types | `src/agent/executor.py` |
| 3.4 | Add debt/savings specific commands | `src/agent/executor.py` |
| 3.5 | Update RAG for new payment types | `src/services/rag_service.py` |
| 3.6 | Update insights for debts/savings | `src/services/insights_service.py` |
| 3.7 | Migrate existing data categories | One-time script |
| 3.8 | Update CLAUDE.md documentation | `CLAUDE.md` |
| 3.9 | Update all docstrings | Various files |
| 3.10 | Final testing and polish | All components |

**Deliverables**:
- AI understands "Add rent payment for £1137.50 monthly"
- AI understands "Add £500 debt to John, paying £50 monthly"
- AI understands "Add savings goal of £5000 for holiday"
- New insights: "You've paid off 60% of your credit card debt"
- Complete documentation update

---

## Milestone Tracker

### Phase 1: Data Model & Backend

| # | Milestone | Status | Notes |
|---|-----------|--------|-------|
| 1.1 | PaymentType enum added | ✅ Complete | Added to src/models/subscription.py |
| 1.2 | Model fields added | ✅ Complete | debt/savings fields added |
| 1.3 | Migration created & tested | ✅ Complete | d8b9e4f5a123 (uses UPPERCASE enum values) |
| 1.4 | Schemas updated | ✅ Complete | src/schemas/subscription.py |
| 1.5 | Service layer updated | ✅ Complete | payment_type filter added |
| 1.6 | API filter added | ✅ Complete | All endpoints updated |
| 1.7 | Import/export updated | ✅ Complete | v2.0 format with Money Flow fields |
| 1.8 | Summary endpoint updated | ✅ Complete | by_payment_type, debt/savings totals |
| 1.9 | Unit tests passing | ✅ Complete | 391 tests passing |
| 1.10 | Integration tests passing | ✅ Complete | All tests updated for v2.0 |

### Phase 2: Frontend & UI

| # | Milestone | Status | Notes |
|---|-----------|--------|-------|
| 2.1 | App renamed to "Money Flow" | ✅ Complete | Header.tsx updated |
| 2.2 | TypeScript types updated | ✅ Complete | PaymentType, labels, icons in api.ts |
| 2.3 | Payment type selector added | ✅ Complete | 8-type selector in AddSubscriptionModal |
| 2.4 | Filter tabs added | ✅ Complete | Dynamic tabs with counts in SubscriptionList |
| 2.5 | Debt fields added | ✅ Complete | total_owed, remaining_balance, creditor (conditional) |
| 2.6 | Savings fields added | ✅ Complete | target_amount, current_saved, recipient (conditional) |
| 2.7 | Debt progress component | ✅ Complete | Integrated into StatsPanel as conditional card |
| 2.8 | Savings progress component | ✅ Complete | Integrated into StatsPanel with progress % |
| 2.9 | Stats panel updated | ✅ Complete | Dynamic grid, debt/savings totals |
| 2.10 | Page metadata updated | ✅ Complete | Title & description in layout.tsx |

### Phase 3: AI Agent & Polish

| # | Milestone | Status | Notes |
|---|-----------|--------|-------|
| 3.1 | System prompts updated | ✅ Complete | src/agent/prompts/system.xml - role, payment_types, capabilities |
| 3.2 | Parser updated | ✅ Complete | src/agent/parser.py - PAYMENT_TYPE_HINTS, _detect_payment_type |
| 3.3 | Executor updated | ✅ Complete | src/agent/executor.py - all handlers Money Flow aware |
| 3.4 | New commands added | ✅ Complete | Debt/savings specific commands in command_patterns.xml |
| 3.5 | RAG updated | ⏳ Skipped | RAG not yet implemented (Phase 2 of RAG plan) |
| 3.6 | Insights updated | ⏳ Skipped | Insights not yet implemented (Phase 3 of RAG plan) |
| 3.7 | Data migration script | ✅ Complete | scripts/migrate_payment_types.py + SQL migration applied |
| 3.8 | CLAUDE.md updated | ✅ Complete | Payment types, model, commands documented |
| 3.9 | Docstrings updated | ⏳ Skipped | Existing docstrings adequate |
| 3.10 | Final testing | ✅ Complete | 391 tests passing |

---

## Migration Strategy

### Existing Data Migration

When running migration, automatically classify existing subscriptions:

```python
# Auto-classification rules
CATEGORY_TO_PAYMENT_TYPE = {
    # Subscriptions
    "Entertainment": PaymentType.subscription,
    "Productivity": PaymentType.subscription,
    "Storage": PaymentType.subscription,
    "Communication": PaymentType.subscription,
    "Business": PaymentType.subscription,
    "Hosting": PaymentType.subscription,

    # Utilities
    "Utilities": PaymentType.utility,

    # Insurance
    "Insurance": PaymentType.insurance,
    "Technology": PaymentType.subscription,  # AppleCare stays as subscription

    # Health (could be insurance or professional service)
    "Health": PaymentType.professional_service,  # Therapist, Gym

    # Financial
    "Financial": PaymentType.subscription,  # Bank fees
    "Finance": PaymentType.subscription,
}
```

### Manual Review List

After auto-migration, user should review:
- **Bupa Health Insurance** → Change to `insurance`
- **AppleCare+ items** → Change to `insurance`
- **Gym Sessions** → Keep as `professional_service`
- **Therapy Session** → Keep as `professional_service`

---

## Risk Assessment

### Risk 1: Data Loss During Migration

**Risk Level**: Low
**Mitigation**:
- Export backup before migration (already have this feature!)
- Migration adds columns only (no data deletion)
- Default values for new fields
- Rollback migration available

### Risk 2: Breaking Changes to API

**Risk Level**: Medium
**Mitigation**:
- New fields are optional
- Existing endpoints continue working
- Deprecation period for any renamed endpoints
- Version export format (1.0 → 2.0)

### Risk 3: UI Complexity

**Risk Level**: Medium
**Mitigation**:
- Payment type selector defaults to "subscription"
- Conditional fields only show when relevant
- Tab filtering keeps views focused
- Progressive disclosure of advanced features

### Risk 4: AI Agent Confusion

**Risk Level**: Low
**Mitigation**:
- Update prompts with clear examples
- Add payment type hints to RAG context
- Fallback to "subscription" if type unclear
- Allow user correction via follow-up

---

## Success Metrics

| Metric | Target |
|--------|--------|
| All existing tests passing | 100% |
| New payment type tests | 20+ tests |
| Successful data migration | 100% of existing data |
| AI correctly classifies new payments | >80% accuracy |
| No user-reported data loss | 0 incidents |

---

## Appendix: User's Complete Payment List

### To Be Added After Refactor

| Name | Type | Amount | Frequency | Currency |
|------|------|--------|-----------|----------|
| Rent | housing | 1,137.50 | monthly | GBP |
| EDF Electricity | utility | 70.00 | monthly | GBP |
| EDF Repayment | debt | 100.00 | monthly | GBP |
| Thames Water | utility | 180.00 | twice/year | GBP |
| Council Tax (Croydon) | utility | TBD | TBD | GBP |
| Credit Card (various) | debt | TBD | monthly | GBP |
| Friends/Family Debt | debt | TBD | TBD | GBP/UAH |
| Collector Payment | debt | TBD | one-time (Dec) | GBP |
| Daughter's Savings | savings | TBD | monthly | GBP |
| Personal Savings | savings | TBD | monthly | GBP |
| GF Transfer | transfer | TBD | monthly | UAH |

---

**Document Owner**: Development Team
**Review Cycle**: After each phase completion
**Next Review**: After Phase 3 completion
