# Financial Analysis Skill

> **Purpose**: Analyze user spending patterns, compare against budgets, detect trends, and identify anomalies in recurring payments.

## Skill Metadata

```yaml
name: financial-analysis
version: 1.0.0
author: Money Flow Team
description: Comprehensive financial analysis for recurring payments
tags: [finance, analysis, budget, trends, anomalies]
requires:
  - payment_data
  - date_range (optional)
  - budget_limits (optional)
```

## Capabilities

### 1. Spending Analysis

Analyze spending patterns across different dimensions:

- **By Payment Type**: Subscriptions, housing, utilities, insurance, debts, savings, transfers
- **By Frequency**: Monthly, yearly, weekly, quarterly
- **By Category**: Entertainment, productivity, health, finance, etc.
- **By Time Period**: Month-over-month, year-over-year

### 2. Budget Comparison

Compare actual spending against user-defined budgets:

- Calculate budget utilization percentage
- Identify over-budget categories
- Project end-of-period spending
- Suggest budget adjustments

### 3. Trend Detection

Identify spending trends over time:

- Increasing/decreasing spending patterns
- Seasonal variations
- New subscriptions impact
- Cancelled subscriptions savings
- Price increases detection

### 4. Anomaly Detection

Flag unusual spending patterns:

- Unexpected charges
- Duplicate subscriptions
- Unusual price changes
- Missed payments
- Abnormal frequency changes

## Analysis Patterns

### Pattern: Monthly Spending Summary

```xml
<analysis_request>
  <type>monthly_summary</type>
  <period>{month}/{year}</period>
  <group_by>payment_type</group_by>
</analysis_request>

<analysis_response>
  <summary>
    <total_spending>{amount}</total_spending>
    <currency>{currency}</currency>
    <change_from_previous>{percentage}%</change_from_previous>
  </summary>
  <breakdown>
    <category name="{payment_type}">
      <amount>{amount}</amount>
      <count>{number_of_payments}</count>
      <percentage_of_total>{percentage}%</percentage_of_total>
    </category>
    <!-- repeat for each category -->
  </breakdown>
  <insights>
    <insight type="trend">{observation}</insight>
    <insight type="anomaly">{observation}</insight>
  </insights>
</analysis_response>
```

### Pattern: Budget Health Check

```xml
<budget_analysis>
  <category name="{category}">
    <budget_limit>{amount}</budget_limit>
    <actual_spending>{amount}</actual_spending>
    <utilization>{percentage}%</utilization>
    <status>{under_budget|on_track|over_budget}</status>
    <projected_end_of_month>{amount}</projected_end_of_month>
    <recommendation>{action}</recommendation>
  </category>
</budget_analysis>
```

### Pattern: Trend Analysis

```xml
<trend_analysis period="{time_range}">
  <overall_trend>{increasing|stable|decreasing}</overall_trend>
  <change_rate>{percentage}% per month</change_rate>
  <key_drivers>
    <driver impact="high">
      <description>{what changed}</description>
      <amount_impact>{+/- amount}</amount_impact>
    </driver>
  </key_drivers>
  <forecast>
    <next_month>{projected_amount}</next_month>
    <confidence>{high|medium|low}</confidence>
  </forecast>
</trend_analysis>
```

### Pattern: Anomaly Alert

```xml
<anomaly_detection>
  <anomaly severity="{critical|warning|info}">
    <type>{duplicate|price_change|unexpected|missing}</type>
    <description>{what was detected}</description>
    <affected_subscription>{name}</affected_subscription>
    <expected>{expected_value}</expected>
    <actual>{actual_value}</actual>
    <suggested_action>{recommendation}</suggested_action>
  </anomaly>
</anomaly_detection>
```

## Response Templates

### Summary Response

When summarizing financial data:

```
Here's your spending analysis for {period}:

**Total Recurring Payments: {currency}{total}**
{change_indicator} {percentage}% from last {period_type}

**Breakdown by Category:**
- Subscriptions: {currency}{amount} ({percentage}%)
- Housing: {currency}{amount} ({percentage}%)
- Utilities: {currency}{amount} ({percentage}%)
- Insurance: {currency}{amount} ({percentage}%)
- Debts: {currency}{amount} ({percentage}%)
- Savings: {currency}{amount} ({percentage}%)
- Transfers: {currency}{amount} ({percentage}%)

**Key Insights:**
1. {insight_1}
2. {insight_2}
3. {insight_3}
```

