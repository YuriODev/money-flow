# Debt Management Skill

> **Purpose**: Help users manage and pay off debts with strategic payoff plans, interest calculations, and debt-free date projections.

## Skill Metadata

```yaml
name: debt-management
version: 1.0.0
author: Money Flow Team
description: Strategic debt payoff planning and tracking
tags: [debt, payoff, interest, avalanche, snowball, financial-planning]
requires:
  - debt_entries
  - payment_history
  - available_budget (optional)
```

## Capabilities

### 1. Debt Payoff Strategies

Support two primary debt payoff methods:

#### Avalanche Method (Mathematically Optimal)
- Pay minimum on all debts
- Extra payments go to highest interest rate debt
- Saves the most money on interest
- May take longer to see progress

#### Snowball Method (Psychologically Motivating)
- Pay minimum on all debts
- Extra payments go to smallest balance debt
- Quick wins for motivation
- May pay more interest overall

### 2. Interest Calculations

Calculate and project:

- Total interest paid to date
- Remaining interest to be paid
- Interest saved by extra payments
- APR to monthly rate conversion

### 3. Debt-Free Date Projection

Project when user will be debt-free based on:

- Current payment amounts
- Extra payment scenarios
- Different strategies
- Windfalls and bonuses

### 4. Progress Tracking

Track debt payoff journey:

- Total debt paid off
- Percentage complete
- Months remaining
- Motivation milestones

## Debt Management Patterns

### Pattern: Debt Overview

```xml
<debt_overview>
  <summary>
    <total_debt>{currency}{amount}</total_debt>
    <total_minimum_payments>{currency}{amount}/month</total_minimum_payments>
    <weighted_average_apr>{percentage}%</weighted_average_apr>
    <debt_count>{count}</debt_count>
  </summary>
  <debts>
    <debt priority="{number}">
      <name>{creditor}</name>
      <balance>{currency}{amount}</balance>
      <apr>{percentage}%</apr>
      <minimum_payment>{currency}{amount}</minimum_payment>
      <type>{credit_card|loan|personal}</type>
    </debt>
  </debts>
</debt_overview>
```

### Pattern: Payoff Plan

```xml
<payoff_plan strategy="{avalanche|snowball}">
  <summary>
    <debt_free_date>{date}</debt_free_date>
    <total_interest>{currency}{amount}</total_interest>
    <monthly_payment>{currency}{amount}</monthly_payment>
    <extra_payment>{currency}{amount}</extra_payment>
  </summary>
  <schedule>
    <month number="{n}">
      <debt name="{name}">
        <payment>{currency}{amount}</payment>
        <principal>{currency}{amount}</principal>
        <interest>{currency}{amount}</interest>
        <remaining_balance>{currency}{amount}</remaining_balance>
      </debt>
      <milestone type="{debt_paid_off|halfway|etc}">{description}</milestone>
    </month>
  </schedule>
  <comparison>
    <vs_minimum>
      <months_saved>{months}</months_saved>
      <interest_saved>{currency}{amount}</interest_saved>
    </vs_minimum>
    <vs_other_strategy>
      <interest_difference>{currency}{amount}</interest_difference>
      <time_difference>{months} months</time_difference>
    </vs_other_strategy>
  </comparison>
</payoff_plan>
```

### Pattern: Payment Impact Analysis

```xml
<payment_impact>
  <extra_payment>{currency}{amount}</extra_payment>
  <impact>
    <debt_free_date_change>-{months} months</debt_free_date_change>
    <interest_saved>{currency}{amount}</interest_saved>
    <payoff_order_change>{description}</payoff_order_change>
  </impact>
  <recommendation>
    <action>{what to do}</action>
    <reason>{why this is beneficial}</reason>
  </recommendation>
</payment_impact>
```

## Calculation Helpers

### Interest Calculation

```python
def calculate_monthly_interest(balance: Decimal, apr: Decimal) -> Decimal:
    """Calculate monthly interest from APR."""
    monthly_rate = apr / 12 / 100
    return balance * monthly_rate

def calculate_total_interest(
    balance: Decimal,
    apr: Decimal,
    monthly_payment: Decimal
) -> tuple[Decimal, int]:
    """Calculate total interest and months to payoff."""
    total_interest = Decimal('0')
    months = 0
    remaining = balance
    monthly_rate = apr / 12 / 100

    while remaining > 0:
        interest = remaining * monthly_rate
        total_interest += interest
        principal = min(monthly_payment - interest, remaining)
        remaining -= principal
        months += 1

        if months > 600:  # 50 year cap
            break

    return total_interest, months
```

