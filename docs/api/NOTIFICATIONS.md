# Money Flow Notifications API

> Complete guide to notification preferences and Telegram integration

---

## Overview

The Notifications API allows users to:
- Configure notification preferences (reminders, digests)
- Link and unlink Telegram accounts
- Send test notifications
- Manually trigger reminder tasks

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/notifications/preferences` | Get notification preferences |
| PUT | `/api/v1/notifications/preferences` | Update notification preferences |
| POST | `/api/v1/notifications/telegram/link` | Initiate Telegram linking |
| GET | `/api/v1/notifications/telegram/status` | Get Telegram connection status |
| DELETE | `/api/v1/notifications/telegram/unlink` | Unlink Telegram account |
| POST | `/api/v1/notifications/test` | Send test notification |
| POST | `/api/v1/notifications/trigger` | Manually trigger reminders |

---

## Notification Preferences

### Get Preferences

```bash
GET /api/v1/notifications/preferences
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "reminder_enabled": true,
  "reminder_days_before": 3,
  "reminder_time": "09:00:00",
  "overdue_alerts": true,
  "daily_digest": false,
  "weekly_digest": true,
  "weekly_digest_day": 0,
  "quiet_hours_enabled": false,
  "quiet_hours_start": null,
  "quiet_hours_end": null,
  "telegram": {
    "enabled": true,
    "verified": true,
    "username": "john_doe",
    "linked": true
  }
}
```

### Update Preferences

```bash
PUT /api/v1/notifications/preferences
Authorization: Bearer <token>
Content-Type: application/json

{
  "reminder_enabled": true,
  "reminder_days_before": 5,
  "reminder_time": "08:00:00",
  "overdue_alerts": true,
  "daily_digest": true,
  "weekly_digest": true,
  "weekly_digest_day": 1,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "22:00:00",
  "quiet_hours_end": "07:00:00"
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `reminder_enabled` | boolean | Enable payment reminders |
| `reminder_days_before` | integer (1-30) | Days before payment to send reminder |
| `reminder_time` | time | Time of day to send reminders (HH:MM:SS) |
| `overdue_alerts` | boolean | Send alerts for overdue payments |
| `daily_digest` | boolean | Send daily payment summary |
| `weekly_digest` | boolean | Send weekly payment summary |
| `weekly_digest_day` | integer (0-6) | Day for weekly digest (0=Monday) |
| `quiet_hours_enabled` | boolean | Enable quiet hours |
| `quiet_hours_start` | time | Start of quiet hours |
| `quiet_hours_end` | time | End of quiet hours |

---

## Telegram Integration

### Linking Flow

1. **Initiate Link** - Request a verification code
2. **Send Code to Bot** - User sends code to @MoneyFlowBot on Telegram
3. **Verification** - Bot verifies and links account
4. **Connected** - Start receiving notifications

### Initiate Telegram Link

```bash
POST /api/v1/notifications/telegram/link
Authorization: Bearer <token>
```

**Response:**
```json
{
  "verification_code": "A3F2B1",
  "bot_username": "MoneyFlowBot",
  "bot_link": "https://t.me/MoneyFlowBot",
  "expires_in_minutes": 10,
  "instructions": "1. Open Telegram and search for @MoneyFlowBot\n2. Start a conversation with the bot\n3. Send this code: A3F2B1\n4. The bot will confirm when linking is complete"
}
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 503 | `Telegram bot is not configured` | Bot token not set in environment |

### Get Telegram Status

```bash
GET /api/v1/notifications/telegram/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "enabled": true,
  "verified": true,
  "username": "john_doe",
  "linked": true
}
```

**Status Values:**

| Field | Description |
|-------|-------------|
| `enabled` | Telegram notifications turned on |
| `verified` | User has verified via bot |
| `username` | Telegram username (if provided) |
| `linked` | Full linking complete (enabled + verified + chat_id) |

### Unlink Telegram

```bash
DELETE /api/v1/notifications/telegram/unlink
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Telegram account has been unlinked successfully"
}
```

---

## Testing Notifications

### Send Test Notification

```bash
POST /api/v1/notifications/test
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Test notification sent successfully! Check your Telegram.",
  "channel": "telegram"
}
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 400 | `Telegram is not linked` | Must link Telegram first |
| 500 | `Failed to send test notification` | Telegram API error |

