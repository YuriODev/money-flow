# Money Flow - Frequently Asked Questions

> Common questions and answers about using Money Flow

---

## Table of Contents

1. [Account & Login](#account--login)
2. [Payments & Subscriptions](#payments--subscriptions)
3. [AI Assistant](#ai-assistant)
4. [Telegram Notifications](#telegram-notifications)
5. [Payment Cards](#payment-cards)
6. [Import & Export](#import--export)
7. [Currency & Calculations](#currency--calculations)
8. [Security & Privacy](#security--privacy)
9. [Technical Issues](#technical-issues)

---

## Account & Login

### How do I create an account?

Click "Register" on the login page and fill in your name, email, and password. Passwords must include uppercase, lowercase, number, and special character.

### I forgot my password. How do I reset it?

Click "Forgot Password" on the login page, enter your email, and follow the instructions sent to your inbox.

### Why am I getting logged out?

Sessions expire after 7 days of inactivity. If you're being logged out sooner:
- Check if you're clearing browser cookies
- Ensure your device clock is accurate
- Try a different browser

### Can I change my email address?

Currently, email addresses cannot be changed after registration. Contact support if you need to migrate to a new email.

### How do I delete my account?

Go to Settings → Profile → Delete Account. This will permanently delete all your data including payments, cards, and settings.

---

## Payments & Subscriptions

### What types of payments can I track?

Money Flow supports 8 payment types:
- **Subscriptions** (Netflix, Spotify, etc.)
- **Housing** (Rent, Mortgage)
- **Utilities** (Electric, Water, Internet)
- **Insurance** (Health, Vehicle, Device)
- **Professional Services** (Therapist, Coach)
- **Debt** (Credit Cards, Loans)
- **Savings** (Regular transfers, Goals)
- **Transfers** (Family support, Gifts)

### How do I add a payment?

Two ways:
1. **AI Chat**: Type "Add Netflix £15.99 monthly"
2. **Manual**: Click "Add Payment" and fill the form

### Can I track one-time payments?

Money Flow is designed for recurring payments. For one-time expenses, consider using the "yearly" frequency with the payment date set to when it occurred.

### What payment frequencies are supported?

- Weekly
- Bi-weekly (every 2 weeks)
- Monthly
- Quarterly (every 3 months)
- Semi-annually (every 6 months)
- Yearly

### How do I pause a subscription without deleting it?

Edit the payment and toggle "Active" to off. The payment will be saved but won't appear in totals or reminders.

### Why isn't my payment showing in "Due This Week"?

Check:
- The payment is marked as "Active"
- The "Next Payment Date" is set correctly
- The date falls within the next 7 days

### How do I track debt payments with a balance?

When adding a debt payment via AI:
```
"Add credit card debt £200 monthly, total owed £5000"
```

Or use the form and fill in "Total Owed" and "Remaining Balance" fields.

### How do I track savings goals?

Via AI:
```
"Add emergency fund £300 monthly, target £10000"
```

The system will track your progress toward the goal.

---

## AI Assistant

### What commands does the AI understand?

The AI understands natural language. Common commands:
- **Add**: "Add Netflix £15.99 monthly"
- **List**: "Show all my subscriptions"
- **Update**: "Change Netflix to £18.99"
- **Delete**: "Remove Amazon Prime"
- **Summary**: "What's my monthly total?"
- **Search**: "Find payments over £50"

### The AI misunderstood my request. What should I do?

Try being more specific:
- Instead of "Add Netflix" → "Add Netflix subscription £15.99 monthly"
- Instead of "Change it" → "Change Netflix to £18.99"

### Can the AI handle multiple currencies?

Yes! Specify the currency:
- "Add Spotify $9.99 monthly"
- "Add rent €800 monthly"

Supported: GBP (£), USD ($), EUR (€), UAH (₴)

### Does the AI remember previous conversations?

Yes, within a session. It can understand context:
```
You: "Add Netflix £15.99"
You: "Actually make it £18.99"  ← AI knows you mean Netflix
```

### Why did the AI create the wrong payment type?

The AI auto-detects payment types based on keywords. You can specify:
```
"Add Audible as a subscription, £7.99 monthly"
```

Or edit the payment afterward to change the type.

---

## Telegram Notifications

### How do I connect Telegram?

1. Go to Settings → Notifications
2. Click "Connect Telegram"
3. Note the verification code
4. Open Telegram and find the Money Flow bot
5. Send the verification code

### The bot isn't responding to my code

- Ensure you're sending just the code (6 characters, e.g., "A3F2B1")
- Codes expire after 10 minutes - generate a new one
- Make sure you started a chat with the correct bot

### How do I change my reminder time?

Go to Settings → Notifications and adjust "Reminder Time".

### Can I get reminders by email instead?

Email notifications are planned for a future release. Currently only Telegram is supported.

### How do I stop notifications?

Either:
- Go to Settings → Notifications → Toggle "Reminder Enabled" off
- Or click "Disconnect Telegram" to unlink completely

### What does "Days Before" mean?

This sets how many days before a payment is due you'll receive a reminder. Default is 3 days.

### Why didn't I get a reminder?

Check:
- Telegram is connected (Settings → Notifications → Status)
- Reminders are enabled
- The payment is marked as Active
- "Days Before" is set appropriately
- Check Telegram for blocked messages

---

## Payment Cards

### What are payment cards used for?

Payment cards help you:
- Organize payments by payment method
- Track spending per card
- Filter payments by card
- See card-specific totals

### Do I need to add real card numbers?

No! Only add:
- A nickname (e.g., "Barclays Debit")
- Last 4 digits (optional, for identification)
- Card type (Debit, Credit, etc.)

We never store full card numbers.

### How do I assign a payment to a card?

Via AI:
```
"Add Netflix £15.99 to Barclays card"
```

Or edit the payment and select a card from the dropdown.

### Can a payment be on multiple cards?

No, each payment can only be assigned to one card. If a subscription switches cards, update the payment to reflect the new card.

---

## Import & Export

### What formats can I export to?

- **JSON**: Full data backup (recommended for restoring)
- **CSV**: Spreadsheet-compatible for analysis

### What's included in an export?

- All payment details
- Card assignments
- Payment types and categories
- Next payment dates

### How do I import from another app?

Currently, we support importing from:
- Money Flow JSON exports
- Money Flow CSV exports

For other apps, you may need to manually format your data to match our CSV structure.

### Will importing duplicate my payments?

The import process shows a preview. If payments already exist with the same name, you'll be warned about potential duplicates.

### How often should I backup?

We recommend exporting weekly or after making significant changes. JSON exports contain all data needed for full restoration.

---

## Currency & Calculations

### What's the default currency?

GBP (British Pounds). You can add payments in any supported currency.

### What currencies are supported?

- GBP (£) - British Pounds
- USD ($) - US Dollars
- EUR (€) - Euros
- UAH (₴) - Ukrainian Hryvnia

### How are totals calculated for mixed currencies?

Payments are converted to your display currency using current exchange rates. The conversion is for display purposes only - the original amount is preserved.

### Why does my monthly total seem wrong?

Check:
- All relevant payments are marked "Active"
- Frequencies are set correctly
- Look for quarterly/yearly payments that may inflate totals

### How is "Yearly Total" calculated?

Yearly total = Sum of (each payment × 12/frequency)
- Monthly payments × 12
- Weekly payments × 52
- Quarterly payments × 4
- etc.

---

## Security & Privacy

### Is my data secure?

Yes:
- Passwords are hashed using bcrypt
- API uses JWT tokens with short expiry
- All connections use HTTPS
- No full card numbers are ever stored

### Who can see my payments?

Only you. All data is private to your account. We don't share or sell user data.

### Is the AI chat private?

Yes. Conversations are used only to process your commands. We don't use your financial data to train AI models.

### What happens if I delete my account?

All your data is permanently deleted:
- Payments
- Cards
- Settings
- Conversation history
- Notification preferences

### How are API tokens handled?

- Access tokens expire after 15 minutes
- Refresh tokens expire after 7 days
- Tokens are blacklisted on logout
- Invalid tokens are automatically rejected

---

## Technical Issues

### The app is slow. What can I do?

- Clear your browser cache
- Try a different browser
- Check your internet connection
- Disable browser extensions that might interfere

### I'm seeing an error message

Common errors:
- **401 Unauthorized**: Session expired, log in again
- **429 Too Many Requests**: Rate limited, wait a minute
- **500 Internal Error**: Server issue, try again later

### The AI isn't responding

- Check your internet connection
- Refresh the page
- Try a simpler command
- The AI service may be temporarily unavailable

### Payments aren't syncing

All changes should be instant. If you notice delays:
- Refresh the page
- Check browser console for errors
- Try logging out and back in

### How do I report a bug?

Visit our GitHub issues page or contact support with:
- What you were doing
- What you expected
- What actually happened
- Browser and device info

---

## Still Have Questions?

- **User Guide**: [USER_GUIDE.md](USER_GUIDE.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **API Docs**: [api/README.md](api/README.md)

---

*Last Updated: December 2025*
*Version: 1.0.0*
