# Payment Reminder Skill

> **Purpose**: Generate intelligent payment reminders with urgency classification, personalization, and multi-channel format support.

## Skill Metadata

```yaml
name: payment-reminder
version: 1.0.0
author: Money Flow Team
description: Smart payment reminders with urgency-based prioritization
tags: [reminders, notifications, scheduling, payments]
requires:
  - upcoming_payments
  - user_preferences
  - notification_channels
```

## Capabilities

### 1. Reminder Generation

Generate contextual payment reminders:

- **Due Date Awareness**: Days until payment due
- **Amount Context**: Show payment amount and currency
- **Payment Method**: Card ending in, bank account, etc.
- **Historical Context**: "This is your 12th Netflix payment"

### 2. Urgency Classification

Classify reminders by urgency level:

| Level | Days Until Due | Color | Icon |
|-------|---------------|-------|------|
| Critical | 0-1 days | Red | ! |
| High | 2-3 days | Orange | ⚠️ |
| Medium | 4-7 days | Yellow | |
| Low | 8-14 days | Blue | |
| Scheduled | 15+ days | Gray | 📅 |

### 3. Personalization Rules

Adapt reminders based on user behavior:

- Payment history (always on time vs. sometimes late)
- Preferred reminder timing
- Amount thresholds for importance
- Category preferences (prioritize bills over subscriptions)

### 4. Multi-Channel Formats

Generate reminders for different channels:

- In-app notifications
- Email digests
- SMS alerts (critical only)
- Push notifications
- Calendar events

## Reminder Patterns

### Pattern: Single Payment Reminder

```xml
<reminder urgency="{critical|high|medium|low}">
  <payment>
    <service_name>{name}</service_name>
    <amount>{currency}{amount}</amount>
    <due_date>{date}</due_date>
    <days_until_due>{days}</days_until_due>
    <payment_method>{card_type} ending in {last_4}</payment_method>
  </payment>
  <message>
    <title>{title}</title>
    <body>{body}</body>
    <action_url>{url}</action_url>
  </message>
</reminder>
```

### Pattern: Daily Digest

```xml
<daily_digest date="{date}">
  <summary>
    <total_due_today>{count} payments ({currency}{total})</total_due_today>
    <total_due_this_week>{count} payments ({currency}{total})</total_due_this_week>
  </summary>
  <critical_payments>
    <payment service="{name}" amount="{amount}" due="{date}" />
  </critical_payments>
  <upcoming_payments>
    <payment service="{name}" amount="{amount}" due="{date}" />
  </upcoming_payments>
</daily_digest>
```

### Pattern: Weekly Summary

```xml
<weekly_summary week_of="{date}">
  <overview>
    <total_payments>{count}</total_payments>
    <total_amount>{currency}{amount}</total_amount>
  </overview>
  <calendar>
    <day date="{date}">
      <payment service="{name}" amount="{amount}" />
    </day>
  </calendar>
  <budget_impact>
    <remaining_budget>{currency}{amount}</remaining_budget>
    <projected_balance>{currency}{amount}</projected_balance>
  </budget_impact>
</weekly_summary>
```

## Response Templates

### Critical Reminder (Due Today/Tomorrow)

```
🚨 **Payment Due {today|tomorrow}!**

**{service_name}** - {currency}{amount}

Due: {due_date}
Payment Method: {card_type} ending in {last_4}

{action_button: "View Payment Details"}

💡 This payment will be automatically charged to your card.
```

### Standard Reminder (2-7 days)

```
📅 **Upcoming Payment**

**{service_name}** - {currency}{amount}
Due in {days} days ({due_date})

Payment Method: {card_type} ending in {last_4}
{if card_balance_low: "⚠️ Card balance may be low for this payment"}

{action_button: "Manage Subscription"}
```

### Weekly Digest Email

```
Subject: Your Weekly Payment Summary - {week_range}

Hi {user_name},

Here's your payment schedule for this week:

**This Week's Payments ({count})**
Total: {currency}{total}

{for each day with payments:}
📆 {day_name}, {date}
{for each payment:}
  • {service_name}: {currency}{amount}
{end for}
{end for}

**Budget Check**
{if on_track:}
✅ You're on track with your {category} budget
{else:}
⚠️ These payments will put you over your {category} budget by {currency}{amount}
{end if}

{action_button: "View Full Calendar"}

Best,
Money Flow
```

### Push Notification Formats

```json
{
  "critical": {
    "title": "Payment Due Today!",
    "body": "{service_name} - {amount} due today",
    "priority": "high",
    "sound": "default",
    "badge": 1
  },
  "high": {
    "title": "Payment Due Soon",
    "body": "{service_name} - {amount} due in {days} days",
    "priority": "high",
    "sound": "default"
  },
  "medium": {
    "title": "Upcoming Payment",
    "body": "{service_name} - {amount} due {date}",
    "priority": "normal"
  },
  "low": {
    "title": "Payment Scheduled",
    "body": "{service_name} - {amount} on {date}",
    "priority": "low"
  }
}
```

