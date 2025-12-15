# Money Flow Rate Limiting

API rate limits protect the service from abuse and ensure fair usage for all users.

## Overview

Money Flow uses Redis-backed rate limiting with different limits for different endpoint types.

## Rate Limits

| Endpoint Category | Limit | Window | Example Endpoints |
|-------------------|-------|--------|-------------------|
| **Read Operations** | 100 requests | 1 minute | GET /subscriptions, GET /summary |
| **Write Operations** | 20 requests | 1 minute | POST, PUT, DELETE /subscriptions |
| **AI Agent** | 10 requests | 1 minute | POST /agent/execute |
| **Authentication** | 5 requests | 1 minute | /auth/login, /auth/register |
| **Health Checks** | Unlimited | - | /health, /health/live |

## Rate Limit Headers

All API responses include rate limit information:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705323660
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed in window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |

## Rate Limit Exceeded

When you exceed the rate limit:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45
Content-Type: application/json

{
  "detail": "Rate limit exceeded. Try again in 45 seconds.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 45
}
```

## Best Practices

### 1. Implement Exponential Backoff

```typescript
const fetchWithRetry = async (url: string, options: RequestInit, maxRetries = 3) => {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const response = await fetch(url, options);

    if (response.status === 429) {
      const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
      const backoff = Math.min(retryAfter * 1000, Math.pow(2, attempt) * 1000);
      await new Promise(resolve => setTimeout(resolve, backoff));
      continue;
    }

    return response;
  }
  throw new Error('Max retries exceeded');
};
```

### 2. Monitor Rate Limit Headers

```typescript
const checkRateLimit = (response: Response) => {
  const remaining = parseInt(response.headers.get('X-RateLimit-Remaining') || '0');
  const limit = parseInt(response.headers.get('X-RateLimit-Limit') || '100');

  if (remaining < limit * 0.1) {
    console.warn(`Rate limit warning: ${remaining}/${limit} remaining`);
  }
};
```

### 3. Batch Requests When Possible

Instead of:
```typescript
// Bad: 10 separate requests
for (const sub of subscriptions) {
  await api.get(`/subscriptions/${sub.id}`);
}
```

Use:
```typescript
// Good: Single request
const allSubs = await api.get('/subscriptions');
```

### 4. Cache Responses

```typescript
const cache = new Map<string, { data: any; expires: number }>();

const cachedFetch = async (url: string) => {
  const cached = cache.get(url);
  if (cached && cached.expires > Date.now()) {
    return cached.data;
  }

  const response = await fetch(url);
  const data = await response.json();

  cache.set(url, {
    data,
    expires: Date.now() + 60000 // 1 minute cache
  });

  return data;
};
```

### 5. Use Webhooks for Real-Time Updates

Instead of polling, use webhooks (when available) for real-time updates.

## Rate Limit by User

Rate limits are applied per-user (by IP for unauthenticated requests):

- Authenticated: Limits tracked by user ID
- Unauthenticated: Limits tracked by IP address

## Endpoint-Specific Limits

### Authentication Endpoints

Strict limits to prevent brute force attacks:

| Endpoint | Limit | Notes |
|----------|-------|-------|
| POST /auth/login | 5/min | Per IP |
| POST /auth/register | 3/min | Per IP |
| POST /auth/forgot-password | 3/min | Per IP |
| POST /auth/refresh | 20/min | Per user |

### Subscription Endpoints

| Endpoint | Limit | Notes |
|----------|-------|-------|
| GET /subscriptions | 100/min | List all |
| GET /subscriptions/{id} | 100/min | Single item |
| POST /subscriptions | 20/min | Create |
| PUT /subscriptions/{id} | 20/min | Update |
| DELETE /subscriptions/{id} | 20/min | Delete |
| GET /subscriptions/summary | 100/min | Analytics |

### AI Agent Endpoint

```http
POST /api/v1/agent/execute
```

- **Limit**: 10 requests/minute
- **Reason**: AI inference is computationally expensive
- **Recommendation**: Cache common queries client-side

## Handling in Different Languages

### Python

```python
import time
import requests

def make_request(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)

        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            time.sleep(retry_after)
            continue

        return response

    raise Exception('Rate limit exceeded after retries')
```

### JavaScript

```javascript
async function makeRequest(url, options) {
  const response = await fetch(url, options);

  if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After') || 60;
    await new Promise(r => setTimeout(r, retryAfter * 1000));
    return makeRequest(url, options);
  }

  return response;
}
```

### Go

```go
func makeRequest(url string) (*http.Response, error) {
    for retries := 0; retries < 3; retries++ {
        resp, err := http.Get(url)
        if err != nil {
            return nil, err
        }

        if resp.StatusCode == 429 {
            retryAfter, _ := strconv.Atoi(resp.Header.Get("Retry-After"))
            time.Sleep(time.Duration(retryAfter) * time.Second)
            continue
        }

        return resp, nil
    }
    return nil, errors.New("rate limit exceeded")
}
```

## Testing Rate Limits

In development, you can test rate limiting:

```bash
# Send 6 auth requests quickly (limit is 5/min)
for i in {1..6}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8001/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"wrong"}'
done

# Output: 401 401 401 401 401 429
```

## Disabling Rate Limits (Development Only)

For local development, you can disable rate limiting:

```bash
# .env
RATE_LIMIT_ENABLED=false
```

**Warning**: Never disable rate limiting in production!

## Questions?

If you need higher rate limits for a legitimate use case, contact support with:
- Your use case description
- Expected request volume
- User ID or API key
