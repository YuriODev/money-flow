# Money Flow API Quickstart

Get started with the Money Flow API in 5 minutes.

## Prerequisites

- HTTP client (curl, Postman, or any programming language)
- Running Money Flow backend (`docker-compose up` or local dev server)

## Step 1: Register a User

```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "is_active": true,
    "is_verified": false
  }
}
```

## Step 2: Login (if already registered)

```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

## Step 3: Create a Subscription

Use the `access_token` from login/register:

```bash
curl -X POST http://localhost:8001/api/v1/subscriptions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Netflix",
    "amount": "15.99",
    "currency": "GBP",
    "frequency": "monthly",
    "start_date": "2024-01-15",
    "category": "entertainment",
    "payment_type": "subscription"
  }'
```

Response:
```json
{
  "id": "uuid",
  "name": "Netflix",
  "amount": "15.99",
  "currency": "GBP",
  "frequency": "monthly",
  "next_payment_date": "2024-02-15",
  "is_active": true,
  "category": "entertainment",
  "payment_type": "subscription"
}
```

## Step 4: List Your Subscriptions

```bash
curl http://localhost:8001/api/v1/subscriptions \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Step 5: Get Spending Summary

```bash
curl http://localhost:8001/api/v1/subscriptions/summary \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:
```json
{
  "total_monthly": "15.99",
  "total_yearly": "191.88",
  "active_count": 1,
  "by_category": {
    "entertainment": "15.99"
  },
  "by_frequency": {
    "monthly": "15.99"
  },
  "upcoming_week": []
}
```

## Step 6: Use the AI Agent

Natural language commands:

```bash
curl -X POST http://localhost:8001/api/v1/agent/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "command": "Add Spotify for £9.99 monthly"
  }'
```

Example commands:
- "Show my subscriptions"
- "Add Netflix for £15.99 monthly"
- "How much am I spending?"
- "Cancel my Spotify subscription"
- "What's due this week?"

## Payment Types

Money Flow supports 8 payment types:

| Type | Description | Example |
|------|-------------|---------|
| `subscription` | Recurring digital services | Netflix, Spotify |
| `housing` | Rent, mortgage | Monthly rent |
| `utility` | Bills, services | Electric, water |
| `professional_service` | Professional fees | Therapist, coach |
| `insurance` | Insurance premiums | Health, car |
| `debt` | Loans, credit | Credit card |
| `savings` | Savings transfers | Emergency fund |
| `transfer` | Regular transfers | Family support |

## Frequencies

Supported billing frequencies:

- `daily`
- `weekly`
- `biweekly`
- `monthly`
- `quarterly`
- `yearly`
- `one_time`

## Error Handling

Always check for errors:

```bash
# 401 Unauthorized - Token expired or invalid
{
  "detail": "Could not validate credentials"
}

# 422 Validation Error
{
  "detail": [
    {
      "loc": ["body", "amount"],
      "msg": "Amount must be positive",
      "type": "value_error"
    }
  ]
}

# 429 Rate Limited
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

## Token Refresh

Access tokens expire after 15 minutes. Use the refresh token:

```bash
curl -X POST http://localhost:8001/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

## Step 7: Enable Telegram Notifications (Optional)

Connect your Telegram account for payment reminders:

```bash
# 1. Initiate Telegram linking
curl -X POST http://localhost:8001/api/v1/notifications/telegram/link \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:
```json
{
  "verification_code": "A3F2B1",
  "bot_username": "MoneyFlowBot",
  "bot_link": "https://t.me/MoneyFlowBot",
  "expires_in_minutes": 10,
  "instructions": "..."
}
```

```bash
# 2. Send the code to @MoneyFlowBot on Telegram

# 3. Test your connection
curl -X POST http://localhost:8001/api/v1/notifications/test \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Step 8: Configure Notification Preferences

```bash
curl -X PUT http://localhost:8001/api/v1/notifications/preferences \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "reminder_enabled": true,
    "reminder_days_before": 3,
    "weekly_digest": true
  }'
```

## Next Steps

- Read [Authentication](AUTHENTICATION.md) for detailed auth flow
- Check [Rate Limiting](RATE_LIMITING.md) for API limits
- Set up [Notifications](NOTIFICATIONS.md) for payment reminders
- Explore [OpenAPI docs](http://localhost:8001/docs) for all endpoints
- Import [Postman collection](../postman/MoneyFlow.postman_collection.json)
