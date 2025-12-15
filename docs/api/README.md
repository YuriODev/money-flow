# Money Flow API Documentation

> **Version**: 1.0.0
> **Base URL**: `https://api.moneyflow.app` (production) | `http://localhost:8001` (local)

## Quick Links

- [Quickstart Guide](QUICKSTART.md) - Get started in 5 minutes
- [Authentication](AUTHENTICATION.md) - JWT tokens and auth flow
- [Rate Limiting](RATE_LIMITING.md) - API limits and best practices
- [API Changelog](CHANGELOG.md) - Version history and changes
- [Migration Guide](MIGRATION_V0_TO_V1.md) - Upgrading from legacy API

## API Overview

Money Flow provides a RESTful API for managing recurring payments, subscriptions, and financial tracking with an AI-powered natural language interface.

### Key Features

- **JWT Authentication** - Secure token-based auth with refresh tokens
- **Rate Limiting** - Redis-backed limits to ensure fair usage
- **API Versioning** - `/api/v1/` prefix with deprecation headers
- **OpenAPI/Swagger** - Interactive documentation at `/docs`
- **AI Agent** - Natural language command processing

### Base Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/v1/auth/*` | Authentication (register, login, refresh, logout) |
| `/api/v1/subscriptions/*` | Subscription CRUD operations |
| `/api/v1/agent/execute` | AI agent for natural language commands |
| `/health` | Health check endpoints |

### Response Format

All API responses follow a consistent format:

```json
{
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "ISO-8601"
  }
}
```

Error responses:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "request_id": "uuid"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Server Error |

## Getting Started

1. **Register** an account at `/api/v1/auth/register`
2. **Login** to get access token at `/api/v1/auth/login`
3. **Include token** in `Authorization: Bearer <token>` header
4. **Make requests** to protected endpoints

See [Quickstart Guide](QUICKSTART.md) for detailed examples.

## Interactive Documentation

- **Swagger UI**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **ReDoc**: [http://localhost:8001/redoc](http://localhost:8001/redoc)
- **OpenAPI Spec**: [http://localhost:8001/openapi.json](http://localhost:8001/openapi.json)

## Support

- GitHub Issues: [github.com/subscription-tracker/issues](https://github.com/subscription-tracker/issues)
- API Status: Check `/health` endpoint