---

## Triggering Reminders

### Manually Trigger Reminder Tasks

Useful for testing reminder delivery without waiting for scheduled jobs.

```bash
POST /api/v1/notifications/trigger
Authorization: Bearer <token>
Content-Type: application/json

{
  "task_type": "reminders"
}
```

**Task Types:**

| Type | Description |
|------|-------------|
| `reminders` | Send payment reminders for upcoming payments |
| `daily_digest` | Send daily payment summary |
| `weekly_digest` | Send weekly payment summary |
| `overdue` | Send overdue payment alerts |

**Response (reminders):**
```json
{
  "success": true,
  "task_type": "reminders",
  "message": "Sent 3 payment reminder(s)",
  "result": {
    "subscriptions_found": 5,
    "reminders_sent": 3
  }
}
```

**Response (daily_digest):**
```json
{
  "success": true,
  "task_type": "daily_digest",
  "message": "Daily digest sent",
  "result": {
    "subscriptions_included": 7,
    "sent": true
  }
}
```

**Response (weekly_digest):**
```json
{
  "success": true,
  "task_type": "weekly_digest",
  "message": "Weekly digest sent",
  "result": {
    "subscriptions_included": 12,
    "sent": true
  }
}
```

**Response (overdue):**
```json
{
  "success": true,
  "task_type": "overdue",
  "message": "Sent 2 overdue alert(s)",
  "result": {
    "overdue_found": 2,
    "alerts_sent": 2
  }
}
```

---

## Notification Message Formats

### Payment Reminder

```
🔔 Payment Reminder

📦 Netflix
💰 £15.99
📅 Due in 3 days (December 21, 2025)

💳 Card: Visa ****1234
```

### Daily Digest

```
📊 Daily Payment Summary

Today's Payments:
• Netflix - £15.99
• Spotify - £9.99

Upcoming This Week:
• Rent - £1,200.00 (Dec 25)
• Electric - £85.00 (Dec 27)

Total this week: £1,310.98
```

### Weekly Digest

```
📅 Weekly Payment Summary

This Week (Dec 18 - Dec 24):
• Netflix - £15.99 (Dec 21)
• Gym - £29.99 (Dec 22)
• Phone - £45.00 (Dec 23)

Total: £90.98

Next Week Preview: 4 payments (£1,350.00)
```

### Overdue Alert

```
⚠️ Overdue Payment Alert

📦 Insurance Premium
💰 £125.00
📅 Was due 2 days ago (December 16)

Please update the payment status or mark as paid.
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `TELEGRAM_NOT_CONFIGURED` | 503 | Telegram bot not configured |
| `TELEGRAM_NOT_LINKED` | 400 | Telegram account not linked |
| `NOTIFICATION_FAILED` | 500 | Failed to send notification |
| `INVALID_TASK_TYPE` | 400 | Unknown task type |

---

## Best Practices

### Setting Up Notifications

1. **Link Telegram First**: Connect your Telegram account before enabling notifications
2. **Test Your Setup**: Use the test notification endpoint to verify everything works
3. **Set Appropriate Times**: Choose reminder times when you'll actually check them
4. **Use Quiet Hours**: Prevent notifications during sleep or focus time

### Recommended Settings

For most users:

```json
{
  "reminder_enabled": true,
  "reminder_days_before": 3,
  "reminder_time": "09:00:00",
  "overdue_alerts": true,
  "daily_digest": false,
  "weekly_digest": true,
  "weekly_digest_day": 0,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "22:00:00",
  "quiet_hours_end": "07:00:00"
}
```

---

## See Also

- [Quickstart Guide](QUICKSTART.md) - Get started with the API
- [Authentication](AUTHENTICATION.md) - JWT token management
- [Rate Limiting](RATE_LIMITING.md) - API limits

---

*Last Updated: December 2025*
*Version: 1.1.0*
