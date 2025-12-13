# Payment Tracking & Calendar Enhancement Plan

**Status**: Planning Phase
**Priority**: High
**Timeline**: 2-3 Weeks (Can run parallel with RAG implementation)

---

## Overview

Enhance the subscription tracker with comprehensive payment tracking features including:
- 📅 **Calendar view** with payment dates visualization
- 💳 **Installment payments** tracking (pay-off subscriptions)
- ⏰ **Payment reminders** and notifications
- 📊 **Payment history** and patterns
- 🎨 **Beautiful modern UI** with proper images and icons

---

## Table of Contents

1. [Database Schema Changes](#database-schema-changes)
2. [Payment Tracking Features](#payment-tracking-features)
3. [Calendar View](#calendar-view)
4. [Installment Payments](#installment-payments)
5. [UI/UX Enhancements](#uiux-enhancements)
6. [Implementation Plan](#implementation-plan)

---

## Database Schema Changes

### Enhanced Subscription Model

```sql
-- Add new fields to subscriptions table
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50);  -- card, bank, paypal, etc.
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS reminder_days INTEGER DEFAULT 3;  -- Days before payment to remind
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS icon_url VARCHAR(500);  -- Subscription service icon
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS color VARCHAR(7) DEFAULT '#3B82F6';  -- Brand color
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS last_payment_date DATE;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS auto_renew BOOLEAN DEFAULT TRUE;

-- Installment payment fields
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS is_installment BOOLEAN DEFAULT FALSE;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS total_installments INTEGER;  -- Total number of payments
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS completed_installments INTEGER DEFAULT 0;  -- Payments made
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS installment_start_date DATE;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS installment_end_date DATE;

-- New table: payment_history
CREATE TABLE payment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL,
    payment_date DATE NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'GBP',
    status VARCHAR(20) DEFAULT 'completed',  -- completed, pending, failed, cancelled
    payment_method VARCHAR(50),
    installment_number INTEGER,  -- NULL for regular payments
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
    INDEX idx_payment_history_subscription (subscription_id),
    INDEX idx_payment_history_date (payment_date),
    INDEX idx_payment_history_status (status)
);

-- New table: payment_reminders
CREATE TABLE payment_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL,
    reminder_date DATE NOT NULL,
    reminder_type VARCHAR(20) DEFAULT 'upcoming',  -- upcoming, overdue, renewal
    is_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
    INDEX idx_reminders_date (reminder_date),
    INDEX idx_reminders_sent (is_sent)
);
```

### Pydantic Schemas

```python
# src/schemas/subscription.py

from decimal import Decimal
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field

class SubscriptionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="GBP", pattern="^[A-Z]{3}$")
    frequency: str
    frequency_interval: int = Field(default=1, ge=1)
    start_date: date
    category: Optional[str] = None
    notes: Optional[str] = None

    # New fields
    payment_method: Optional[str] = None
    reminder_days: int = Field(default=3, ge=0, le=30)
    icon_url: Optional[str] = None
    color: str = Field(default="#3B82F6", pattern="^#[0-9A-Fa-f]{6}$")
    auto_renew: bool = True

    # Installment fields
    is_installment: bool = False
    total_installments: Optional[int] = Field(None, ge=1)
    installment_start_date: Optional[date] = None

class SubscriptionResponse(SubscriptionBase):
    id: str
    next_payment_date: date
    last_payment_date: Optional[date]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Computed fields
    completed_installments: Optional[int] = None
    installments_remaining: Optional[int] = None
    installment_end_date: Optional[date] = None
    days_until_payment: int
    payment_status: str  # upcoming, due_soon, overdue

class PaymentHistory(BaseModel):
    id: str
    subscription_id: str
    payment_date: date
    amount: Decimal
    currency: str
    status: str
    payment_method: Optional[str]
    installment_number: Optional[int]
    notes: Optional[str]

class CalendarEvent(BaseModel):
    """Payment event for calendar view."""
    subscription_id: str
    subscription_name: str
    payment_date: date
    amount: Decimal
    currency: str
    icon_url: Optional[str]
    color: str
    is_installment: bool
    installment_info: Optional[str] = None  # "3/12"
```

---

## Payment Tracking Features

### 1. Next Payment Date Calculation

Enhanced to handle installment payments:

```python
# src/services/payment_service.py

class PaymentService:
    """
    Comprehensive payment tracking and management.

    Handles regular subscriptions, installment payments, payment history,
    and payment predictions.
    """

    async def get_next_payment_info(
        self,
        subscription_id: str
    ) -> NextPaymentInfo:
        """
        Get comprehensive next payment information.

        Returns:
            NextPaymentInfo containing:
            - next_payment_date
            - days_until_payment
            - payment_amount
            - payment_status (upcoming/due_soon/overdue)
            - installment_info (if applicable)
            - remaining_payments
            - total_cost_remaining

        Example:
            >>> service = PaymentService(db)
            >>> info = await service.get_next_payment_info("sub_123")
            >>> print(f"Next payment: {info.next_payment_date}")
            >>> print(f"Amount: £{info.payment_amount}")
            >>> print(f"Installment: {info.installment_info}")  # "3 of 12"
        """
        subscription = await self.db.get(Subscription, subscription_id)

        today = date.today()
        days_until = (subscription.next_payment_date - today).days

        # Determine status
        status = "upcoming"
        if days_until < 0:
            status = "overdue"
        elif days_until <= subscription.reminder_days:
            status = "due_soon"

        # Installment info
        installment_info = None
        if subscription.is_installment:
            remaining = subscription.total_installments - subscription.completed_installments
            installment_info = f"{subscription.completed_installments + 1} of {subscription.total_installments}"

        return NextPaymentInfo(
            next_payment_date=subscription.next_payment_date,
            days_until_payment=days_until,
            payment_amount=subscription.amount,
            payment_status=status,
            installment_info=installment_info,
            remaining_payments=subscription.total_installments - subscription.completed_installments if subscription.is_installment else None,
            total_cost_remaining=subscription.amount * remaining if subscription.is_installment else None
        )

    async def get_payment_history(
        self,
        subscription_id: str,
        limit: int = 50
    ) -> list[PaymentHistory]:
        """Get payment history for a subscription."""
        stmt = (
            select(PaymentHistory)
            .where(PaymentHistory.subscription_id == subscription_id)
            .order_by(PaymentHistory.payment_date.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def record_payment(
        self,
        subscription_id: str,
        payment_date: date,
        amount: Decimal,
        status: str = "completed",
        payment_method: Optional[str] = None
    ) -> PaymentHistory:
        """
        Record a payment for a subscription.

        For installment payments, automatically increments completed_installments
        and updates the subscription status when fully paid.
        """
        subscription = await self.db.get(Subscription, subscription_id)

        # Determine installment number
        installment_number = None
        if subscription.is_installment:
            installment_number = subscription.completed_installments + 1

        # Create payment record
        payment = PaymentHistory(
            subscription_id=subscription_id,
            payment_date=payment_date,
            amount=amount,
            status=status,
            payment_method=payment_method,
            installment_number=installment_number
        )
        self.db.add(payment)

        # Update subscription
        subscription.last_payment_date = payment_date

        if subscription.is_installment and status == "completed":
            subscription.completed_installments += 1

            # Check if fully paid
            if subscription.completed_installments >= subscription.total_installments:
                subscription.is_active = False
                subscription.notes = (subscription.notes or "") + "\n✓ Fully paid off"

        # Calculate next payment date
        subscription.next_payment_date = self._calculate_next_payment(subscription)

        await self.db.commit()
        await self.db.refresh(payment)

        return payment

    async def get_payment_pattern_analysis(
        self,
        subscription_id: str
    ) -> PaymentPatternAnalysis:
        """
        Analyze payment patterns for a subscription.

        Returns insights like:
        - Average payment amount
        - Payment consistency (on-time percentage)
        - Common payment dates
        - Cost trends over time
        """
        history = await self.get_payment_history(subscription_id, limit=100)

        # Analyze patterns
        total_payments = len(history)
        on_time_payments = sum(1 for p in history if p.status == "completed")
        avg_amount = sum(p.amount for p in history) / total_payments if total_payments > 0 else 0

        return PaymentPatternAnalysis(
            total_payments=total_payments,
            on_time_percentage=(on_time_payments / total_payments * 100) if total_payments > 0 else 0,
            average_amount=avg_amount,
            typical_payment_day=self._get_most_common_day(history),
            cost_trend="stable"  # Could be: increasing, decreasing, stable
        )
```

---

## Calendar View

### Monthly Calendar Component

```typescript
// frontend/src/components/PaymentCalendar.tsx

interface PaymentCalendarProps {
  subscriptions: Subscription[];
  selectedDate?: Date;
  onDateClick?: (date: Date, payments: CalendarEvent[]) => void;
}

export function PaymentCalendar({ subscriptions, selectedDate, onDateClick }: PaymentCalendarProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [calendarEvents, setCalendarEvents] = useState<Map<string, CalendarEvent[]>>(new Map());

  useEffect(() => {
    // Build calendar events for the month
    const events = buildCalendarEvents(subscriptions, currentMonth);
    setCalendarEvents(events);
  }, [subscriptions, currentMonth]);

  return (
    <div className="payment-calendar bg-white rounded-lg shadow-lg p-6">
      {/* Calendar Header */}
      <div className="calendar-header flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">
          {format(currentMonth, 'MMMM yyyy')}
        </h2>
        <div className="flex gap-2">
          <button
            onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
            className="px-4 py-2 rounded-lg bg-gray-100 hover:bg-gray-200"
          >
            ← Previous
          </button>
          <button
            onClick={() => setCurrentMonth(new Date())}
            className="px-4 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600"
          >
            Today
          </button>
          <button
            onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
            className="px-4 py-2 rounded-lg bg-gray-100 hover:bg-gray-200"
          >
            Next →
          </button>
        </div>
      </div>

      {/* Day Labels */}
      <div className="grid grid-cols-7 gap-2 mb-2">
        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => (
          <div key={day} className="text-center font-semibold text-gray-600 text-sm">
            {day}
          </div>
        ))}
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 gap-2">
        {getDaysInMonth(currentMonth).map((date, index) => {
          const dateKey = format(date, 'yyyy-MM-dd');
          const dayEvents = calendarEvents.get(dateKey) || [];
          const isToday = isSameDay(date, new Date());
          const hasPayments = dayEvents.length > 0;

          return (
            <CalendarDay
              key={index}
              date={date}
              events={dayEvents}
              isToday={isToday}
              hasPayments={hasPayments}
              onClick={() => onDateClick?.(date, dayEvents)}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="calendar-legend mt-6 flex flex-wrap gap-4">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-green-500"></div>
          <span className="text-sm text-gray-600">Paid</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-blue-500"></div>
          <span className="text-sm text-gray-600">Upcoming</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
          <span className="text-sm text-gray-600">Due Soon</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-red-500"></div>
          <span className="text-sm text-gray-600">Overdue</span>
        </div>
      </div>
    </div>
  );
}

interface CalendarDayProps {
  date: Date;
  events: CalendarEvent[];
  isToday: boolean;
  hasPayments: boolean;
  onClick: () => void;
}

function CalendarDay({ date, events, isToday, hasPayments, onClick }: CalendarDayProps) {
  const totalAmount = events.reduce((sum, event) => sum + Number(event.amount), 0);

  return (
    <div
      onClick={onClick}
      className={`
        calendar-day
        min-h-24 p-2 rounded-lg border-2 cursor-pointer
        transition-all duration-200 hover:shadow-md
        ${isToday ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white'}
        ${hasPayments ? 'hover:border-blue-400' : 'hover:border-gray-300'}
      `}
    >
      {/* Date number */}
      <div className={`text-sm font-semibold mb-1 ${isToday ? 'text-blue-600' : 'text-gray-700'}`}>
        {format(date, 'd')}
      </div>

      {/* Payment indicators */}
      {hasPayments && (
        <div className="space-y-1">
          {events.slice(0, 3).map((event, index) => (
            <PaymentIndicator key={index} event={event} />
          ))}
          {events.length > 3 && (
            <div className="text-xs text-gray-500">
              +{events.length - 3} more
            </div>
          )}
          <div className="text-xs font-bold text-gray-700 mt-1">
            £{totalAmount.toFixed(2)}
          </div>
        </div>
      )}
    </div>
  );
}

function PaymentIndicator({ event }: { event: CalendarEvent }) {
  const statusColor = {
    completed: 'bg-green-100 border-green-500',
    upcoming: 'bg-blue-100 border-blue-500',
    due_soon: 'bg-yellow-100 border-yellow-500',
    overdue: 'bg-red-100 border-red-500'
  };

  return (
    <div
      className={`
        text-xs px-1.5 py-0.5 rounded border-l-2 truncate
        ${statusColor[event.payment_status] || 'bg-gray-100 border-gray-500'}
      `}
      style={{ borderLeftColor: event.color }}
      title={`${event.subscription_name}: £${event.amount}`}
    >
      {event.icon_url && (
        <img src={event.icon_url} alt="" className="inline w-3 h-3 mr-1" />
      )}
      {event.subscription_name}
    </div>
  );
}
```

### Calendar API Endpoints

```python
# src/api/calendar.py

@router.get("/api/calendar/events", response_model=CalendarResponse)
async def get_calendar_events(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all payment events for a specific month.

    Returns calendar events with payment dates, amounts, and status.
    """
    start_date = date(year, month, 1)
    end_date = start_date + relativedelta(months=1)

    service = PaymentService(db)
    events = await service.get_calendar_events(start_date, end_date)

    return CalendarResponse(
        year=year,
        month=month,
        events=events,
        total_amount=sum(e.amount for e in events)
    )

@router.get("/api/calendar/summary", response_model=CalendarSummary)
async def get_calendar_summary(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db)
):
    """Get monthly payment summary for calendar view."""
    service = PaymentService(db)
    return await service.get_monthly_summary(year, month)
```

---

## Installment Payments

### Installment Tracking Component

```typescript
// frontend/src/components/InstallmentTracker.tsx

interface InstallmentTrackerProps {
  subscription: Subscription;
}

export function InstallmentTracker({ subscription }: InstallmentTrackerProps) {
  if (!subscription.is_installment) return null;

  const progress = (subscription.completed_installments / subscription.total_installments) * 100;
  const remaining = subscription.total_installments - subscription.completed_installments;
  const remainingCost = subscription.amount * remaining;

  return (
    <div className="installment-tracker bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6 border border-purple-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <CreditCard className="w-5 h-5" />
          Installment Payment Plan
        </h3>
        <span className="text-sm text-gray-600">
          {subscription.completed_installments} / {subscription.total_installments} paid
        </span>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Progress</span>
          <span className="font-semibold">{progress.toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-gradient-to-r from-purple-500 to-blue-500 h-3 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>

      {/* Payment Details Grid */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-white rounded-lg p-3 border border-purple-100">
          <div className="text-xs text-gray-500 mb-1">Next Payment</div>
          <div className="text-lg font-bold text-purple-600">
            £{subscription.amount.toFixed(2)}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            {format(subscription.next_payment_date, 'MMM dd, yyyy')}
          </div>
        </div>

        <div className="bg-white rounded-lg p-3 border border-blue-100">
          <div className="text-xs text-gray-500 mb-1">Remaining</div>
          <div className="text-lg font-bold text-blue-600">
            £{remainingCost.toFixed(2)}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            {remaining} payment{remaining !== 1 ? 's' : ''} left
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="border-t border-purple-200 pt-4">
        <div className="text-sm text-gray-600 mb-2">Payment Schedule</div>
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-700">
            {format(subscription.installment_start_date, 'MMM yyyy')} - {' '}
            {format(subscription.installment_end_date, 'MMM yyyy')}
          </span>
        </div>
      </div>

      {/* Completion Celebration */}
      {remaining === 0 && (
        <div className="mt-4 bg-green-100 border border-green-300 rounded-lg p-3 flex items-center gap-3">
          <CheckCircle className="w-6 h-6 text-green-600" />
          <div>
            <div className="font-semibold text-green-800">Fully Paid!</div>
            <div className="text-sm text-green-700">This subscription is paid off 🎉</div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## UI/UX Enhancements

### Subscription Card with Icons

```typescript
// frontend/src/components/SubscriptionCard.tsx

interface SubscriptionCardProps {
  subscription: Subscription;
  onEdit?: () => void;
  onDelete?: () => void;
}

export function SubscriptionCard({ subscription, onEdit, onDelete }: SubscriptionCardProps) {
  const daysUntilPayment = differenceInDays(
    new Date(subscription.next_payment_date),
    new Date()
  );

  const statusConfig = {
    overdue: {
      color: 'border-red-500 bg-red-50',
      badge: 'bg-red-100 text-red-800',
      icon: AlertCircle,
      label: 'Overdue'
    },
    due_soon: {
      color: 'border-yellow-500 bg-yellow-50',
      badge: 'bg-yellow-100 text-yellow-800',
      icon: Clock,
      label: 'Due Soon'
    },
    upcoming: {
      color: 'border-blue-500 bg-blue-50',
      badge: 'bg-blue-100 text-blue-800',
      icon: Calendar,
      label: 'Upcoming'
    }
  };

  const status = subscription.payment_status || 'upcoming';
  const config = statusConfig[status];

  return (
    <div className={`subscription-card rounded-lg border-2 p-4 shadow-sm hover:shadow-md transition-shadow ${config.color}`}>
      {/* Header with Icon */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {/* Service Icon/Logo */}
          {subscription.icon_url ? (
            <img
              src={subscription.icon_url}
              alt={subscription.name}
              className="w-12 h-12 rounded-lg"
            />
          ) : (
            <div
              className="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold text-lg"
              style={{ backgroundColor: subscription.color }}
            >
              {subscription.name.charAt(0).toUpperCase()}
            </div>
          )}

          {/* Name and Category */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800">
              {subscription.name}
            </h3>
            {subscription.category && (
              <span className="text-xs text-gray-500">
                {subscription.category}
              </span>
            )}
          </div>
        </div>

        {/* Status Badge */}
        <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.badge}`}>
          <config.icon className="w-3 h-3" />
          {config.label}
        </div>
      </div>

      {/* Payment Info */}
      <div className="grid grid-cols-2 gap-4 mb-3">
        <div>
          <div className="text-xs text-gray-500 mb-1">Amount</div>
          <div className="text-xl font-bold text-gray-800">
            £{subscription.amount.toFixed(2)}
          </div>
          <div className="text-xs text-gray-600">
            {subscription.frequency}
          </div>
        </div>

        <div>
          <div className="text-xs text-gray-500 mb-1">Next Payment</div>
          <div className="text-sm font-semibold text-gray-800">
            {format(subscription.next_payment_date, 'MMM dd, yyyy')}
          </div>
          <div className="text-xs text-gray-600">
            {daysUntilPayment >= 0 ? `in ${daysUntilPayment} days` : `${Math.abs(daysUntilPayment)} days ago`}
          </div>
        </div>
      </div>

      {/* Installment Info */}
      {subscription.is_installment && (
        <div className="bg-white rounded p-2 mb-3 border border-purple-200">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600">Installment</span>
            <span className="font-semibold text-purple-600">
              {subscription.completed_installments + 1} / {subscription.total_installments}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2">
            <div
              className="bg-purple-500 h-1.5 rounded-full"
              style={{ width: `${(subscription.completed_installments / subscription.total_installments) * 100}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-3 border-t border-gray-200">
        <button
          onClick={onEdit}
          className="flex-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Edit
        </button>
        <button
          onClick={onDelete}
          className="flex-1 px-3 py-2 text-sm font-medium text-red-700 bg-white border border-red-300 rounded-lg hover:bg-red-50"
        >
          Delete
        </button>
      </div>
    </div>
  );
}
```

### Service Icon Library

```typescript
// frontend/src/data/subscription-icons.ts

/**
 * Curated list of popular subscription services with icons and brand colors.
 * Icons from: https://simpleicons.org/ or custom uploads
 */
export const SUBSCRIPTION_ICONS = {
  // Streaming Services
  netflix: {
    icon: 'https://cdn.simpleicons.org/netflix',
    color: '#E50914'
  },
  spotify: {
    icon: 'https://cdn.simpleicons.org/spotify',
    color: '#1DB954'
  },
  'disney+': {
    icon: 'https://cdn.simpleicons.org/disneyplus',
    color: '#113CCF'
  },
  'prime video': {
    icon: 'https://cdn.simpleicons.org/amazonprimevideo',
    color: '#00A8E1'
  },

  // Software
  'microsoft 365': {
    icon: 'https://cdn.simpleicons.org/microsoft',
    color: '#F25022'
  },
  adobe: {
    icon: 'https://cdn.simpleicons.org/adobe',
    color: '#FF0000'
  },
  github: {
    icon: 'https://cdn.simpleicons.org/github',
    color: '#181717'
  },

  // Fitness
  'peloton': {
    icon: 'https://cdn.simpleicons.org/peloton',
    color: '#B12122'
  },

  // Add more as needed
};

export function getSubscriptionIcon(name: string): { icon: string; color: string } | null {
  const normalized = name.toLowerCase().trim();
  return SUBSCRIPTION_ICONS[normalized] || null;
}
```

---

## Implementation Plan

### Week 1: Database & Backend

- [ ] Day 1-2: Database migrations
  - Add new subscription fields
  - Create payment_history table
  - Create payment_reminders table
  - Run migrations

- [ ] Day 3-4: Payment Service
  - Implement PaymentService
  - Add payment recording
  - Add payment history retrieval
  - Add pattern analysis

- [ ] Day 5: Calendar API
  - Calendar events endpoint
  - Monthly summary endpoint
  - Payment schedule calculations

### Week 2: Frontend UI Components

- [ ] Day 1-2: Calendar Component
  - Monthly calendar view
  - Day cells with payment indicators
  - Event popups
  - Navigation (prev/next month)

- [ ] Day 3: Installment Tracker
  - Progress visualization
  - Payment schedule
  - Remaining payments display

- [ ] Day 4-5: Enhanced Subscription Cards
  - Service icons integration
  - Payment status badges
  - Improved layout
  - Responsive design

### Week 3: Polish & Integration

- [ ] Day 1-2: Icon Library
  - Curate popular service icons
  - Auto-detect and suggest icons
  - Custom icon upload support

- [ ] Day 3: Payment Reminders
  - Reminder generation service
  - Email/notification integration
  - User preferences

- [ ] Day 4-5: Testing & Refinement
  - Integration tests
  - UI/UX testing
  - Performance optimization
  - Bug fixes

---

**Document Version**: 1.0
**Last Updated**: 2025-11-28
**Status**: Ready for Implementation
**Priority**: High - Essential for user experience