## Scheduling Logic

### Default Reminder Schedule

```python
REMINDER_SCHEDULE = {
    "critical_amount": 100,  # Currency amount threshold
    "schedules": {
        "default": [
            {"days_before": 7, "urgency": "low"},
            {"days_before": 3, "urgency": "medium"},
            {"days_before": 1, "urgency": "high"},
            {"days_before": 0, "urgency": "critical"}
        ],
        "high_amount": [  # For payments > critical_amount
            {"days_before": 14, "urgency": "low"},
            {"days_before": 7, "urgency": "medium"},
            {"days_before": 3, "urgency": "high"},
            {"days_before": 1, "urgency": "critical"},
            {"days_before": 0, "urgency": "critical"}
        ],
        "bills": [  # Housing, utilities
            {"days_before": 7, "urgency": "medium"},
            {"days_before": 3, "urgency": "high"},
            {"days_before": 1, "urgency": "critical"},
            {"days_before": 0, "urgency": "critical"}
        ]
    }
}
```

### Smart Scheduling

Adjust reminders based on:

1. **Payment History**
   - User always pays on time → Fewer reminders
   - User sometimes misses payments → More reminders

2. **Day of Week**
   - Don't send low-priority reminders on weekends
   - Send critical reminders any time

3. **Time of Day**
   - Morning (8-9 AM) for daily digests
   - Evening (6-7 PM) for next-day reminders

4. **User Timezone**
   - Respect user's local time
   - Don't send notifications during sleep hours

## Example Conversations

### Example 1: Daily Check

**User**: "What payments do I have coming up?"

**Assistant**:
```
Here are your upcoming payments:

**This Week**
🔴 Tomorrow: Netflix - £15.99
🟠 Friday: Spotify - £10.99
🟢 Sunday: iCloud - £2.99

**Next Week**
📅 Monday: Rent - £1,200.00
📅 Wednesday: Electric Bill - £85.00

Total coming up: £1,314.97

Would you like me to remind you before any specific payment?
```

### Example 2: Set Custom Reminder

**User**: "Remind me 3 days before my rent is due"

**Assistant**:
```
I've set up a reminder for your rent payment:

**Rent** - £1,200.00
📅 Due: January 1, 2026
🔔 Reminder: December 29, 2025 (3 days before)

I'll send you a notification on that day. Would you also like:
- A weekly summary of all upcoming payments?
- An extra reminder the day before?
```

### Example 3: Handle Late Payment Risk

**User**: "I might not have enough for my rent next week"

**Assistant**:
```
I understand. Let me help you plan:

**Rent Due**: January 1, 2026 - £1,200.00

**Your other payments before rent:**
- Netflix: £15.99 (Dec 27)
- Spotify: £10.99 (Dec 28)
- Total: £26.98

**Options:**
1. ⏸️ Pause Netflix/Spotify temporarily to save £26.98
2. 📅 Contact landlord about payment date
3. 💳 Check if any subscriptions can be paid after rent

Would you like me to help with any of these options?
```

## Configuration Options

```yaml
reminder_settings:
  # Notification preferences
  channels:
    in_app: true
    email: true
    push: true
    sms: false  # Only for critical

  # Timing preferences
  digest_time: "08:00"  # Daily digest time
  quiet_hours:
    start: "22:00"
    end: "07:00"

  # Urgency thresholds
  critical_threshold_days: 1
  high_threshold_days: 3
  medium_threshold_days: 7

  # Amount thresholds
  high_amount_threshold: 100

  # Personalization
  reduce_reminders_if_on_time: true
  max_reminders_per_day: 5
  group_small_payments: true
  small_payment_threshold: 10
```

## Error Handling

| Scenario | Response |
|----------|----------|
| No upcoming payments | "You don't have any payments due in the next 30 days." |
| Invalid date | "I couldn't understand that date. Try 'next Tuesday' or 'January 15'." |
| Notification delivery failed | "I couldn't send the notification. Check your notification settings." |
| Time zone unknown | "What timezone are you in? This helps me send reminders at the right time." |

## Integration Points

### Input Data

```python
class UpcomingPayment:
    id: str
    service_name: str
    amount: Decimal
    currency: str
    due_date: date
    payment_method: PaymentMethod | None
    category: str
    payment_type: str
    reminder_settings: ReminderSettings | None
```

### API Endpoints

- `GET /api/v1/subscriptions/upcoming` - Get upcoming payments
- `POST /api/v1/reminders` - Create custom reminder
- `PUT /api/v1/reminders/{id}` - Update reminder
- `GET /api/v1/reminders/schedule` - Get reminder schedule

## Related Skills

- [Financial Analysis Skill](../financial-analysis/SKILL.md) - Analyzes payment patterns for smart scheduling
- [Debt Management Skill](../debt-management/SKILL.md) - Prioritizes debt payments in reminders
- [Savings Goal Skill](../savings-goal/SKILL.md) - Reminds about savings contributions