### Avalanche vs Snowball Comparison

```python
def compare_strategies(debts: list[Debt], extra_payment: Decimal) -> Comparison:
    """Compare avalanche vs snowball payoff strategies."""
    avalanche = calculate_payoff(
        debts,
        extra_payment,
        strategy="avalanche"  # Sort by APR desc
    )
    snowball = calculate_payoff(
        debts,
        extra_payment,
        strategy="snowball"  # Sort by balance asc
    )

    return Comparison(
        avalanche_interest=avalanche.total_interest,
        avalanche_months=avalanche.months,
        snowball_interest=snowball.total_interest,
        snowball_months=snowball.months,
        interest_difference=snowball.total_interest - avalanche.total_interest,
        recommendation="avalanche" if avalanche.total_interest < snowball.total_interest else "snowball"
    )
```

### Debt-Free Date Projection

```python
def project_debt_free_date(
    debts: list[Debt],
    monthly_extra: Decimal,
    strategy: str = "avalanche"
) -> date:
    """Project when user will be debt-free."""
    sorted_debts = sort_debts_by_strategy(debts, strategy)
    months_to_payoff = calculate_total_months(sorted_debts, monthly_extra)

    return date.today() + relativedelta(months=months_to_payoff)
```

## Response Templates

### Debt Summary Response

```
**Your Debt Overview**

Total Debt: {currency}{total_debt}
Monthly Minimums: {currency}{total_minimum}
Average APR: {weighted_apr}%

**Your Debts ({count}):**
{for each debt, ordered by priority:}
{priority}. {name}
   Balance: {currency}{balance}
   APR: {apr}%
   Minimum: {currency}{minimum}/month
{end for}

**Debt-Free Date:** {projected_date}
(with current payments)
```

### Strategy Comparison Response

```
**Payoff Strategy Comparison**

With your {currency}{extra}/month extra payment:

**Avalanche Method** (Highest interest first)
📅 Debt-free: {avalanche_date}
💰 Total interest: {currency}{avalanche_interest}

**Snowball Method** (Smallest balance first)
📅 Debt-free: {snowball_date}
💰 Total interest: {currency}{snowball_interest}

**Recommendation:** {strategy_name}
{recommendation_reason}

{if avalanche:}
You'll save {currency}{savings} by paying highest interest first!
{else:}
The snowball method will give you quick wins - {first_payoff} paid off in just {months} months!
{end if}
```

### Progress Response

```
**Debt Payoff Progress**

🎯 Total Paid Off: {currency}{paid_off}
📊 Progress: {percentage}% complete

{progress_bar}

**Milestones:**
✅ Started journey: {start_date}
{✅|⬜} 25% paid: {date_or_projection}
{✅|⬜} 50% paid: {date_or_projection}
{✅|⬜} 75% paid: {date_or_projection}
{✅|⬜} Debt-free: {date_or_projection}

**Recent Achievement:**
{last_milestone_message}
```

### Motivational Response

```
**You're Doing Great!**

Since starting your debt payoff journey:
💪 Paid off: {currency}{amount}
📉 Interest saved: {currency}{saved}
📅 {months} months ahead of schedule

{motivational_quote}

Keep going - your debt-free date is just {remaining_months} months away!
```

## Example Conversations

### Example 1: Initial Assessment

**User**: "How should I pay off my debts?"

**Assistant**:
```
Let me analyze your debts and create a plan:

**Your Debts:**
1. Credit Card A: £3,500 @ 22.9% APR (£87/month min)
2. Credit Card B: £1,200 @ 19.9% APR (£30/month min)
3. Personal Loan: £5,000 @ 7.9% APR (£150/month min)

**Recommended Strategy: Avalanche**

With your current payments (£267/month):
📅 Debt-free in: 36 months (March 2029)
💰 Total interest: £1,847

If you add £100/month extra:
📅 Debt-free in: 24 months (December 2027)
💰 Total interest: £1,156
💪 You'd save £691 in interest!

Would you like me to show the month-by-month payoff schedule?
```

