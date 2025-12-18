# Money Flow - User Guide

> **Your complete guide to managing recurring payments with AI assistance**

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Managing Payments](#managing-payments)
4. [Using the AI Assistant](#using-the-ai-assistant)
5. [Payment Cards](#payment-cards)
6. [Telegram Notifications](#telegram-notifications)
7. [Settings](#settings)
8. [Import & Export](#import--export)
9. [Keyboard Shortcuts](#keyboard-shortcuts)
10. [Tips & Best Practices](#tips--best-practices)

---

## Getting Started

### Creating Your Account

1. Navigate to the Money Flow app
2. Click **Register** on the login page
3. Enter your details:
   - Full name
   - Email address
   - Password (must include uppercase, lowercase, number, and special character)
4. Click **Create Account**
5. You'll be automatically logged in

### Logging In

1. Enter your email and password
2. Click **Sign In**
3. Your session will remain active for 7 days (with automatic token refresh)

### First Steps

After logging in, we recommend:

1. **Add your first payment** - Use the AI chat or click "Add Payment"
2. **Set up a payment card** - Organize payments by card
3. **Connect Telegram** - Get payment reminders (optional)

---

## Dashboard Overview

### Stats Panel

The top of your dashboard shows key statistics:

| Stat | Description |
|------|-------------|
| **Monthly Total** | Sum of all active monthly payments |
| **Yearly Total** | Projected annual spending |
| **Active Payments** | Number of active recurring payments |
| **Due This Week** | Payments coming up in the next 7 days |

### Payment List

Your payments are displayed in a sortable, filterable list:

- **Search**: Type to filter by name
- **Filter by Type**: Subscription, Housing, Utility, Debt, Savings, etc.
- **Filter by Status**: Active, Paused, All
- **Sort**: By name, amount, or next payment date

### Payment Calendar

The calendar view shows:

- 📅 Payment dates marked on the calendar
- 💰 Daily/weekly/monthly totals
- 🔴 Overdue payments highlighted
- 🟡 Upcoming payments (within reminder period)

---

## Managing Payments

### Adding a Payment

**Method 1: AI Assistant (Recommended)**
```
"Add Netflix for £15.99 monthly"
"Add rent £1200 monthly due on the 1st"
"Track my gym membership £29.99/month"
```

**Method 2: Manual Form**
1. Click **Add Payment** button
2. Fill in the form:
   - Name (required)
   - Amount (required)
   - Currency (GBP, USD, EUR, UAH)
   - Frequency (weekly, monthly, yearly, etc.)
   - Payment Type (subscription, housing, utility, etc.)
   - Next Payment Date
   - Payment Card (optional)
3. Click **Save**

### Payment Types

Money Flow supports 8 payment types:

| Type | Examples | Icon |
|------|----------|------|
| **Subscription** | Netflix, Spotify, Claude AI | 📦 |
| **Housing** | Rent, Mortgage | 🏠 |
| **Utility** | Electric, Water, Internet | ⚡ |
| **Insurance** | Health, Vehicle, Device | 🛡️ |
| **Professional** | Therapist, Coach, Trainer | 👔 |
| **Debt** | Credit Card, Loan | 💳 |
| **Savings** | Regular transfers, Goals | 💰 |
| **Transfer** | Family support, Gifts | 🔄 |

### Editing a Payment

1. Click on a payment in the list
2. Click the **Edit** button (pencil icon)
3. Modify any fields
4. Click **Save Changes**

### Deleting a Payment

1. Click on a payment in the list
2. Click the **Delete** button (trash icon)
3. Confirm the deletion

### Pausing a Payment

Pause a payment without deleting it:

1. Edit the payment
2. Toggle **Active** to off
3. Save changes

Paused payments won't appear in upcoming totals or reminders.

---

## Using the AI Assistant

The AI chat panel on the right side of your dashboard understands natural language commands.

### Quick Commands

| Command | Example |
|---------|---------|
| **Add** | "Add Spotify £10.99 monthly" |
| **List** | "Show all my subscriptions" |
| **Summary** | "What's my monthly total?" |
| **Update** | "Change Netflix to £18.99" |
| **Delete** | "Remove Amazon Prime" |
| **Search** | "Find all payments over £50" |

### Natural Language Examples

**Adding Payments:**
```
"Add Netflix subscription for £15.99 per month"
"Track my rent payment of £1200 monthly, due on the 1st"
"Add council tax £150/month to Barclays card"
"I pay £45 monthly for my gym membership"
```

**Querying Payments:**
```
"How much do I spend on subscriptions?"
"What payments are due this week?"
"Show me all my utility bills"
"What's my total monthly spending?"
```

**Modifying Payments:**
```
"Update Spotify to £11.99"
"Pause my gym membership"
"Change Netflix payment date to the 15th"
"Move Disney+ to my Amex card"
```

### Payment Type Detection

The AI automatically detects payment types:

- "Add rent" → Housing
- "Add electric bill" → Utility
- "Add Netflix" → Subscription
- "Add health insurance" → Insurance
- "Add credit card payment" → Debt
- "Add savings transfer" → Savings

### Conversation Context

The AI remembers your conversation context:

```
You: "Add Netflix for £15.99"
AI: "Added Netflix - £15.99/month"
You: "Actually make it £18.99"
AI: "Updated Netflix to £18.99/month"
```

---

## Payment Cards

Organize payments by linking them to payment cards.

### Adding a Card

1. Go to **Settings** → **Cards** (or use the Cards Dashboard)
2. Click **Add Card**
3. Enter:
   - Card name (e.g., "Barclays Debit")
   - Last 4 digits (optional)
   - Card type (Debit, Credit, etc.)
4. Click **Save**

### Assigning Payments to Cards

**Via AI:**
```
"Add Netflix £15.99 to Barclays card"
"Move Spotify to my Amex"
```

**Via Form:**
1. Edit the payment
2. Select a card from the dropdown
3. Save changes

### Card Dashboard

The Cards Dashboard shows:

- All your payment cards
- Total spending per card
- Number of payments per card
- Quick access to card-specific payments

---

## Telegram Notifications

Get payment reminders directly in Telegram.

### Connecting Telegram

1. Go to **Settings** → **Notifications**
2. Click **Connect Telegram**
3. A verification code will appear (e.g., `A3F2B1`)
4. Open Telegram and search for the Money Flow bot
5. Send the verification code to the bot
6. You'll see "Successfully linked!" confirmation

### Notification Settings

Configure your reminders:

| Setting | Description | Default |
|---------|-------------|---------|
| **Reminder Enabled** | Turn reminders on/off | On |
| **Days Before** | Days before payment to remind | 3 |
| **Reminder Time** | Time to send reminders | 09:00 |
| **Overdue Alerts** | Alert for missed payments | On |
| **Daily Digest** | Daily payment summary | Off |
| **Weekly Digest** | Weekly summary (choose day) | On (Monday) |

### Telegram Commands

Send these commands to the bot:

| Command | Description |
|---------|-------------|
| `/start` | Start linking process |
| `/status` | Check connection status |
| `/help` | Show available commands |

### Testing Notifications

1. Go to **Settings** → **Notifications**
2. Click **Send Test Notification**
3. Check your Telegram for the test message

### Triggering Reminders Manually

For testing purposes, you can trigger reminders:

1. Go to **Settings** → **Notifications**
2. Use the "Trigger" dropdown to select:
   - Payment Reminders
   - Daily Digest
   - Weekly Digest
   - Overdue Alerts
3. Click **Trigger**

---

## Settings

Access settings via the gear icon in the header.

### Profile Tab

- **Name**: Update your display name
- **Email**: View your email (read-only)
- **Password**: Change your password

### Notifications Tab

- **Telegram**: Connect/disconnect Telegram
- **Reminder Settings**: Configure reminder timing
- **Digest Settings**: Set up daily/weekly summaries

### Preferences (Coming Soon)

- Currency preference
- Date format
- Theme selection (light/dark)
- Default view

---

## Import & Export

### Exporting Data

1. Click the **Export** button in the header
2. Choose format:
   - **JSON**: Full data backup (recommended)
   - **CSV**: Spreadsheet-compatible format
3. File will download automatically

### Importing Data

1. Click the **Import** button in the header
2. Select your JSON or CSV file
3. Review the import preview
4. Click **Confirm Import**

### Export Format

**JSON Export** includes:
- All payment details
- Card assignments
- Payment history
- User preferences

**CSV Export** includes:
- Payment name, amount, frequency
- Next payment date
- Payment type, category
- Card name

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `N` | New payment |
| `S` | Open settings |
| `E` | Export data |
| `I` | Import data |
| `/` | Focus AI chat |
| `Esc` | Close modal |
| `?` | Show shortcuts help |

---

## Tips & Best Practices

### Organizing Payments

1. **Use payment types** - Helps with filtering and reporting
2. **Assign cards** - Track spending by payment method
3. **Set accurate dates** - Ensures correct upcoming payment alerts
4. **Use descriptive names** - "Netflix UK" vs "Netflix US"

### Staying on Top of Payments

1. **Enable Telegram reminders** - Never miss a payment
2. **Check weekly digest** - Review upcoming payments each week
3. **Review monthly summary** - Track spending trends
4. **Use the calendar view** - Visualize your payment schedule

### Managing Debt & Savings

For debt payments:
```
"Add credit card debt £500 monthly, total owed £5000"
```

For savings goals:
```
"Add emergency fund savings £200 monthly, target £10000"
```

### Using the AI Efficiently

- Be specific: "Add Netflix £15.99 monthly" vs "Add Netflix"
- Use natural dates: "due on the 1st", "every Friday"
- Batch operations: "Show all subscriptions over £10"

---

## Getting Help

- **FAQ**: See [FAQ.md](FAQ.md) for common questions
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for issues
- **API Documentation**: See [api/README.md](api/README.md) for developers

---

*Last Updated: December 2025*
*Version: 1.0.0*
