# Savings Goal Skill

> **Purpose**: Help users track savings goals, project achievement dates, recommend contributions, and celebrate milestones.

## Skill Metadata

```yaml
name: savings-goal
version: 1.0.0
author: Money Flow Team
description: Savings goal tracking and achievement projections
tags: [savings, goals, financial-planning, milestones, projections]
requires:
  - savings_entries
  - contribution_history
  - target_dates (optional)
```

## Capabilities

### 1. Goal Tracking

Track progress toward savings goals:

- Current saved amount
- Target amount
- Percentage complete
- Remaining amount
- Contribution frequency

### 2. Milestone Celebration

Celebrate achievements:

- 10%, 25%, 50%, 75%, 90% milestones
- First contribution
- Consistent saver streaks
- Goal completion
- Personal bests

### 3. Contribution Recommendations

Calculate optimal contributions:

- Based on target date
- Based on available budget
- Catch-up contributions
- Accelerated savings options

### 4. Goal Achievement Projection

Project when goals will be achieved:

- Based on current contribution rate
- With increased contributions
- Multiple scenarios comparison

## Savings Patterns

### Pattern: Goal Overview

```xml
<savings_goal>
  <name>{goal_name}</name>
  <target_amount>{currency}{amount}</target_amount>
  <current_saved>{currency}{amount}</current_saved>
  <remaining>{currency}{amount}</remaining>
  <percentage_complete>{percentage}%</percentage_complete>
  <target_date>{date|none}</target_date>
  <contribution>
    <frequency>{monthly|weekly|bi-weekly}</frequency>
    <amount>{currency}{amount}</amount>
  </contribution>
  <projected_achievement_date>{date}</projected_achievement_date>
</savings_goal>
```

### Pattern: Progress Visualization

```xml
<progress_visual>
  <progress_bar filled="{percentage}" />
  <milestones>
    <milestone percentage="25" status="{achieved|pending}" date="{date}" />
    <milestone percentage="50" status="{achieved|pending}" date="{date}" />
    <milestone percentage="75" status="{achieved|pending}" date="{date}" />
    <milestone percentage="100" status="{achieved|pending}" date="{date}" />
  </milestones>
</progress_visual>
```

### Pattern: Contribution Recommendation

```xml
<contribution_recommendation>
  <goal_name>{name}</goal_name>
  <target_date>{date}</target_date>
  <current_contribution>{currency}{amount}/{frequency}</current_contribution>
  <scenarios>
    <scenario name="current">
      <contribution>{currency}{amount}</contribution>
      <achievement_date>{date}</achievement_date>
      <on_track>{true|false}</on_track>
    </scenario>
    <scenario name="on_track">
      <contribution>{currency}{amount}</contribution>
      <achievement_date>{date}</achievement_date>
      <increase_needed>{currency}{amount}</increase_needed>
    </scenario>
    <scenario name="accelerated">
      <contribution>{currency}{amount}</contribution>
      <achievement_date>{date}</achievement_date>
      <months_saved>{months}</months_saved>
    </scenario>
  </scenarios>
  <recommendation>
    <scenario>{recommended_scenario}</scenario>
    <reason>{why_this_is_best}</reason>
  </recommendation>
</contribution_recommendation>
```

### Pattern: Milestone Celebration

```xml
<milestone_celebration>
  <milestone_type>{first_contribution|percentage|streak|goal_complete}</milestone_type>
  <achievement>{description}</achievement>
  <message>{celebration_message}</message>
  <stats>
    <total_saved>{currency}{amount}</total_saved>
    <time_saving>{months}</time_saving>
    <contributions_made>{count}</contributions_made>
  </stats>
  <next_milestone>
    <description>{next_goal}</description>
    <projected_date>{date}</projected_date>
  </next_milestone>
</milestone_celebration>
```

## Projection Calculations

### Contribution Calculator

