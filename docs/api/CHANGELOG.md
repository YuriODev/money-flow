# Money Flow API Changelog

All notable changes to the Money Flow API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this API adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-12-18

### Added

- **Notifications API**: Complete notification preferences management
  - `GET/PUT /api/v1/notifications/preferences` - User notification settings
  - `POST /api/v1/notifications/telegram/link` - Initiate Telegram linking
  - `GET /api/v1/notifications/telegram/status` - Connection status
  - `DELETE /api/v1/notifications/telegram/unlink` - Unlink account
  - `POST /api/v1/notifications/test` - Test notification delivery
  - `POST /api/v1/notifications/trigger` - Manual reminder trigger
- **Telegram Integration**: Full Telegram bot support
  - Verification code flow for account linking
  - Payment reminders with customizable timing
  - Daily and weekly digest messages
  - Overdue payment alerts
  - Quiet hours support
- **Calendar API**: Payment calendar data
  - `GET /api/v1/calendar/events` - Calendar event data
- **Notification Preferences Model**: New database table
  - Reminder settings (enabled, days before, time)
  - Digest settings (daily, weekly with day selector)
  - Quiet hours (start, end times)
  - Telegram integration fields

### Changed

- **Documentation**: Added comprehensive Notifications API guide
- **Health Endpoint**: Includes Telegram service status

---

## [1.0.0] - 2024-12-15

### Added

- **API Versioning**: All endpoints now available under `/api/v1/` prefix
- **Version Headers**:
  - `X-API-Version` header for version selection
  - `X-API-Supported-Versions` response header
  - `Accept: application/vnd.moneyflow.v1+json` support
- **Deprecation Headers**: Legacy `/api/` endpoints return deprecation warnings
  - `Deprecation: true`
  - `Sunset: Sun, 01 Jun 2025 00:00:00 GMT`
  - `Link: </api/v1/...>; rel="successor-version"`
- **OpenAPI Tags**: Endpoints grouped by functionality
- **Enhanced Documentation**: Improved endpoint descriptions and examples

### Changed

- **Base Path**: Primary API path is now `/api/v1/`
- **App Version**: Updated to 1.0.0
- **API Title**: Changed from "Subscription Tracker API" to "Money Flow API"

### Deprecated

- **Legacy Endpoints**: `/api/*` routes (without v1) are deprecated
  - Will be removed after June 1, 2025
  - Migrate to `/api/v1/*` endpoints

---

## [0.9.0] - 2024-12-14

### Added

- **Performance Indexes**: Database indexes for common queries
  - `ix_subscriptions_user_active_next_payment`
  - `ix_subscriptions_user_payment_type_active`
  - `ix_subscriptions_card_active`
  - `ix_subscriptions_user_category`
  - `ix_payment_history_sub_date_status`
  - `ix_conversations_user_session`
  - `ix_rag_analytics_user_created`
- **Response Caching**: Redis-based caching for list and summary endpoints
- **Locust Load Tests**: Performance testing framework

### Changed

- **Summary Endpoint**: Improved calculation performance
- **List Endpoint**: Optimized with proper indexing

---

## [0.8.0] - 2024-12-13

### Added

- **API Contract Tests**: Schemathesis fuzz testing for all endpoints
- **OpenAPI Spec Export**: Script to generate versioned OpenAPI specs
- **Redis Integration Tests**: Comprehensive cache and rate limit testing
- **Qdrant Integration Tests**: Vector store operation testing
- **Claude API Tests**: AI intent classification testing

### Fixed

- **Pydantic Schema**: Fixed body parameter detection in OpenAPI spec
- **Contract Test Concurrency**: Resolved asyncpg issues with PostgreSQL

---

## [0.7.0] - 2024-12-12

### Added

- **User Data Isolation**: All queries filtered by authenticated user
- **API Response Envelope**: Standardized response format
- **RAG System Improvements**: Better embedding cache and context retrieval

### Fixed

- **Summary Calculations**: Corrected monthly/yearly totals
- **Currency Conversion**: Fixed edge cases in conversion logic
- **Debt/Savings Tracking**: Proper balance calculations

---

## [0.6.0] - 2024-12-11

### Added

- **E2E Testing**: Playwright test framework with CI integration
- **Auth E2E Tests**: Login, register, logout flows
- **Subscription E2E Tests**: CRUD operations via UI
- **Agent E2E Tests**: Natural language command testing

---

## [0.5.0] - 2024-12-10

### Added

- **Structured Logging**: JSON-formatted logs with structlog
- **Request Tracing**: `request_id` in all logs and responses
- **Sentry Integration**: Error tracking for backend
- **Prometheus Metrics**: HTTP and business metrics
- **Health Endpoints**: `/health`, `/health/live`, `/health/ready`

### Security

- **Sensitive Data Redaction**: API keys, tokens, emails redacted from logs

---

## [0.4.0] - 2024-12-09

### Added

- **GitHub Actions CI/CD**: Automated testing and deployment
- **Pre-commit Hooks**: Ruff, Prettier, detect-secrets
- **Security Scanning**: Bandit, Safety, npm audit, Trivy
- **Docker Pipeline**: Multi-arch builds to GHCR
- **Telegram Notifications**: CI/CD status alerts

---

## [0.3.0] - 2024-12-08

### Added

- **Rate Limiting**: Redis-backed limits with slowapi
  - 100/min GET, 20/min writes, 10/min agent, 5/min auth
- **Prompt Injection Protection**: 20+ dangerous pattern blocks
- **Security Headers**: CSP, HSTS, X-Frame-Options
- **CORS Hardening**: Environment-based configuration
- **Input Validation**: Enhanced Pydantic validators

---

## [0.2.0] - 2024-12-07

### Added

- **JWT Authentication**: Access and refresh tokens
- **User Model**: Email, password (bcrypt), roles
- **Auth Endpoints**: Register, login, logout, refresh, me
- **Token Blacklist**: Redis-based logout support
- **Protected Routes**: All subscription endpoints require auth

### Security

- **Password Hashing**: bcrypt with salt
- **Password Validation**: Strength requirements enforced

---

## [0.1.0] - 2024-12-01

### Added

- **Initial Release**
- **Subscription CRUD**: Create, read, update, delete
- **8 Payment Types**: subscription, housing, utility, etc.
- **AI Agent**: Natural language command processing
- **Currency Support**: GBP (default), USD, EUR, UAH
- **RAG System**: Conversational context and semantic search
- **Import/Export**: JSON and CSV formats

---

## Versioning Policy

- **Major (X.0.0)**: Breaking changes to API contract
- **Minor (0.X.0)**: New features, backward compatible
- **Patch (0.0.X)**: Bug fixes, no API changes

## Deprecation Policy

1. Deprecated features announced with `Deprecation` header
2. Minimum 6-month sunset period
3. Migration guide provided
4. Breaking changes only in major versions

## Support

- Current version: v1.1.0
- Supported versions: v1.x
- End of life: See sunset dates in deprecation headers