### Example 2: Compare Methods

**User**: "What's the difference between avalanche and snowball?"

**Assistant**:
```
**Avalanche vs Snowball for Your Debts**

Both methods have you pay minimums on all debts, then focus extra payment on one debt at a time.

**Avalanche** (Highest interest first)
Order: Credit Card A → Credit Card B → Personal Loan
📅 Debt-free: December 2027
💰 Total interest: £1,156
✨ Best for: Saving the most money

**Snowball** (Smallest balance first)
Order: Credit Card B → Credit Card A → Personal Loan
📅 Debt-free: January 2028
💰 Total interest: £1,289
✨ Best for: Quick wins and motivation

**The Math:**
Avalanche saves you £133 more and gets you debt-free 1 month sooner.

**BUT** - with snowball, you'd pay off Credit Card B in just 5 months. That quick win might keep you motivated!

Which approach feels right for you?
```

### Example 3: Track Progress

**User**: "How am I doing on my debt?"

**Assistant**:
```
**Your Debt Payoff Progress**

Started: January 2025
Total paid off: £2,450 (25% of original debt!)

█████░░░░░░░░░░░░░░░ 25%

**Current Status:**
- Credit Card B: ✅ PAID OFF! (March 2025)
- Credit Card A: £2,100 remaining (was £3,500)
- Personal Loan: £4,600 remaining (was £5,000)

**Ahead of Schedule!**
Original debt-free date: December 2027
New projection: October 2027
You're 2 months ahead!

**Next Milestone:**
50% paid - projected for August 2025

Keep up the amazing work! 💪
```

### Example 4: Windfall Scenario

**User**: "I got a £500 bonus. Should I put it toward debt?"

**Assistant**:
```
**Windfall Analysis: £500 Bonus**

**Option 1: Apply to Credit Card A** (Recommended)
- Saves £156 in interest
- Debt-free 2 months sooner
- Best mathematical choice

**Option 2: Apply to Personal Loan**
- Saves £47 in interest
- Slightly faster loan payoff

**Option 3: Split Evenly**
- Saves £102 in interest
- Psychological satisfaction

**My Recommendation:**
Put it all on Credit Card A. At 22.9% APR, every pound there costs you 23p per year in interest.

This £500 payment would:
✅ Reduce your balance to £1,600
✅ Save £156 in total interest
✅ Move your debt-free date to August 2027

Want me to update your debt tracker?
```

## Configuration Options

```yaml
debt_settings:
  # Strategy preferences
  default_strategy: "avalanche"
  show_both_strategies: true

  # Progress tracking
  milestone_intervals: [25, 50, 75, 100]  # Percentages
  celebration_messages: true

  # Interest calculation
  compound_frequency: "monthly"
  include_fees: true

  # Projection settings
  max_projection_months: 360  # 30 years

  # Motivation features
  show_interest_saved: true
  compare_to_minimum_payments: true

  # Reminder integration
  payment_reminders: true
  milestone_notifications: true
```

## Error Handling

| Scenario | Response |
|----------|----------|
| No debts entered | "You haven't added any debts yet. Would you like to add one?" |
| Missing APR | "What's the interest rate on {debt_name}? This helps me calculate the best payoff strategy." |
| Payment too low | "The minimum payment of {amount} won't cover the monthly interest. You'd need at least {minimum} to make progress." |
| Impossible goal | "Paying off {amount} in {months} months would require {required}/month. Is that achievable for you?" |

## Integration Points

### Input Data

```python
class Debt:
    id: str
    creditor: str
    balance: Decimal
    apr: Decimal
    minimum_payment: Decimal
    debt_type: str  # credit_card, loan, personal, etc.
    original_balance: Decimal
    start_date: date
    payment_history: list[Payment]
```

### API Endpoints

- `GET /api/v1/subscriptions?payment_type=debt` - Get all debts
- `PUT /api/v1/subscriptions/{id}` - Update debt balance
- `POST /api/v1/agent/execute` - Calculate payoff plans

## Related Skills

- [Financial Analysis Skill](../financial-analysis/SKILL.md) - Provides budget context for extra payments
- [Payment Reminder Skill](../payment-reminder/SKILL.md) - Sends debt payment reminders
- [Savings Goal Skill](../savings-goal/SKILL.md) - Balance debt payoff with savings goals