```python
def calculate_required_contribution(
    target_amount: Decimal,
    current_saved: Decimal,
    target_date: date,
    frequency: str = "monthly"
) -> Decimal:
    """Calculate required contribution to meet target date.

    Args:
        target_amount: Goal amount.
        current_saved: Current savings.
        target_date: Target achievement date.
        frequency: Contribution frequency.

    Returns:
        Required contribution amount per period.
    """
    remaining = target_amount - current_saved
    days_until_target = (target_date - date.today()).days

    if frequency == "monthly":
        periods = days_until_target / 30.44  # Average days per month
    elif frequency == "weekly":
        periods = days_until_target / 7
    elif frequency == "bi-weekly":
        periods = days_until_target / 14
    else:
        periods = days_until_target / 30.44

    if periods <= 0:
        return remaining  # Lump sum needed

    return (remaining / Decimal(str(periods))).quantize(
        Decimal("0.01"), rounding=ROUND_UP
    )
```

### Achievement Date Projection

```python
def project_achievement_date(
    target_amount: Decimal,
    current_saved: Decimal,
    contribution: Decimal,
    frequency: str = "monthly"
) -> date:
    """Project when goal will be achieved.

    Args:
        target_amount: Goal amount.
        current_saved: Current savings.
        contribution: Contribution amount per period.
        frequency: Contribution frequency.

    Returns:
        Projected achievement date.
    """
    remaining = target_amount - current_saved
    if remaining <= 0:
        return date.today()

    if contribution <= 0:
        return None  # Will never achieve

    periods_needed = math.ceil(remaining / contribution)

    if frequency == "monthly":
        return date.today() + relativedelta(months=periods_needed)
    elif frequency == "weekly":
        return date.today() + timedelta(weeks=periods_needed)
    elif frequency == "bi-weekly":
        return date.today() + timedelta(weeks=periods_needed * 2)

    return date.today() + relativedelta(months=periods_needed)
```

## Response Templates

### Goal Status Response

```
**{goal_name}**

Target: {currency}{target_amount}
Saved: {currency}{current_saved} ({percentage}%)
Remaining: {currency}{remaining}

{progress_bar}

**Contribution:**
{currency}{contribution}/{frequency}

**Projected Achievement:**
{achievement_date} ({months_remaining} months)
{if on_track: "✅ You're on track!"}
{if behind: "⚠️ You need {currency}{extra}/month to meet your target date"}
```

### Milestone Response

```
🎉 **Milestone Achieved!**

You've reached {percentage}% of your "{goal_name}" goal!

**Your Progress:**
💰 Total Saved: {currency}{amount}
📅 Started: {start_date}
🔥 Saving Streak: {streak} months

**What This Means:**
{motivational_message}

**Next Milestone:**
{next_percentage}% - just {currency}{remaining_to_next} away!
```

### Contribution Recommendation Response

```
**Savings Recommendation for "{goal_name}"**

To reach your {currency}{target} goal by {target_date}:

**Option 1: Stay on Track**
💵 {currency}{required}/month
📅 Achieve: {target_date}
{if increase_needed: "↑ Increase by {currency}{increase}"}

**Option 2: Accelerate**
💵 {currency}{accelerated}/month
📅 Achieve: {earlier_date}
⚡ {months} months earlier!

**Option 3: Comfortable Pace**
💵 {currency}{comfortable}/month
📅 Achieve: {later_date}
🌿 More budget flexibility

**My Recommendation:** {recommended_option}
{reason_for_recommendation}
```

### Goal Completion Response

```
🎊 **GOAL COMPLETE!**

**{goal_name}** - {currency}{target_amount}

You did it! Here's your journey:

📅 Started: {start_date}
📅 Completed: {completion_date}
⏱️ Duration: {months} months
💰 Total Saved: {currency}{total_saved}
📊 Average Monthly: {currency}{average_monthly}

**Achievement Stats:**
🏆 Contributions: {contribution_count}
🔥 Longest Streak: {longest_streak} months
💪 Best Month: {currency}{best_month}

**What's Next?**
{suggestions_for_next_goal}
```

## Example Conversations

### Example 1: Check Progress

**User**: "How am I doing on my vacation fund?"

**Assistant**:
```
**Vacation Fund 2026** ✈️

Target: £3,000
Saved: £1,250 (42%)
Remaining: £1,750

████████░░░░░░░░░░░░ 42%

**Your Savings:**
£250/month automatic transfer

**Timeline:**
📅 Target: June 2026
📅 Projected: May 2026
✅ You're 1 month ahead of schedule!

**Next Milestone:**
50% (£1,500) - just £250 away! That's your next contribution!
```

