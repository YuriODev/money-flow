# Money Flow Claude Skills

> **Custom Claude Skills for Financial Management**

This directory contains specialized Claude Skills that enhance Money Flow's AI capabilities with domain-specific knowledge for financial management.

## Available Skills

| Skill | Version | Description |
|-------|---------|-------------|
| [Financial Analysis](./financial-analysis/SKILL.md) | 1.0.0 | Spending analysis, budget comparison, trend detection, anomaly alerts |
| [Payment Reminder](./payment-reminder/SKILL.md) | 1.0.0 | Smart reminders with urgency classification, multi-channel support |
| [Debt Management](./debt-management/SKILL.md) | 1.0.0 | Debt payoff strategies (avalanche/snowball), interest calculations |
| [Savings Goal](./savings-goal/SKILL.md) | 1.0.0 | Goal tracking, contribution recommendations, milestone celebrations |

## Directory Structure

```
.claude/skills/
├── README.md                       # This file
├── financial-analysis/
│   ├── SKILL.md                   # Skill definition and patterns
│   └── examples/
│       └── analysis_examples.json # Example inputs/outputs
├── payment-reminder/
│   ├── SKILL.md                   # Skill definition and patterns
│   └── templates/
│       └── notification_templates.json  # Notification formats
├── debt-management/
│   ├── SKILL.md                   # Skill definition and patterns
│   └── calculators/
│       ├── __init__.py
│       └── interest_calculator.py # Payoff calculations
└── savings-goal/
    ├── SKILL.md                   # Skill definition and patterns
    └── projections/
        ├── __init__.py
        └── savings_calculator.py  # Projection calculations
```

## How Skills Work

### Skill Structure

Each skill follows a standard structure:

1. **SKILL.md** - The main skill definition containing:
   - Metadata (name, version, requirements)
   - Capabilities description
   - XML patterns for AI understanding
   - Response templates
   - Example conversations
   - Configuration options
   - Error handling

2. **Supporting Files** - Additional resources:
   - Examples (JSON files with sample inputs/outputs)
   - Templates (notification, email, message templates)
   - Calculators (Python modules for complex calculations)

### Skill Patterns

Skills use XML patterns to structure AI interactions:

```xml
<analysis_request>
  <type>monthly_summary</type>
  <period>{month}/{year}</period>
</analysis_request>
```

This helps Claude understand the expected format and produce consistent responses.

### Integration with Agent

Skills are used by the Money Flow agent (`src/agent/`) to:

1. Parse natural language commands
2. Apply domain-specific logic
3. Format responses consistently
4. Handle edge cases gracefully

## Using Skills

### In Agent Prompts

Skills can be referenced in the agent's system prompts:

```python
from pathlib import Path

skill_path = Path(".claude/skills/financial-analysis/SKILL.md")
skill_content = skill_path.read_text()

system_prompt = f"""
You are a financial assistant with the following skill:

{skill_content}

Use this skill to analyze user spending patterns.
"""
```

### In Python Code

Calculator modules can be imported directly:

```python
from .claude.skills.debt_management.calculators import (
    Debt,
    PayoffStrategy,
    calculate_payoff,
    compare_strategies,
)

# Create debts
debts = [
    Debt("1", "Credit Card", Decimal("3500"), Decimal("22.9"), Decimal("87")),
    Debt("2", "Personal Loan", Decimal("5000"), Decimal("7.9"), Decimal("150")),
]

# Calculate payoff plan
result = calculate_payoff(debts, extra_payment=Decimal("100"))
print(f"Debt-free in {result.months_to_payoff} months")
print(f"Total interest: £{result.total_interest}")

# Compare strategies
comparison = compare_strategies(debts, extra_payment=Decimal("100"))
print(f"Avalanche saves £{comparison.interest_saved} more than snowball")
```

## Skill Development Guidelines

### Creating a New Skill

1. Create a new directory under `.claude/skills/`
2. Add a `SKILL.md` file with:
   - Clear purpose statement
   - Metadata block
   - Capability descriptions
   - XML patterns for inputs/outputs
   - Response templates
   - Example conversations
   - Configuration options
   - Error handling guide

3. Add supporting files:
   - Examples in `examples/` directory
   - Python calculators in `calculators/` or similar
   - Templates in `templates/` directory

### Best Practices

1. **Clear Patterns**: Use XML patterns that are easy to parse
2. **Consistent Templates**: Response templates should be consistent across similar operations
3. **Error Handling**: Define clear error responses for edge cases
4. **Examples**: Include diverse examples covering common use cases
5. **Configuration**: Make settings configurable where appropriate
6. **Integration**: Document how the skill integrates with other skills

### Testing Skills

Skills should be tested with:

1. **Unit tests** for calculator modules
2. **Integration tests** for agent interactions
3. **Example validation** to ensure examples match patterns

## Skill Composition

Skills can work together:

- **Financial Analysis** provides budget context for **Payment Reminder** urgency
- **Debt Management** integrates with **Savings Goal** for balanced planning
- **Payment Reminder** uses data from all skills to prioritize notifications

## Contributing

To add or improve skills:

1. Follow the existing skill structure
2. Document all patterns and templates
3. Add comprehensive examples
4. Include error handling
5. Write tests for calculators
6. Update this README

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-16 | Initial release with 4 skills |