### Budget Alert Response

When budget thresholds are exceeded:

```
**Budget Alert**

Your {category} spending has reached {percentage}% of your {currency}{budget} budget.

Current spending: {currency}{actual}
Remaining budget: {currency}{remaining}
Days left in period: {days}

**Recommendation:** {specific_action}
```

### Trend Response

When reporting trends:

```
**Spending Trend Analysis ({period})**

Your recurring payments are {trending} at {rate}% per month.

**Main Changes:**
{bullet_list_of_changes}

**Projected Impact:**
If this trend continues, your monthly payments will be {currency}{projected} by {future_date}.
```

## Integration Points

### Input Data Structure

```python
class PaymentData:
    id: str
    service_name: str
    amount: Decimal
    currency: str
    billing_frequency: str  # monthly, yearly, weekly, quarterly
    payment_type: str  # subscription, housing, utility, etc.
    category: str
    next_billing_date: date
    created_at: datetime
    last_payment_date: datetime | None
    price_history: list[PriceChange]
```

### API Endpoints Used

- `GET /api/v1/subscriptions` - Fetch all payments
- `GET /api/v1/subscriptions/summary` - Get spending summary
- `GET /api/v1/subscriptions/upcoming` - Get upcoming payments
- `POST /api/v1/agent/execute` - Execute analysis commands

## Example Conversations

### Example 1: Monthly Summary

**User**: "How much am I spending on subscriptions this month?"

**Assistant**:
```
Here's your subscription spending for December 2025:

**Total Subscriptions: £127.94**
↑ 8% from November

**Your Active Subscriptions:**
- Netflix: £15.99/month
- Spotify: £10.99/month
- Claude Pro: £18.00/month
- Adobe CC: £54.99/month
- iCloud: £2.99/month
- Others (5): £24.98/month

**Insight:** Your Adobe Creative Cloud is your largest subscription at 43% of your subscription budget. Have you used all the apps included?
```

### Example 2: Budget Check

**User**: "Am I on track with my budget?"

**Assistant**:
```
**Budget Status for December 2025**

| Category      | Budget  | Spent   | Status       |
|--------------|---------|---------|--------------|
| Subscriptions | £150    | £127.94 | ✅ On Track  |
| Utilities     | £200    | £185.50 | ⚠️ Warning   |
| Housing       | £1,200  | £1,200  | ✅ On Track  |
| Insurance     | £100    | £89.00  | ✅ On Track  |

**Alert:** Your utilities spending is at 93% with 15 days remaining. Consider reviewing your energy usage.
```

### Example 3: Anomaly Detection

**User**: "Are there any unusual charges?"

**Assistant**:
```
I found 2 items that need your attention:

**⚠️ Price Increase Detected**
Netflix increased from £13.99 to £15.99 (+14%)
Last changed: December 1, 2025

**⚠️ Potential Duplicate**
You have two similar streaming services:
- Netflix: £15.99/month
- Disney+: £10.99/month

If you're not using both regularly, cancelling one would save £131.88/year.
```

## Configuration Options

```yaml
analysis_settings:
  default_currency: GBP
  trend_period_months: 6
  anomaly_detection:
    price_change_threshold: 10%  # Flag changes above this
    duplicate_similarity: 0.8    # Similarity score for duplicates
  budget_alerts:
    warning_threshold: 80%
    critical_threshold: 100%
  forecast:
    confidence_minimum: 0.7
    projection_months: 3
```

## Error Handling

| Error | Response |
|-------|----------|
| No payment data | "I don't have any payment data to analyze yet. Add some subscriptions first!" |
| Insufficient history | "I need at least 3 months of data to detect reliable trends." |
| Budget not set | "You haven't set a budget for {category}. Would you like to set one now?" |
| Date range invalid | "Please specify a valid date range (e.g., 'last 3 months' or 'January 2025')." |

## Related Skills

- [Payment Reminder Skill](../payment-reminder/SKILL.md) - Uses analysis to prioritize reminders
- [Debt Management Skill](../debt-management/SKILL.md) - Integrates debt tracking with analysis
- [Savings Goal Skill](../savings-goal/SKILL.md) - Uses trends for savings projections