### Example 2: Get Recommendation

**User**: "I want to save £5,000 for a car by December"

**Assistant**:
```
Let me calculate what you'll need:

**New Car Fund** 🚗
Target: £5,000 by December 2025
Time Available: 12 months

**Recommended Contribution:**
💵 £417/month

**Savings Schedule:**
- Starting balance: £0
- Monthly savings: £417
- Final total: £5,004

**Alternative Options:**

If £417/month is too much:
• £350/month → Achieve by February 2026
• £300/month → Achieve by April 2026

If you can save more:
• £500/month → Achieve by October 2025!

Would you like me to set up this goal?
```

### Example 3: Multiple Goals

**User**: "Show me all my savings goals"

**Assistant**:
```
**Your Savings Goals**

1. **Emergency Fund** 🏥
   ████████████████░░░░ 80%
   £4,000 / £5,000
   📅 Complete by: February 2025

2. **Vacation 2026** ✈️
   ████████░░░░░░░░░░░░ 42%
   £1,250 / £3,000
   📅 Complete by: May 2026

3. **New Laptop** 💻
   ██████░░░░░░░░░░░░░░ 30%
   £450 / £1,500
   📅 Complete by: August 2025

**Total Savings:**
£5,700 across 3 goals
£650/month combined contributions

**Priority Recommendation:**
Focus on Emergency Fund first - just £1,000 to go!
Then redirect that £200/month to accelerate other goals.
```

### Example 4: Celebrate Milestone

**User**: "I just made another deposit to my emergency fund"

**Assistant**:
```
🎉 **Congratulations!**

Your deposit of £200 to Emergency Fund has been recorded!

**New Balance:** £4,200 (84%)

████████████████░░░░ 84%

**Milestone Alert!**
You've passed 80%! Just £800 to go!

**Your Stats:**
🔥 21-month savings streak!
💰 Total contributed: £4,200
📊 Average: £200/month

**Finish Line in Sight:**
At your current pace, you'll complete this goal in just 4 months!

Keep it up - you're doing amazing! 💪
```

## Configuration Options

```yaml
savings_settings:
  # Milestone settings
  milestone_percentages: [10, 25, 50, 75, 90, 100]
  celebrate_milestones: true

  # Contribution settings
  default_frequency: "monthly"
  round_recommendations_to: 5  # Round to nearest £5

  # Projection settings
  warn_if_behind_schedule: true
  suggest_catchup_contributions: true

  # Motivation features
  show_streaks: true
  show_comparisons: true
  achievement_badges: true

  # Goal types
  goal_icons:
    emergency: "🏥"
    vacation: "✈️"
    car: "🚗"
    house: "🏠"
    education: "📚"
    wedding: "💒"
    retirement: "🌴"
    custom: "💰"
```

## Error Handling

| Scenario | Response |
|----------|----------|
| No goals set | "You haven't set any savings goals yet. What are you saving for?" |
| Target date passed | "The target date has passed. Would you like to set a new target?" |
| Zero contribution | "You haven't set a contribution amount. How much can you save each month?" |
| Goal already complete | "Great news - you've already reached this goal! Time to celebrate! 🎉" |
| Unrealistic goal | "Saving {amount} in {time} would require {contribution}/month. Is that achievable?" |

## Integration Points

### Input Data

```python
class SavingsGoal:
    id: str
    name: str
    target_amount: Decimal
    current_saved: Decimal
    contribution_amount: Decimal
    contribution_frequency: str
    target_date: date | None
    start_date: date
    category: str  # emergency, vacation, car, house, etc.
    icon: str
    contribution_history: list[Contribution]
```

### API Endpoints

- `GET /api/v1/subscriptions?payment_type=savings` - Get all savings goals
- `PUT /api/v1/subscriptions/{id}` - Update savings progress
- `POST /api/v1/agent/execute` - Calculate projections

## Related Skills

- [Financial Analysis Skill](../financial-analysis/SKILL.md) - Finds budget room for savings
- [Payment Reminder Skill](../payment-reminder/SKILL.md) - Reminds about savings contributions
- [Debt Management Skill](../debt-management/SKILL.md) - Balances debt payoff with savings
