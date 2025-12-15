# Migration Guide: API v0 to v1

This guide helps you migrate from the legacy `/api/` endpoints to the new versioned `/api/v1/` endpoints.

## Timeline

- **Now**: v1 endpoints available, legacy endpoints deprecated
- **June 1, 2025**: Legacy endpoints will be removed (Sunset date)

## What's Changed

### Base URL

| Before | After |
|--------|-------|
| `/api/subscriptions` | `/api/v1/subscriptions` |
| `/api/auth/login` | `/api/v1/auth/login` |
| `/api/agent/execute` | `/api/v1/agent/execute` |

### Version Header Support (New)

You can optionally specify the API version via headers:

```http
# Option 1: X-API-Version header
X-API-Version: 1

# Option 2: Accept header with vendor MIME type
Accept: application/vnd.moneyflow.v1+json
```

### Response Headers (New)

All responses now include version information:

```http
X-API-Version: 1
X-API-Supported-Versions: 1
```

### Deprecation Warnings

Legacy endpoints return deprecation headers:

```http
Deprecation: true
Sunset: Sun, 01 Jun 2025 00:00:00 GMT
Link: </api/v1/subscriptions>; rel="successor-version"
X-API-Deprecation-Info: This endpoint is deprecated...
```

## Migration Steps

### Step 1: Update Base URL

**Before:**
```typescript
const API_BASE = '/api';
```

**After:**
```typescript
const API_BASE = '/api/v1';
```

### Step 2: Update All Endpoint Calls

**Authentication:**
```typescript
// Before
await fetch('/api/auth/login', { ... });
await fetch('/api/auth/register', { ... });

// After
await fetch('/api/v1/auth/login', { ... });
await fetch('/api/v1/auth/register', { ... });
```

**Subscriptions:**
```typescript
// Before
await fetch('/api/subscriptions');
await fetch('/api/subscriptions/summary');

// After
await fetch('/api/v1/subscriptions');
await fetch('/api/v1/subscriptions/summary');
```

**Agent:**
```typescript
// Before
await fetch('/api/agent/execute', { ... });

// After
await fetch('/api/v1/agent/execute', { ... });
```

### Step 3: Test Your Integration

1. Run your test suite against the new endpoints
2. Check for deprecation warnings in responses
3. Verify all functionality works as expected

### Step 4: Deploy Changes

Deploy your updated code before the sunset date.

## Code Examples

### Python

```python
# Before
import requests

BASE_URL = "http://localhost:8001/api"
response = requests.get(f"{BASE_URL}/subscriptions")

# After
BASE_URL = "http://localhost:8001/api/v1"
response = requests.get(f"{BASE_URL}/subscriptions")
```

### JavaScript/TypeScript

```typescript
// Before
const api = axios.create({
  baseURL: 'http://localhost:8001/api',
});

// After
const api = axios.create({
  baseURL: 'http://localhost:8001/api/v1',
});
```

### cURL

```bash
# Before
curl http://localhost:8001/api/subscriptions

# After
curl http://localhost:8001/api/v1/subscriptions
```

## What Hasn't Changed

The following remain the same between v0 and v1:

- **Request/Response formats**: All payloads are identical
- **Authentication**: JWT tokens work the same way
- **Query parameters**: All filters and pagination unchanged
- **Error codes**: Same HTTP status codes and error formats
- **Rate limits**: Same limits apply

## Endpoint Mapping

Complete mapping of old to new endpoints:

### Authentication

| Old Path | New Path |
|----------|----------|
| POST /api/auth/register | POST /api/v1/auth/register |
| POST /api/auth/login | POST /api/v1/auth/login |
| POST /api/auth/logout | POST /api/v1/auth/logout |
| POST /api/auth/refresh | POST /api/v1/auth/refresh |
| GET /api/auth/me | GET /api/v1/auth/me |
| POST /api/auth/forgot-password | POST /api/v1/auth/forgot-password |
| POST /api/auth/reset-password | POST /api/v1/auth/reset-password |

### Subscriptions

| Old Path | New Path |
|----------|----------|
| GET /api/subscriptions | GET /api/v1/subscriptions |
| POST /api/subscriptions | POST /api/v1/subscriptions |
| GET /api/subscriptions/{id} | GET /api/v1/subscriptions/{id} |
| PUT /api/subscriptions/{id} | PUT /api/v1/subscriptions/{id} |
| DELETE /api/subscriptions/{id} | DELETE /api/v1/subscriptions/{id} |
| GET /api/subscriptions/summary | GET /api/v1/subscriptions/summary |
| GET /api/subscriptions/upcoming | GET /api/v1/subscriptions/upcoming |

### Agent

| Old Path | New Path |
|----------|----------|
| POST /api/agent/execute | POST /api/v1/agent/execute |

### Import/Export

| Old Path | New Path |
|----------|----------|
| GET /api/subscriptions/export/json | GET /api/v1/subscriptions/export/json |
| GET /api/subscriptions/export/csv | GET /api/v1/subscriptions/export/csv |
| POST /api/subscriptions/import/json | POST /api/v1/subscriptions/import/json |
| POST /api/subscriptions/import/csv | POST /api/v1/subscriptions/import/csv |

### Cards

| Old Path | New Path |
|----------|----------|
| GET /api/cards | GET /api/v1/cards |
| POST /api/cards | POST /api/v1/cards |
| GET /api/cards/{id} | GET /api/v1/cards/{id} |
| PUT /api/cards/{id} | PUT /api/v1/cards/{id} |
| DELETE /api/cards/{id} | DELETE /api/v1/cards/{id} |

### Health (Unchanged)

Health endpoints are NOT versioned:

| Path | Status |
|------|--------|
| /health | Unchanged |
| /health/live | Unchanged |
| /health/ready | Unchanged |

## Handling the Transition Period

During the transition, both endpoints work:

```typescript
// Recommended: Use v1 immediately
const response = await fetch('/api/v1/subscriptions');

// Still works but deprecated (returns warnings)
const legacyResponse = await fetch('/api/subscriptions');
// Check for deprecation header
if (legacyResponse.headers.get('Deprecation') === 'true') {
  console.warn('Using deprecated endpoint');
}
```

## Checking Your Migration Status

Run this script to check if you're using deprecated endpoints:

```bash
# Check your codebase for old endpoints
grep -r "'/api/" --include="*.ts" --include="*.tsx" --include="*.js" | \
  grep -v "'/api/v1" | \
  grep -v "node_modules"
```

## FAQ

### Q: Can I use both v0 and v1 during migration?

Yes, both work during the transition period. Legacy endpoints return deprecation headers.

### Q: Will my authentication tokens still work?

Yes, JWT tokens are version-agnostic.

### Q: Are there any breaking changes?

No breaking changes. v1 is a path-only change.

### Q: What happens after the sunset date?

Legacy endpoints will return `410 Gone` status.

### Q: How do I know which version I'm using?

Check the `X-API-Version` response header.

## Support

If you encounter issues during migration:

1. Check this guide for common solutions
2. Review the [API Changelog](CHANGELOG.md)
3. Open an issue on GitHub

## Checklist

- [ ] Update API base URL to `/api/v1/`
- [ ] Update all endpoint paths in code
- [ ] Update API client configuration
- [ ] Run test suite against new endpoints
- [ ] Check for deprecation warnings in logs
- [ ] Deploy changes before sunset date
- [ ] Remove any legacy endpoint references
