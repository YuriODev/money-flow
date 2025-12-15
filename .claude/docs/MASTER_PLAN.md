# Money Flow - Master Development Plan

> **Comprehensive Roadmap for Production-Ready Enhancement**
>
> **Version**: 1.0.0
> **Created**: December 13, 2025
> **Project**: Money Flow (Subscription Tracker)
> **Total Duration**: 16 Weeks (4 Phases)
> **Estimated Effort**: ~400 hours

---

## Executive Summary

This master plan transforms Money Flow from a well-architected personal project into a production-ready, secure, and scalable application. The plan is organized into 4 phases across 16 weeks, with each phase building upon the previous.

### Phase Overview

| Phase | Name | Duration | Focus Areas |
|-------|------|----------|-------------|
| **Phase 1** | Foundation & Security | Weeks 1-4 | Auth, Security Hardening, CI/CD |
| **Phase 2** | Quality & Testing | Weeks 5-8 | E2E Tests, Bug Fixes, Monitoring |
| **Phase 3** | Architecture & Performance | Weeks 9-12 | Scalability, Caching, API Versioning |
| **Phase 4** | Features & Polish | Weeks 13-16 | Custom Skills, Mobile, Advanced Features |

### Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Test Coverage | ~70% | 95%+ |
| E2E Test Count | 0 | 50+ |
| Security Score | D | A |
| API Response Time (p95) | Unknown | <200ms |
| Uptime SLA | N/A | 99.9% |
| CI/CD Pipeline | None | Full automation |

---

## Master Sprint Table

### Legend

- 🔴 **Critical** - Blocking for production
- 🟠 **High** - Important for stability
- 🟡 **Medium** - Enhances quality
- 🟢 **Low** - Nice to have
- ⏱️ **Estimated Hours**
- 📦 **Deliverable**

---

# PHASE 1: Foundation & Security (Weeks 1-4)

## Sprint 1.1: Authentication System (Week 1)

### Overview
Implement complete user authentication with JWT tokens, secure password handling, and session management.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **1.1.1** | **Database Schema for Users** | ✅ | 4h | None | `users` table migration |
| 1.1.1.1 | Create User model with SQLAlchemy | ✅ | 1h | - | `src/models/user.py` |
| 1.1.1.2 | Add fields: id, email, hashed_password, created_at, updated_at, is_active, is_verified | ✅ | 1h | 1.1.1.1 | Model complete |
| 1.1.1.3 | Create Alembic migration | ✅ | 1h | 1.1.1.2 | Migration file |
| 1.1.1.4 | Add user_id foreign key to subscriptions table | ✅ | 1h | 1.1.1.3 | Updated schema |
| **1.1.2** | **Password Security** | ✅ | 3h | 1.1.1 | Secure auth utils |
| 1.1.2.1 | Install passlib[bcrypt] and python-jose | ✅ | 0.5h | - | Updated requirements.txt |
| 1.1.2.2 | Create password hashing utilities | ✅ | 1h | 1.1.2.1 | `src/auth/security.py` |
| 1.1.2.3 | Implement password strength validation | ✅ | 1h | 1.1.2.2 | Validation rules |
| 1.1.2.4 | Add password reset token generation | ✅ | 0.5h | 1.1.2.2 | Token utils |
| **1.1.3** | **JWT Token System** | ✅ | 4h | 1.1.2 | Token auth |
| 1.1.3.1 | Create JWT token creation/validation | ✅ | 1.5h | - | `src/auth/jwt.py` |
| 1.1.3.2 | Implement access token (15min expiry) | ✅ | 1h | 1.1.3.1 | Access tokens |
| 1.1.3.3 | Implement refresh token (7 day expiry) | ✅ | 1h | 1.1.3.1 | Refresh tokens |
| 1.1.3.4 | Add token blacklist in Redis | ✅ | 0.5h | 1.1.3.1 | Logout support |
| **1.1.4** | **Auth API Endpoints** | ✅ | 6h | 1.1.3 | Auth router |
| 1.1.4.1 | POST /api/auth/register | ✅ | 1h | - | Registration endpoint |
| 1.1.4.2 | POST /api/auth/login | ✅ | 1h | 1.1.4.1 | Login endpoint |
| 1.1.4.3 | POST /api/auth/refresh | ✅ | 1h | 1.1.4.2 | Token refresh |
| 1.1.4.4 | POST /api/auth/logout | ✅ | 0.5h | 1.1.4.3 | Logout endpoint |
| 1.1.4.5 | GET /api/auth/me | ✅ | 0.5h | 1.1.4.2 | Current user info |
| 1.1.4.6 | POST /api/auth/forgot-password | ✅ | 1h | 1.1.4.1 | Password reset request |
| 1.1.4.7 | POST /api/auth/reset-password | ✅ | 1h | 1.1.4.6 | Password reset confirm |
| **1.1.5** | **Auth Middleware** | ✅ | 3h | 1.1.4 | Protected routes |
| 1.1.5.1 | Create FastAPI dependency for auth | ✅ | 1h | - | `get_current_user` |
| 1.1.5.2 | Apply to all subscription endpoints | ✅ | 1h | 1.1.5.1 | Protected routes |
| 1.1.5.3 | Add user_id filtering to all queries | ✅ | 1h | 1.1.5.2 | Data isolation |

**Sprint 1.1 Deliverables:**
- 📦 Complete user authentication system
- 📦 JWT access/refresh token flow
- 📦 All existing endpoints protected
- 📦 User data isolation

**Sprint 1.1 Tests Required:**
```python
# tests/test_auth.py
- test_register_new_user
- test_register_duplicate_email
- test_login_valid_credentials
- test_login_invalid_credentials
- test_refresh_token
- test_logout_invalidates_token
- test_protected_endpoint_without_token
- test_protected_endpoint_with_valid_token
- test_user_cannot_access_other_user_data
```

---

## Sprint 1.2: Security Hardening (Week 2)

### Overview
Implement comprehensive security measures including rate limiting, input validation, prompt injection protection, and security headers.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **1.2.1** | **Rate Limiting** | ✅ | 4h | Sprint 1.1 | Rate limiter |
| 1.2.1.1 | Install slowapi | ✅ | 0.5h | - | Updated requirements |
| 1.2.1.2 | Configure Redis-backed rate limiter | ✅ | 1h | 1.2.1.1 | Limiter config |
| 1.2.1.3 | Apply 100/min limit to GET endpoints | ✅ | 1h | 1.2.1.2 | GET protection |
| 1.2.1.4 | Apply 20/min limit to POST/PUT/DELETE | ✅ | 1h | 1.2.1.2 | Write protection |
| 1.2.1.5 | Apply 10/min limit to /api/agent/execute | ✅ | 0.5h | 1.2.1.2 | AI protection |
| **1.2.2** | **Prompt Injection Protection** | ✅ | 5h | None | Safe NL parsing |
| 1.2.2.1 | Create input sanitizer module | ✅ | 1h | - | `src/security/sanitizer.py` |
| 1.2.2.2 | Define dangerous pattern blocklist | ✅ | 1h | 1.2.2.1 | Pattern list |
| 1.2.2.3 | Implement context boundary enforcement | ✅ | 1.5h | 1.2.2.2 | Boundary checks |
| 1.2.2.4 | Add output validation for AI responses | ✅ | 1h | 1.2.2.3 | Output validation |
| 1.2.2.5 | Create prompt injection test suite | ✅ | 0.5h | 1.2.2.4 | Security tests |
| **1.2.3** | **Input Validation Enhancement** | ✅ | 4h | None | Strict validation |
| 1.2.3.1 | Add Pydantic validators for all string fields | ✅ | 1h | - | String validation |
| 1.2.3.2 | Implement max length constraints | ✅ | 0.5h | 1.2.3.1 | Length limits |
| 1.2.3.3 | Add regex validation for service_name | ✅ | 0.5h | 1.2.3.1 | Name validation |
| 1.2.3.4 | Validate currency codes against enum | ✅ | 0.5h | - | Currency validation |
| 1.2.3.5 | Add amount range validation (0.01 - 1,000,000) | ✅ | 0.5h | - | Amount validation |
| 1.2.3.6 | Sanitize notes field for XSS | ✅ | 1h | - | XSS protection |
| **1.2.4** | **Security Headers** | ✅ | 2h | None | Secure headers |
| 1.2.4.1 | Add secure-headers middleware | ✅ | 0.5h | - | Middleware setup |
| 1.2.4.2 | Configure CSP, X-Frame-Options, etc. | ✅ | 1h | 1.2.4.1 | Header config |
| 1.2.4.3 | Add HSTS for HTTPS enforcement | ✅ | 0.5h | 1.2.4.2 | HSTS header |
| **1.2.5** | **CORS Hardening** | ✅ | 2h | None | Secure CORS |
| 1.2.5.1 | Remove wildcard CORS in production | ✅ | 0.5h | - | Specific origins |
| 1.2.5.2 | Configure allowed methods explicitly | ✅ | 0.5h | 1.2.5.1 | Method whitelist |
| 1.2.5.3 | Set appropriate max_age | ✅ | 0.5h | 1.2.5.1 | Cache config |
| 1.2.5.4 | Add environment-based CORS config | ✅ | 0.5h | 1.2.5.1 | Env-aware CORS |
| **1.2.6** | **Secrets Management** | ✅ | 3h | None | Secure secrets |
| 1.2.6.1 | Create .env.example with all variables | ✅ | 0.5h | - | Template file |
| 1.2.6.2 | Add .env to .gitignore verification | ✅ | 0.25h | - | Git security |
| 1.2.6.3 | Implement secrets validation on startup | ✅ | 1h | - | Startup checks |
| 1.2.6.4 | Add GCP Secret Manager integration | ✅ | 1.25h | - | Cloud secrets |

**Sprint 1.2 Security Checklist:**
```
✅ Rate limiting on all endpoints
✅ Prompt injection patterns blocked
✅ Input validation on all fields
✅ Security headers configured
✅ CORS restricted to known origins
✅ Secrets not in code/logs
✅ SQL injection prevented (ORM)
✅ XSS protection on notes
```

---

## Sprint 1.3: CI/CD Pipeline (Week 3)

### Overview
Implement complete CI/CD pipeline with GitHub Actions for automated testing, security scanning, and deployment.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **1.3.1** | **GitHub Actions Setup** | ✅ | 2h | None | Workflow files |
| 1.3.1.1 | Create `.github/workflows/` directory | ✅ | 0.25h | - | Directory structure |
| 1.3.1.2 | Create `ci.yml` for continuous integration | ✅ | 1h | 1.3.1.1 | CI workflow |
| 1.3.1.3 | Create `cd.yml` for deployment | ✅ | 0.75h | 1.3.1.1 | CD workflow |
| **1.3.2** | **Test Automation Pipeline** | ✅ | 6h | 1.3.1 | Auto tests |
| 1.3.2.1 | Configure Python test matrix (3.11, 3.12) | ✅ | 0.5h | - | Python matrix |
| 1.3.2.2 | Set up PostgreSQL service container | ✅ | 1h | 1.3.2.1 | Test DB |
| 1.3.2.3 | Set up Redis service container | ✅ | 0.5h | 1.3.2.1 | Test Redis |
| 1.3.2.4 | Configure pytest with coverage reporting | ✅ | 1h | 1.3.2.2 | Coverage report |
| 1.3.2.5 | Add coverage threshold check (90%) | ✅ | 0.5h | 1.3.2.4 | Quality gate (70% initial) |
| 1.3.2.6 | Configure frontend test runner (Jest/Vitest) | ✅ | 1.5h | - | Frontend tests (placeholder) |
| 1.3.2.7 | Add TypeScript type checking step | ✅ | 0.5h | 1.3.2.6 | Type safety |
| 1.3.2.8 | Cache pip and npm dependencies | ✅ | 0.5h | 1.3.2.4 | Faster builds |
| **1.3.3** | **Code Quality Gates** | ✅ | 4h | 1.3.1 | Quality checks |
| 1.3.3.1 | Add Ruff linting step | ✅ | 0.5h | - | Python linting |
| 1.3.3.2 | Add Ruff formatting check | ✅ | 0.5h | 1.3.3.1 | Code formatting |
| 1.3.3.3 | Add ESLint for frontend | ✅ | 0.5h | - | JS/TS linting |
| 1.3.3.4 | Add Prettier check for frontend | ✅ | 0.5h | 1.3.3.3 | Frontend format (via pre-commit) |
| 1.3.3.5 | Configure pre-commit hooks | ✅ | 1h | 1.3.3.2 | Local checks |
| 1.3.3.6 | Add commit message linting | ✅ | 0.5h | 1.3.3.5 | Conventional commits |
| 1.3.3.7 | Add PR template | ✅ | 0.5h | - | PR standards |
| **1.3.4** | **Security Scanning** | ✅ | 4h | 1.3.1 | Security gates |
| 1.3.4.1 | Add Bandit for Python security scan | ✅ | 0.5h | - | Python security |
| 1.3.4.2 | Add Safety for dependency vulnerabilities | ✅ | 0.5h | 1.3.4.1 | Dep scanning |
| 1.3.4.3 | Add npm audit for frontend | ✅ | 0.5h | - | JS dep scanning |
| 1.3.4.4 | Add Trivy for Docker image scanning | ✅ | 1h | - | Image security |
| 1.3.4.5 | Configure SAST with CodeQL | ✅ | 1h | - | Static analysis |
| 1.3.4.6 | Add secret scanning | ✅ | 0.5h | - | Leaked secrets |
| **1.3.5** | **Docker Build Pipeline** | ✅ | 4h | 1.3.4 | Container builds |
| 1.3.5.1 | Multi-stage Dockerfile optimization | ✅ | 1h | - | Smaller images |
| 1.3.5.2 | Build backend image on PR | ✅ | 0.5h | 1.3.5.1 | Backend build |
| 1.3.5.3 | Build frontend image on PR | ✅ | 0.5h | 1.3.5.1 | Frontend build |
| 1.3.5.4 | Push to GitHub Container Registry | ✅ | 1h | 1.3.5.2 | Image registry |
| 1.3.5.5 | Tag images with commit SHA and version | ✅ | 0.5h | 1.3.5.4 | Image tagging |
| 1.3.5.6 | Add build matrix for arm64/amd64 | ✅ | 0.5h | 1.3.5.4 | Multi-arch |
| **1.3.6** | **Deployment Automation** | ✅ | 6h | 1.3.5 | Auto deploy |
| 1.3.6.1 | Create staging environment config | ✅ | 1h | - | Staging env |
| 1.3.6.2 | Create production environment config | ✅ | 1h | 1.3.6.1 | Prod env |
| 1.3.6.3 | Deploy to staging on main branch push | ✅ | 1h | 1.3.6.1 | Auto staging |
| 1.3.6.4 | Deploy to production on release tag | ✅ | 1h | 1.3.6.2 | Release deploy |
| 1.3.6.5 | Add Telegram notification on deploy | ✅ | 0.5h | 1.3.6.3 | Deploy alerts |
| 1.3.6.6 | Add rollback workflow | ✅ | 0.5h | 1.3.6.4 | Rollback support |
| 1.3.6.7 | Add database migration step | ✅ | 1h | 1.3.6.3 | DB migrations (placeholder) |

**Sprint 1.3 CI/CD Workflow:**
```yaml
# .github/workflows/ci.yml structure
on: [push, pull_request]
jobs:
  lint:           # Ruff, ESLint, Prettier
  test-backend:   # pytest + PostgreSQL + Redis
  test-frontend:  # Jest/Vitest
  security:       # Bandit, Safety, npm audit
  build:          # Docker multi-stage
  deploy-staging: # On main branch
  deploy-prod:    # On release tag
```

---

## Sprint 1.4: Logging & Observability Setup (Week 4)

### Overview
Implement structured logging, error tracking, and basic monitoring infrastructure.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **1.4.1** | **Structured Logging** | ✅ | 5h | None | JSON logs |
| 1.4.1.1 | Install structlog | ✅ | 0.5h | - | Updated requirements |
| 1.4.1.2 | Configure JSON log format | ✅ | 1h | 1.4.1.1 | Log config |
| 1.4.1.3 | Add request_id to all logs | ✅ | 1h | 1.4.1.2 | Request tracing |
| 1.4.1.4 | Add user_id to authenticated request logs | ✅ | 0.5h | 1.4.1.3 | User context |
| 1.4.1.5 | Configure log levels per environment | ✅ | 0.5h | 1.4.1.2 | Env-aware logging |
| 1.4.1.6 | Add sensitive data redaction | ✅ | 1h | 1.4.1.2 | PII protection |
| 1.4.1.7 | Frontend error logging to backend | ✅ | 0.5h | - | Frontend errors |
| **1.4.2** | **Request/Response Logging** | ✅ | 3h | 1.4.1 | API logging |
| 1.4.2.1 | Create logging middleware | ✅ | 1h | - | Middleware |
| 1.4.2.2 | Log request method, path, duration | ✅ | 0.5h | 1.4.2.1 | Request logs |
| 1.4.2.3 | Log response status, size | ✅ | 0.5h | 1.4.2.1 | Response logs |
| 1.4.2.4 | Exclude health check from logs | ✅ | 0.25h | 1.4.2.2 | Clean logs |
| 1.4.2.5 | Add slow query logging (>1s) | ✅ | 0.75h | 1.4.2.2 | Performance logs |
| **1.4.3** | **Error Tracking (Sentry)** | ✅ | 4h | None | Error tracking |
| 1.4.3.1 | Create Sentry account/project | ✅ | 0.5h | - | Sentry setup |
| 1.4.3.2 | Install sentry-sdk[fastapi] | ✅ | 0.25h | 1.4.3.1 | SDK install |
| 1.4.3.3 | Configure Sentry for backend | ✅ | 1h | 1.4.3.2 | Backend Sentry |
| 1.4.3.4 | Install @sentry/nextjs | ✅ | 0.25h | 1.4.3.1 | Frontend SDK |
| 1.4.3.5 | Configure Sentry for frontend | ✅ | 1h | 1.4.3.4 | Frontend Sentry |
| 1.4.3.6 | Add user context to Sentry | ✅ | 0.5h | 1.4.3.3 | User tracking |
| 1.4.3.7 | Configure release tracking | ✅ | 0.5h | 1.4.3.3 | Release context |
| **1.4.4** | **Health Check Enhancement** | ✅ | 3h | None | Better health checks |
| 1.4.4.1 | Add database connection check | ✅ | 0.5h | - | DB health |
| 1.4.4.2 | Add Redis connection check | ✅ | 0.5h | - | Redis health |
| 1.4.4.3 | Add Qdrant connection check | ✅ | 0.5h | - | Qdrant health |
| 1.4.4.4 | Add Claude API connectivity check | ✅ | 0.5h | - | AI health |
| 1.4.4.5 | Create /health/ready endpoint | ✅ | 0.5h | 1.4.4.1 | Readiness probe |
| 1.4.4.6 | Create /health/live endpoint | ✅ | 0.5h | - | Liveness probe |
| **1.4.5** | **Metrics Collection** | ✅ | 4h | None | Prometheus metrics |
| 1.4.5.1 | Install prometheus-fastapi-instrumentator | ✅ | 0.5h | - | Metrics lib |
| 1.4.5.2 | Expose /metrics endpoint | ✅ | 0.5h | 1.4.5.1 | Metrics endpoint |
| 1.4.5.3 | Add custom business metrics | ✅ | 1.5h | 1.4.5.2 | Custom metrics |
| 1.4.5.4 | Add database query metrics | ✅ | 0.5h | 1.4.5.2 | DB metrics |
| 1.4.5.5 | Add AI agent latency metrics | ✅ | 0.5h | 1.4.5.2 | AI metrics |
| 1.4.5.6 | Add RAG query performance metrics | ✅ | 0.5h | 1.4.5.2 | RAG metrics |

**Phase 1 Completion Checklist:**
```
✅ User authentication fully functional (Sprint 1.1)
✅ All endpoints protected and rate limited (Sprint 1.2)
✅ Security scanning in CI/CD (Sprint 1.3)
✅ Automated deployment pipeline (Sprint 1.3)
✅ Structured logging with request tracing (Sprint 1.4)
✅ Error tracking with Sentry - Backend (Sprint 1.4)
✅ Health checks for all services (Sprint 1.4)
✅ Frontend Sentry integration (Completed in Sprint 2.2)
```

**Phase 1 Status: ✅ COMPLETE** (December 14, 2025)

---

# PHASE 2: Quality & Testing (Weeks 5-8)

## Sprint 2.1: E2E Testing Framework (Week 5) ✅ COMPLETE

### Overview
Set up comprehensive E2E testing with Playwright, covering all user workflows.

**Status: ✅ COMPLETE** (December 14, 2025)

**Completed:**
- Playwright installed and configured with chromium browser
- playwright.config.ts with multi-project setup (desktop Chrome, mobile)
- Test fixtures: DashboardPage, AgentChatPage, API request helpers
- Authentication setup (auth.setup.ts) for authenticated test state
- Authentication E2E tests (auth.spec.ts): login, logout, validation, protected routes
- Subscription CRUD E2E tests (subscriptions.spec.ts): create, edit, delete, filter, search
- Agent Chat E2E tests (agent.spec.ts): NL commands, all payment types, conversation context
- Docker E2E configuration (docker-compose.e2e.yml, Dockerfile.e2e)
- CI pipeline integration (test-e2e job in ci.yml with PostgreSQL + Redis services)

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **2.1.1** | **Playwright Setup** | ✅ | 3h | None | E2E framework |
| 2.1.1.1 | Install @playwright/test | ✅ | 0.5h | - | Playwright install |
| 2.1.1.2 | Configure playwright.config.ts | ✅ | 1h | 2.1.1.1 | Config file |
| 2.1.1.3 | Set up test fixtures for auth | ✅ | 1h | 2.1.1.2 | Auth fixtures |
| 2.1.1.4 | Configure Docker Compose for E2E | ✅ | 0.5h | 2.1.1.2 | Test environment |
| **2.1.2** | **Authentication E2E Tests** | ✅ | 4h | 2.1.1 | Auth tests |
| 2.1.2.1 | Test user registration flow | ✅ | 0.75h | - | Register test |
| 2.1.2.2 | Test login flow | ✅ | 0.75h | 2.1.2.1 | Login test |
| 2.1.2.3 | Test logout flow | ✅ | 0.5h | 2.1.2.2 | Logout test |
| 2.1.2.4 | Test password reset flow | ✅ | 1h | 2.1.2.1 | Reset test |
| 2.1.2.5 | Test session persistence | ✅ | 0.5h | 2.1.2.2 | Session test |
| 2.1.2.6 | Test invalid credentials handling | ✅ | 0.5h | 2.1.2.2 | Error handling |
| **2.1.3** | **Subscription CRUD E2E Tests** | ✅ | 6h | 2.1.1 | CRUD tests |
| 2.1.3.1 | Test add subscription (all 9 types) | ✅ | 2h | - | Add tests |
| 2.1.3.2 | Test edit subscription | ✅ | 1h | 2.1.3.1 | Edit tests |
| 2.1.3.3 | Test delete subscription | ✅ | 0.5h | 2.1.3.1 | Delete tests |
| 2.1.3.4 | Test subscription list filtering | ✅ | 1h | 2.1.3.1 | Filter tests |
| 2.1.3.5 | Test subscription search | ✅ | 0.5h | 2.1.3.1 | Search tests |
| 2.1.3.6 | Test pagination | ✅ | 0.5h | 2.1.3.1 | Pagination tests |
| 2.1.3.7 | Test sorting | ✅ | 0.5h | 2.1.3.1 | Sort tests |
| **2.1.4** | **Payment Cards E2E Tests** | ✅ | 3h | 2.1.1 | Card tests |
| 2.1.4.1 | Test add payment card | ✅ | 0.75h | - | Add card test |
| 2.1.4.2 | Test edit payment card | ✅ | 0.5h | 2.1.4.1 | Edit card test |
| 2.1.4.3 | Test delete payment card | ✅ | 0.5h | 2.1.4.1 | Delete card test |
| 2.1.4.4 | Test assign subscription to card | ✅ | 0.75h | 2.1.4.1 | Assignment test |
| 2.1.4.5 | Test card balance calculation | ✅ | 0.5h | 2.1.4.4 | Balance test |
| **2.1.5** | **Import/Export E2E Tests** | ✅ | 3h | 2.1.1 | I/O tests |
| 2.1.5.1 | Test JSON export | ✅ | 0.5h | - | JSON export test |
| 2.1.5.2 | Test JSON import | ✅ | 0.75h | 2.1.5.1 | JSON import test |
| 2.1.5.3 | Test CSV export | ✅ | 0.5h | - | CSV export test |
| 2.1.5.4 | Test CSV import | ✅ | 0.75h | 2.1.5.3 | CSV import test |
| 2.1.5.5 | Test import validation errors | ✅ | 0.5h | 2.1.5.2 | Validation test |

---

## Sprint 2.2: AI Agent E2E & Bug Fixes (Week 6)

### Overview
E2E tests for AI agent functionality and fixing identified endpoint issues.

**Sprint 2.2 Status: ✅ COMPLETE** (December 15, 2025)

**Completed:**
- AI Agent E2E tests with comprehensive test coverage
- Basic add command NL parsing (subscription, yearly, weekly frequencies)
- Edit command NL parsing
- Delete command NL parsing
- Query commands (spending summary, upcoming payments, list all)
- Debt tracking commands (add debt, make payment, total debt)
- Savings goal commands (add goal, contribute, check progress)
- Reference resolution ("cancel it", "that one")
- Multi-turn conversations (context maintenance, follow-ups, corrections)
- Additional payment types (housing, utilities, insurance, transfers)
- Frontend Sentry integration completed (deferred from Sprint 1.4)
- **User data isolation** - Fixed subscription_service.py to filter by user_id
- **API endpoint protection** - All subscription endpoints now require current_user
- **Settings Roadmap** - Created comprehensive docs/SETTINGS_ROADMAP.md (1000+ lines)

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **2.2.1** | **AI Agent E2E Tests** | ✅ | 6h | Sprint 2.1 | Agent tests |
| 2.2.1.1 | Test basic add command NL parsing | ✅ | 1h | - | Add command test |
| 2.2.1.2 | Test edit command NL parsing | ✅ | 0.75h | 2.2.1.1 | Edit command test |
| 2.2.1.3 | Test delete command NL parsing | ✅ | 0.5h | 2.2.1.1 | Delete command test |
| 2.2.1.4 | Test query commands (spending summary) | ✅ | 0.75h | 2.2.1.1 | Query test |
| 2.2.1.5 | Test debt tracking commands | ✅ | 0.75h | 2.2.1.1 | Debt test |
| 2.2.1.6 | Test savings goal commands | ✅ | 0.75h | 2.2.1.1 | Savings test |
| 2.2.1.7 | Test reference resolution ("cancel it") | ✅ | 0.75h | 2.2.1.1 | Context test |
| 2.2.1.8 | Test multi-turn conversations | ✅ | 0.75h | 2.2.1.7 | Multi-turn test |
| **2.2.2** | **Endpoint Bug Fixes** | ✅ | 8h | None | Bug fixes |
| 2.2.2.1 | Audit all GET endpoints for edge cases | ✅ | 1h | - | Audit report |
| 2.2.2.2 | Fix subscription summary calculation bugs | ✅ | 1.5h | 2.2.2.1 | Summary fix |
| 2.2.2.3 | Fix upcoming payments date filtering | ✅ | 1h | 2.2.2.1 | Date filter fix |
| 2.2.2.4 | Fix currency conversion edge cases | ✅ | 1h | 2.2.2.1 | Currency fix |
| 2.2.2.5 | Fix debt balance calculation | ✅ | 1h | 2.2.2.1 | Debt calc fix |
| 2.2.2.6 | Fix savings progress calculation | ✅ | 1h | 2.2.2.1 | Savings calc fix |
| 2.2.2.7 | Fix card balance aggregation | ✅ | 0.75h | 2.2.2.1 | Card balance fix |
| 2.2.2.8 | Fix export format inconsistencies | ✅ | 0.75h | 2.2.2.1 | Export fix |
| **2.2.3** | **API Response Consistency** | ✅ | 4h | 2.2.2 | Consistent API |
| 2.2.3.1 | Standardize error response format | ✅ | 1h | - | Error format |
| 2.2.3.2 | Standardize success response format | ✅ | 0.5h | 2.2.3.1 | Success format |
| 2.2.3.3 | Add consistent pagination format | ✅ | 1h | 2.2.3.2 | Pagination format |
| 2.2.3.4 | Add response envelope (data, meta, errors) | ✅ | 1h | 2.2.3.3 | Response envelope |
| 2.2.3.5 | Update frontend to handle new format | ✅ | 0.5h | 2.2.3.4 | Frontend update |
| **2.2.4** | **RAG System Bug Fixes** | ✅ | 4h | None | RAG fixes |
| 2.2.4.1 | Fix embedding cache invalidation | ✅ | 1h | - | Cache fix |
| 2.2.4.2 | Fix conversation context retrieval | ✅ | 1h | - | Context fix |
| 2.2.4.3 | Fix semantic search relevance scoring | ✅ | 1h | - | Search fix |
| 2.2.4.4 | Fix historical query date parsing | ✅ | 0.5h | - | Date parsing fix |
| 2.2.4.5 | Add missing index on vector collection | ✅ | 0.5h | - | Index optimization |
| **2.2.5** | **User Data Isolation** | ✅ | 2h | None | Multi-user support |
| 2.2.5.1 | Add user_id filtering to subscription_service | ✅ | 0.5h | - | Service fix |
| 2.2.5.2 | Add current_user dependency to all endpoints | ✅ | 1h | 2.2.5.1 | Endpoint protection |
| 2.2.5.3 | Verify data isolation between users | ✅ | 0.5h | 2.2.5.2 | Isolation test |
| **2.2.6** | **Settings Roadmap Planning** | ✅ | 3h | None | Feature roadmap |
| 2.2.6.1 | Define 10 settings tabs structure | ✅ | 1h | - | Tab structure |
| 2.2.6.2 | Plan AI-powered features | ✅ | 1h | - | AI features |
| 2.2.6.3 | Create docs/SETTINGS_ROADMAP.md | ✅ | 1h | - | Roadmap doc |

---

## Sprint 2.3: Integration Tests & Contract Testing (Week 7)

### Overview
Comprehensive integration tests and API contract testing.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **2.3.1** | **API Contract Testing** | ✅ | 5h | None | Contract tests |
| 2.3.1.1 | Generate OpenAPI spec from FastAPI | ✅ | 0.5h | - | openapi.json |
| 2.3.1.2 | Set up Schemathesis for fuzz testing | ✅ | 1h | 2.3.1.1 | Fuzz testing |
| 2.3.1.3 | Create contract tests for all endpoints | ✅ | 2h | 2.3.1.2 | Contract tests |
| 2.3.1.4 | Add contract tests to CI pipeline | ✅ | 0.5h | 2.3.1.3 | CI integration |
| 2.3.1.5 | Set up OpenAPI diff checking | ✅ | 1h | 2.3.1.1 | Breaking change detection |
| **2.3.2** | **Database Integration Tests** | ✅ | 6h | None | DB tests |
| 2.3.2.1 | Test subscription CRUD with real DB | ✅ | 1h | - | Sub CRUD tests |
| 2.3.2.2 | Test card-subscription relationships | ✅ | 1h | 2.3.2.1 | Relationship tests |
| 2.3.2.3 | Test cascade deletes | ✅ | 0.5h | 2.3.2.1 | Cascade tests |
| 2.3.2.4 | Test concurrent modifications | ✅ | 1h | 2.3.2.1 | Concurrency tests |
| 2.3.2.5 | Test transaction rollbacks | ✅ | 0.5h | 2.3.2.1 | Rollback tests |
| 2.3.2.6 | Test migration up/down | ✅ | 1h | - | Migration tests |
| 2.3.2.7 | Test data integrity constraints | ✅ | 1h | 2.3.2.1 | Constraint tests |
| **2.3.3** | **Redis Integration Tests** | 🟠 | 3h | None | Redis tests |
| 2.3.3.1 | Test embedding cache operations | 🟠 | 0.75h | - | Cache tests |
| 2.3.3.2 | Test rate limiter storage | 🟠 | 0.75h | - | Rate limit tests |
| 2.3.3.3 | Test token blacklist | 🟠 | 0.5h | - | Blacklist tests |
| 2.3.3.4 | Test cache expiration | 🟡 | 0.5h | 2.3.3.1 | TTL tests |
| 2.3.3.5 | Test Redis connection failure handling | 🟠 | 0.5h | - | Failure tests |
| **2.3.4** | **Qdrant Integration Tests** | ✅ | 4h | None | Vector DB tests |
| 2.3.4.1 | Test vector insertion | ✅ | 0.75h | - | Insert tests |
| 2.3.4.2 | Test similarity search | ✅ | 1h | 2.3.4.1 | Search tests |
| 2.3.4.3 | Test filtering by user_id | ✅ | 0.5h | 2.3.4.2 | Filter tests |
| 2.3.4.4 | Test collection management | ✅ | 0.5h | - | Collection tests |
| 2.3.4.5 | Test Qdrant connection failure handling | ✅ | 0.5h | - | Failure tests |
| 2.3.4.6 | Test embedding update operations | ✅ | 0.75h | 2.3.4.1 | Update tests |
| **2.3.5** | **Claude API Integration Tests** | 🟠 | 3h | None | AI tests |
| 2.3.5.1 | Test API connection and auth | 🟠 | 0.5h | - | Connection test |
| 2.3.5.2 | Test intent classification accuracy | 🟠 | 1h | 2.3.5.1 | Classification tests |
| 2.3.5.3 | Test entity extraction accuracy | 🟠 | 1h | 2.3.5.1 | Extraction tests |
| 2.3.5.4 | Test API failure fallback (regex) | 🔴 | 0.5h | - | Fallback test |

---

## Sprint 2.4: Performance & Load Testing (Week 8)

### Overview
Performance benchmarking and load testing to ensure scalability.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **2.4.1** | **Performance Benchmarking** | 🟠 | 5h | None | Benchmarks |
| 2.4.1.1 | Set up Locust for load testing | 🟠 | 1h | - | Locust setup |
| 2.4.1.2 | Create benchmark scenarios | 🟠 | 1h | 2.4.1.1 | Test scenarios |
| 2.4.1.3 | Benchmark GET /subscriptions | 🟠 | 0.5h | 2.4.1.2 | List benchmark |
| 2.4.1.4 | Benchmark POST /subscriptions | 🟠 | 0.5h | 2.4.1.2 | Create benchmark |
| 2.4.1.5 | Benchmark /api/agent/execute | 🟠 | 0.5h | 2.4.1.2 | Agent benchmark |
| 2.4.1.6 | Benchmark /api/search/notes | 🟠 | 0.5h | 2.4.1.2 | Search benchmark |
| 2.4.1.7 | Generate baseline performance report | 🟠 | 1h | 2.4.1.3 | Baseline report |
| **2.4.2** | **Load Testing** | 🟠 | 4h | 2.4.1 | Load tests |
| 2.4.2.1 | Test 10 concurrent users | 🟠 | 0.5h | - | 10 users test |
| 2.4.2.2 | Test 50 concurrent users | 🟠 | 0.5h | 2.4.2.1 | 50 users test |
| 2.4.2.3 | Test 100 concurrent users | 🟠 | 0.5h | 2.4.2.2 | 100 users test |
| 2.4.2.4 | Test sustained load (1 hour) | 🟡 | 1h | 2.4.2.1 | Soak test |
| 2.4.2.5 | Test spike load handling | 🟡 | 0.5h | 2.4.2.1 | Spike test |
| 2.4.2.6 | Document performance limits | 🟠 | 1h | 2.4.2.3 | Limits doc |
| **2.4.3** | **Database Query Optimization** | 🟠 | 5h | 2.4.2 | Query optimization |
| 2.4.3.1 | Add EXPLAIN ANALYZE for slow queries | 🟠 | 1h | - | Query analysis |
| 2.4.3.2 | Add missing indexes | 🔴 | 1h | 2.4.3.1 | Index creation |
| 2.4.3.3 | Optimize N+1 queries | 🟠 | 1h | 2.4.3.1 | N+1 fix |
| 2.4.3.4 | Add connection pooling config | 🟠 | 1h | - | Pool config |
| 2.4.3.5 | Test query performance improvements | 🟠 | 1h | 2.4.3.2 | Performance test |
| **2.4.4** | **Caching Strategy** | 🟡 | 4h | None | Caching |
| 2.4.4.1 | Implement response caching for list endpoints | 🟡 | 1h | - | List caching |
| 2.4.4.2 | Add cache invalidation on mutations | 🟡 | 1h | 2.4.4.1 | Invalidation |
| 2.4.4.3 | Cache summary calculations | 🟡 | 1h | - | Summary caching |
| 2.4.4.4 | Monitor cache hit rates | 🟡 | 0.5h | 2.4.4.1 | Hit rate tracking |
| 2.4.4.5 | Document caching strategy | 🟡 | 0.5h | 2.4.4.3 | Cache docs |

**Phase 2 Completion Checklist:**
```
✅ 50+ E2E tests passing (Sprint 2.1)
✅ All endpoint bugs fixed (Sprint 2.2)
✅ User data isolation implemented (Sprint 2.2)
✅ Settings roadmap planned (Sprint 2.2)
✅ API contract tests in CI (Sprint 2.3.1)
✅ Database integration tests (Sprint 2.3.2) - 33 tests
⏭️ Redis integration tests (Sprint 2.3.3) - Skipped
✅ Qdrant integration tests (Sprint 2.3.4) - 42 tests
□ Claude API integration tests (Sprint 2.3.5)
□ Performance baseline documented (Sprint 2.4)
□ Load test results documented (Sprint 2.4)
□ Database queries optimized (Sprint 2.4)
□ Caching strategy implemented (Sprint 2.4)
```

---

# PHASE 3: Architecture & Performance (Weeks 9-12)

## Sprint 3.1: API Versioning & Documentation (Week 9)

### Overview
Implement API versioning for backward compatibility and comprehensive documentation.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **3.1.1** | **API Versioning** | 🔴 | 6h | None | Versioned API |
| 3.1.1.1 | Create /api/v1/ prefix structure | 🔴 | 1h | - | URL structure |
| 3.1.1.2 | Move all existing routes to v1 | 🔴 | 2h | 3.1.1.1 | Route migration |
| 3.1.1.3 | Update frontend API calls | 🔴 | 1.5h | 3.1.1.2 | Frontend update |
| 3.1.1.4 | Add version header support | 🟡 | 0.5h | 3.1.1.1 | Header versioning |
| 3.1.1.5 | Add deprecation warning middleware | 🟡 | 0.5h | 3.1.1.2 | Deprecation support |
| 3.1.1.6 | Document versioning policy | 🟠 | 0.5h | 3.1.1.2 | Version docs |
| **3.1.2** | **OpenAPI Enhancement** | 🟠 | 5h | 3.1.1 | Better docs |
| 3.1.2.1 | Add detailed endpoint descriptions | 🟠 | 1h | - | Descriptions |
| 3.1.2.2 | Add request/response examples | 🟠 | 1.5h | 3.1.2.1 | Examples |
| 3.1.2.3 | Add error response documentation | 🟠 | 0.5h | 3.1.2.1 | Error docs |
| 3.1.2.4 | Add authentication documentation | 🟠 | 0.5h | - | Auth docs |
| 3.1.2.5 | Group endpoints by tags | 🟡 | 0.5h | 3.1.2.1 | Tag grouping |
| 3.1.2.6 | Export and version OpenAPI spec | 🟠 | 1h | 3.1.2.2 | Spec versioning |
| **3.1.3** | **Developer Documentation** | 🟠 | 6h | None | Dev docs |
| 3.1.3.1 | Create API quickstart guide | 🟠 | 1h | - | Quickstart |
| 3.1.3.2 | Document authentication flow | 🟠 | 0.75h | - | Auth guide |
| 3.1.3.3 | Document webhook integration (future) | 🟡 | 0.5h | - | Webhook docs |
| 3.1.3.4 | Create SDK usage examples | 🟡 | 1h | - | SDK examples |
| 3.1.3.5 | Document rate limiting | 🟠 | 0.5h | - | Rate limit docs |
| 3.1.3.6 | Create Postman collection | 🟠 | 1h | 3.1.2.2 | Postman export |
| 3.1.3.7 | Add API changelog | 🟠 | 0.5h | - | Changelog |
| 3.1.3.8 | Create migration guide (v0 to v1) | 🟠 | 0.75h | 3.1.1.2 | Migration guide |

---

## Sprint 3.2: Database Scalability (Week 10)

### Overview
Prepare database for multi-user scale with proper indexing, partitioning, and backup strategies.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **3.2.1** | **Index Optimization** | 🔴 | 4h | None | Optimized indexes |
| 3.2.1.1 | Analyze query patterns | 🔴 | 1h | - | Query analysis |
| 3.2.1.2 | Add composite index (user_id, payment_type) | 🔴 | 0.5h | 3.2.1.1 | Composite index |
| 3.2.1.3 | Add index on next_billing_date | 🔴 | 0.5h | 3.2.1.1 | Date index |
| 3.2.1.4 | Add partial index for active subscriptions | 🟠 | 0.5h | 3.2.1.1 | Partial index |
| 3.2.1.5 | Add index for card_id lookups | 🟠 | 0.5h | 3.2.1.1 | Card index |
| 3.2.1.6 | Test index effectiveness | 🟠 | 1h | 3.2.1.2 | Index testing |
| **3.2.2** | **Connection Pool Optimization** | 🟠 | 3h | None | Pool config |
| 3.2.2.1 | Configure SQLAlchemy pool size | 🟠 | 0.5h | - | Pool size |
| 3.2.2.2 | Set pool overflow limits | 🟠 | 0.5h | 3.2.2.1 | Overflow config |
| 3.2.2.3 | Add pool pre-ping | 🟠 | 0.25h | 3.2.2.1 | Connection health |
| 3.2.2.4 | Configure pool recycle | 🟠 | 0.25h | 3.2.2.1 | Connection recycling |
| 3.2.2.5 | Add pool metrics logging | 🟡 | 0.5h | 3.2.2.1 | Pool monitoring |
| 3.2.2.6 | Load test pool configuration | 🟠 | 1h | 3.2.2.2 | Pool load test |
| **3.2.3** | **Backup Strategy** | 🔴 | 5h | None | Backup system |
| 3.2.3.1 | Create pg_dump backup script | 🔴 | 1h | - | Backup script |
| 3.2.3.2 | Configure daily backup schedule | 🔴 | 0.5h | 3.2.3.1 | Backup schedule |
| 3.2.3.3 | Set up GCS bucket for backups | 🔴 | 0.5h | - | Backup storage |
| 3.2.3.4 | Implement backup rotation (30 days) | 🟠 | 0.5h | 3.2.3.2 | Rotation policy |
| 3.2.3.5 | Create restore script | 🔴 | 1h | 3.2.3.1 | Restore script |
| 3.2.3.6 | Test backup/restore process | 🔴 | 1h | 3.2.3.5 | DR test |
| 3.2.3.7 | Document DR procedure | 🟠 | 0.5h | 3.2.3.6 | DR docs |
| **3.2.4** | **Query Optimization** | 🟠 | 4h | 3.2.1 | Optimized queries |
| 3.2.4.1 | Optimize subscription list query | 🟠 | 0.75h | - | List optimization |
| 3.2.4.2 | Optimize summary aggregation | 🟠 | 1h | - | Summary optimization |
| 3.2.4.3 | Optimize upcoming payments query | 🟠 | 0.75h | - | Upcoming optimization |
| 3.2.4.4 | Add select_in_loading for relationships | 🟠 | 0.5h | - | Eager loading |
| 3.2.4.5 | Use server-side cursors for exports | 🟡 | 0.5h | - | Export optimization |
| 3.2.4.6 | Benchmark optimized queries | 🟠 | 0.5h | 3.2.4.1 | Query benchmarks |

---

## Sprint 3.3: Service Architecture Improvements (Week 11)

### Overview
Improve service architecture with dependency injection, proper error handling, and resilience patterns.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **3.3.1** | **Dependency Injection** | 🟠 | 5h | None | DI pattern |
| 3.3.1.1 | Install dependency-injector | 🟠 | 0.5h | - | DI library |
| 3.3.1.2 | Create service container | 🟠 | 1h | 3.3.1.1 | Container |
| 3.3.1.3 | Refactor services to use DI | 🟠 | 2h | 3.3.1.2 | Service refactor |
| 3.3.1.4 | Create factory providers | 🟠 | 0.5h | 3.3.1.2 | Factories |
| 3.3.1.5 | Add singleton providers for expensive resources | 🟠 | 0.5h | 3.3.1.2 | Singletons |
| 3.3.1.6 | Update tests to use test container | 🟠 | 0.5h | 3.3.1.3 | Test updates |
| **3.3.2** | **Error Handling Standardization** | 🔴 | 5h | None | Error handling |
| 3.3.2.1 | Create custom exception hierarchy | 🔴 | 1h | - | Exceptions |
| 3.3.2.2 | Create global exception handler | 🔴 | 1h | 3.3.2.1 | Handler |
| 3.3.2.3 | Add validation error formatting | 🟠 | 0.5h | 3.3.2.2 | Validation errors |
| 3.3.2.4 | Add database error handling | 🔴 | 0.5h | 3.3.2.2 | DB errors |
| 3.3.2.5 | Add external API error handling | 🟠 | 0.5h | 3.3.2.2 | API errors |
| 3.3.2.6 | Add error codes and messages catalog | 🟠 | 1h | 3.3.2.1 | Error catalog |
| 3.3.2.7 | Update frontend error handling | 🟠 | 0.5h | 3.3.2.6 | Frontend errors |
| **3.3.3** | **Resilience Patterns** | 🟠 | 6h | None | Resilience |
| 3.3.3.1 | Add circuit breaker for Claude API | 🟠 | 1h | - | Circuit breaker |
| 3.3.3.2 | Add retry with exponential backoff | 🟠 | 1h | 3.3.3.1 | Retry logic |
| 3.3.3.3 | Add timeout configuration | 🔴 | 0.5h | - | Timeouts |
| 3.3.3.4 | Add bulkhead pattern for AI requests | 🟡 | 1h | 3.3.3.1 | Bulkhead |
| 3.3.3.5 | Add fallback for degraded mode | 🟠 | 1h | 3.3.3.1 | Fallback |
| 3.3.3.6 | Add health degradation indicators | 🟡 | 0.5h | 3.3.3.5 | Health status |
| 3.3.3.7 | Test failure scenarios | 🟠 | 1h | 3.3.3.2 | Chaos testing |
| **3.3.4** | **Async Task Queue** | 🟡 | 5h | None | Background tasks |
| 3.3.4.1 | Evaluate task queue options (Celery/ARQ) | 🟡 | 0.5h | - | Evaluation |
| 3.3.4.2 | Set up ARQ with Redis | 🟡 | 1h | 3.3.4.1 | ARQ setup |
| 3.3.4.3 | Move email sending to background | 🟡 | 0.5h | 3.3.4.2 | Email queue |
| 3.3.4.4 | Move export generation to background | 🟡 | 1h | 3.3.4.2 | Export queue |
| 3.3.4.5 | Add task monitoring | 🟡 | 0.5h | 3.3.4.2 | Task monitoring |
| 3.3.4.6 | Add task retry logic | 🟡 | 0.5h | 3.3.4.2 | Task retry |
| 3.3.4.7 | Update Docker Compose with worker | 🟡 | 1h | 3.3.4.2 | Worker container |

---

## Sprint 3.4: Monitoring & Alerting (Week 12)

### Overview
Implement comprehensive monitoring stack with Prometheus, Grafana, and alerting.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **3.4.1** | **Prometheus Setup** | 🟠 | 4h | None | Metrics collection |
| 3.4.1.1 | Add Prometheus to Docker Compose | 🟠 | 0.5h | - | Prometheus container |
| 3.4.1.2 | Configure Prometheus scrape targets | 🟠 | 0.5h | 3.4.1.1 | Scrape config |
| 3.4.1.3 | Add FastAPI metrics exporter | 🟠 | 0.5h | 3.4.1.1 | Backend metrics |
| 3.4.1.4 | Add PostgreSQL exporter | 🟠 | 0.5h | 3.4.1.1 | DB metrics |
| 3.4.1.5 | Add Redis exporter | 🟡 | 0.5h | 3.4.1.1 | Redis metrics |
| 3.4.1.6 | Add Qdrant metrics | 🟡 | 0.5h | 3.4.1.1 | Vector DB metrics |
| 3.4.1.7 | Configure retention and storage | 🟠 | 0.5h | 3.4.1.1 | Storage config |
| 3.4.1.8 | Set up Prometheus federation (future) | 🟡 | 0.5h | 3.4.1.7 | Federation prep |
| **3.4.2** | **Grafana Dashboards** | 🟠 | 6h | 3.4.1 | Visualizations |
| 3.4.2.1 | Add Grafana to Docker Compose | 🟠 | 0.5h | - | Grafana container |
| 3.4.2.2 | Create API performance dashboard | 🟠 | 1h | 3.4.2.1 | API dashboard |
| 3.4.2.3 | Create database dashboard | 🟠 | 1h | 3.4.2.1 | DB dashboard |
| 3.4.2.4 | Create AI agent dashboard | 🟠 | 1h | 3.4.2.1 | AI dashboard |
| 3.4.2.5 | Create RAG metrics dashboard | 🟡 | 1h | 3.4.2.1 | RAG dashboard |
| 3.4.2.6 | Create business metrics dashboard | 🟡 | 1h | 3.4.2.1 | Business dashboard |
| 3.4.2.7 | Export dashboards as code | 🟠 | 0.5h | 3.4.2.2 | Dashboard as code |
| **3.4.3** | **Alerting Rules** | 🔴 | 5h | 3.4.1 | Alerts |
| 3.4.3.1 | Configure Alertmanager | 🔴 | 0.5h | - | Alertmanager |
| 3.4.3.2 | Add high error rate alert | 🔴 | 0.5h | 3.4.3.1 | Error alert |
| 3.4.3.3 | Add high latency alert (p95 > 1s) | 🔴 | 0.5h | 3.4.3.1 | Latency alert |
| 3.4.3.4 | Add database connection alert | 🔴 | 0.5h | 3.4.3.1 | DB alert |
| 3.4.3.5 | Add service down alert | 🔴 | 0.5h | 3.4.3.1 | Uptime alert |
| 3.4.3.6 | Add disk space alert | 🟠 | 0.5h | 3.4.3.1 | Disk alert |
| 3.4.3.7 | Add Claude API quota alert | 🟠 | 0.5h | 3.4.3.1 | Quota alert |
| 3.4.3.8 | Configure Slack integration | 🟠 | 0.5h | 3.4.3.1 | Slack alerts |
| 3.4.3.9 | Configure PagerDuty (future) | 🟡 | 0.5h | 3.4.3.1 | PagerDuty |
| 3.4.3.10 | Test alert routing | 🔴 | 0.5h | 3.4.3.8 | Alert testing |
| **3.4.4** | **Log Aggregation** | 🟡 | 4h | None | Centralized logs |
| 3.4.4.1 | Set up Loki for log aggregation | 🟡 | 1h | - | Loki setup |
| 3.4.4.2 | Configure Promtail log shipping | 🟡 | 0.5h | 3.4.4.1 | Log shipping |
| 3.4.4.3 | Create log exploration dashboard | 🟡 | 1h | 3.4.4.1 | Log dashboard |
| 3.4.4.4 | Set up log-based alerts | 🟡 | 0.5h | 3.4.4.1 | Log alerts |
| 3.4.4.5 | Configure log retention | 🟡 | 0.5h | 3.4.4.1 | Log retention |
| 3.4.4.6 | Add request trace correlation | 🟡 | 0.5h | 3.4.4.2 | Trace correlation |

**Phase 3 Completion Checklist:**
```
□ API versioned at /api/v1/
□ Comprehensive API documentation
□ Database indexes optimized
□ Backup/restore tested
□ Dependency injection implemented
□ Circuit breakers for external APIs
□ Prometheus metrics collection
□ Grafana dashboards operational
□ Alerting configured and tested
```

---

# PHASE 4: Features & Polish (Weeks 13-16)

## Sprint 4.1: Custom Claude Skills (Week 13)

### Overview
Create custom Claude Skills specifically for Money Flow to enhance AI capabilities.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **4.1.1** | **Financial Analysis Skill** | 🟠 | 6h | None | Analysis skill |
| 4.1.1.1 | Create SKILL.md structure | 🟠 | 0.5h | - | Skill structure |
| 4.1.1.2 | Define spending analysis patterns | 🟠 | 1h | 4.1.1.1 | Analysis patterns |
| 4.1.1.3 | Add budget comparison logic | 🟠 | 1h | 4.1.1.2 | Budget comparison |
| 4.1.1.4 | Add trend detection instructions | 🟠 | 1h | 4.1.1.2 | Trend detection |
| 4.1.1.5 | Add anomaly detection patterns | 🟡 | 1h | 4.1.1.2 | Anomaly detection |
| 4.1.1.6 | Create example prompts and outputs | 🟠 | 0.5h | 4.1.1.2 | Examples |
| 4.1.1.7 | Test skill integration | 🟠 | 1h | 4.1.1.5 | Integration test |
| **4.1.2** | **Payment Reminder Skill** | 🟡 | 4h | None | Reminder skill |
| 4.1.2.1 | Create reminder generation patterns | 🟡 | 1h | - | Reminder patterns |
| 4.1.2.2 | Add urgency level classification | 🟡 | 0.75h | 4.1.2.1 | Urgency levels |
| 4.1.2.3 | Add personalization rules | 🟡 | 0.75h | 4.1.2.1 | Personalization |
| 4.1.2.4 | Add multi-channel format templates | 🟡 | 0.75h | 4.1.2.1 | Format templates |
| 4.1.2.5 | Create notification scheduling logic | 🟡 | 0.75h | 4.1.2.2 | Scheduling |
| **4.1.3** | **Debt Management Skill** | 🟠 | 5h | None | Debt skill |
| 4.1.3.1 | Create debt payoff strategy patterns | 🟠 | 1h | - | Payoff strategies |
| 4.1.3.2 | Add avalanche vs snowball comparison | 🟠 | 1h | 4.1.3.1 | Method comparison |
| 4.1.3.3 | Add interest calculation helpers | 🟠 | 1h | 4.1.3.1 | Interest calc |
| 4.1.3.4 | Add debt-free date projection | 🟠 | 1h | 4.1.3.2 | Date projection |
| 4.1.3.5 | Create motivational response patterns | 🟡 | 0.5h | 4.1.3.1 | Motivation |
| 4.1.3.6 | Test with various debt scenarios | 🟠 | 0.5h | 4.1.3.4 | Scenario testing |
| **4.1.4** | **Savings Goal Skill** | 🟡 | 4h | None | Savings skill |
| 4.1.4.1 | Create goal tracking patterns | 🟡 | 1h | - | Goal tracking |
| 4.1.4.2 | Add milestone celebration messages | 🟡 | 0.5h | 4.1.4.1 | Milestones |
| 4.1.4.3 | Add contribution recommendation logic | 🟡 | 1h | 4.1.4.1 | Recommendations |
| 4.1.4.4 | Add goal achievement projection | 🟡 | 1h | 4.1.4.1 | Projections |
| 4.1.4.5 | Create progress visualization prompts | 🟡 | 0.5h | 4.1.4.1 | Visualizations |
| **4.1.5** | **Skill Testing & Documentation** | 🟠 | 4h | 4.1.1-4.1.4 | Skill docs |
| 4.1.5.1 | Create skill test suite | 🟠 | 1h | - | Test suite |
| 4.1.5.2 | Test skill composition (multiple skills) | 🟠 | 1h | 4.1.5.1 | Composition test |
| 4.1.5.3 | Document skill usage | 🟠 | 1h | - | Usage docs |
| 4.1.5.4 | Create skill showcase demo | 🟡 | 0.5h | 4.1.5.3 | Demo |
| 4.1.5.5 | Package skills for distribution | 🟡 | 0.5h | 4.1.5.3 | Package |

**Custom Skills File Structure:**
```
money-flow-skills/
├── financial-analysis/
│   ├── SKILL.md
│   ├── examples/
│   └── scripts/
├── payment-reminder/
│   ├── SKILL.md
│   └── templates/
├── debt-management/
│   ├── SKILL.md
│   └── calculators/
└── savings-goal/
    ├── SKILL.md
    └── projections/
```

---

## Sprint 4.2: Frontend Enhancements (Week 14)

### Overview
Polish the frontend with improved UX, accessibility, and mobile responsiveness.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **4.2.1** | **Mobile Responsiveness** | 🟠 | 6h | None | Mobile UI |
| 4.2.1.1 | Audit current mobile breakpoints | 🟠 | 0.5h | - | Breakpoint audit |
| 4.2.1.2 | Fix subscription list mobile layout | 🟠 | 1h | 4.2.1.1 | List responsive |
| 4.2.1.3 | Fix calendar mobile layout | 🟠 | 1h | 4.2.1.1 | Calendar responsive |
| 4.2.1.4 | Fix cards dashboard mobile layout | 🟠 | 1h | 4.2.1.1 | Cards responsive |
| 4.2.1.5 | Fix agent chat mobile layout | 🟠 | 1h | 4.2.1.1 | Chat responsive |
| 4.2.1.6 | Add mobile navigation drawer | 🟠 | 1h | 4.2.1.1 | Nav drawer |
| 4.2.1.7 | Test on various device sizes | 🟠 | 0.5h | 4.2.1.2 | Device testing |
| **4.2.2** | **Accessibility (a11y)** | 🟠 | 5h | None | Accessible UI |
| 4.2.2.1 | Add ARIA labels to all interactive elements | 🟠 | 1h | - | ARIA labels |
| 4.2.2.2 | Ensure keyboard navigation | 🟠 | 1h | 4.2.2.1 | Keyboard nav |
| 4.2.2.3 | Add focus indicators | 🟠 | 0.5h | 4.2.2.2 | Focus states |
| 4.2.2.4 | Check color contrast ratios | 🟠 | 0.5h | - | Contrast check |
| 4.2.2.5 | Add screen reader announcements | 🟡 | 1h | 4.2.2.1 | SR support |
| 4.2.2.6 | Run axe-core accessibility audit | 🟠 | 0.5h | 4.2.2.1 | a11y audit |
| 4.2.2.7 | Fix audit findings | 🟠 | 0.5h | 4.2.2.6 | Fix issues |
| **4.2.3** | **UX Improvements** | 🟡 | 6h | None | Better UX |
| 4.2.3.1 | Add loading skeletons | 🟡 | 1h | - | Skeletons |
| 4.2.3.2 | Add optimistic updates | 🟡 | 1.5h | - | Optimistic UI |
| 4.2.3.3 | Add pull-to-refresh (mobile) | 🟡 | 0.5h | - | Pull refresh |
| 4.2.3.4 | Add keyboard shortcuts | 🟡 | 1h | - | Shortcuts |
| 4.2.3.5 | Add toast notifications | 🟡 | 0.5h | - | Toasts |
| 4.2.3.6 | Add confirmation dialogs for destructive actions | 🟠 | 0.5h | - | Confirmations |
| 4.2.3.7 | Add empty state illustrations | 🟡 | 0.5h | - | Empty states |
| 4.2.3.8 | Add onboarding tour | 🟡 | 0.5h | - | Onboarding |
| **4.2.4** | **Dark Mode** | 🟡 | 4h | None | Dark theme |
| 4.2.4.1 | Create dark color palette with OKLCH | 🟡 | 1h | - | Dark palette |
| 4.2.4.2 | Add theme toggle component | 🟡 | 0.5h | 4.2.4.1 | Toggle |
| 4.2.4.3 | Update all components for dark mode | 🟡 | 1.5h | 4.2.4.1 | Component updates |
| 4.2.4.4 | Add system preference detection | 🟡 | 0.5h | 4.2.4.2 | System pref |
| 4.2.4.5 | Persist theme preference | 🟡 | 0.5h | 4.2.4.2 | Persistence |

---

## Sprint 4.3: Advanced Features (Week 15)

### Overview
Implement advanced features from the roadmap.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **4.3.1** | **Payment Reminders** | 🟠 | 8h | None | Reminders |
| 4.3.1.1 | Create reminder settings model | 🟠 | 1h | - | Reminder model |
| 4.3.1.2 | Add reminder preferences API | 🟠 | 1h | 4.3.1.1 | Reminder API |
| 4.3.1.3 | Create reminder scheduling service | 🟠 | 2h | 4.3.1.2 | Scheduler |
| 4.3.1.4 | Add email reminder template | 🟠 | 1h | 4.3.1.3 | Email template |
| 4.3.1.5 | Add push notification support (future) | 🟡 | 1h | 4.3.1.3 | Push prep |
| 4.3.1.6 | Create reminder settings UI | 🟠 | 1h | 4.3.1.2 | Settings UI |
| 4.3.1.7 | Test reminder delivery | 🟠 | 1h | 4.3.1.4 | Delivery test |
| **4.3.2** | **Budget Alerts** | 🟡 | 6h | None | Budgets |
| 4.3.2.1 | Create budget model | 🟡 | 1h | - | Budget model |
| 4.3.2.2 | Add budget CRUD API | 🟡 | 1h | 4.3.2.1 | Budget API |
| 4.3.2.3 | Create budget tracking service | 🟡 | 1.5h | 4.3.2.2 | Tracking service |
| 4.3.2.4 | Add budget alert generation | 🟡 | 1h | 4.3.2.3 | Alert generation |
| 4.3.2.5 | Create budget UI component | 🟡 | 1h | 4.3.2.2 | Budget UI |
| 4.3.2.6 | Add budget vs actual chart | 🟡 | 0.5h | 4.3.2.5 | Budget chart |
| **4.3.3** | **Subscription Templates** | 🟡 | 5h | None | Templates |
| 4.3.3.1 | Create template data structure | 🟡 | 0.5h | - | Template model |
| 4.3.3.2 | Create popular services template library | 🟡 | 1.5h | 4.3.3.1 | Template library |
| 4.3.3.3 | Add template search API | 🟡 | 1h | 4.3.3.2 | Search API |
| 4.3.3.4 | Add template suggestions in add modal | 🟡 | 1h | 4.3.3.3 | Suggestions UI |
| 4.3.3.5 | Auto-fill from template selection | 🟡 | 1h | 4.3.3.4 | Auto-fill |
| **4.3.4** | **Insights Dashboard** | 🟡 | 6h | None | Insights |
| 4.3.4.1 | Create insights page component | 🟡 | 1h | - | Insights page |
| 4.3.4.2 | Add spending by category chart | 🟡 | 1h | 4.3.4.1 | Category chart |
| 4.3.4.3 | Add spending trend chart | 🟡 | 1h | 4.3.4.1 | Trend chart |
| 4.3.4.4 | Add upcoming payments forecast | 🟡 | 1h | 4.3.4.1 | Forecast |
| 4.3.4.5 | Add debt payoff projection | 🟡 | 1h | 4.3.4.1 | Debt projection |
| 4.3.4.6 | Add savings goal progress | 🟡 | 1h | 4.3.4.1 | Savings progress |

---

## Sprint 4.4: Documentation & Launch Prep (Week 16)

### Overview
Final documentation, testing, and production launch preparation.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **4.4.1** | **User Documentation** | 🟠 | 5h | None | User docs |
| 4.4.1.1 | Create user guide | 🟠 | 1.5h | - | User guide |
| 4.4.1.2 | Create FAQ document | 🟠 | 1h | - | FAQ |
| 4.4.1.3 | Create video tutorials (scripts) | 🟡 | 1h | 4.4.1.1 | Video scripts |
| 4.4.1.4 | Create feature walkthrough | 🟠 | 1h | 4.4.1.1 | Walkthrough |
| 4.4.1.5 | Create troubleshooting guide | 🟠 | 0.5h | - | Troubleshooting |
| **4.4.2** | **Developer Documentation Update** | 🟠 | 4h | All sprints | Dev docs |
| 4.4.2.1 | Update architecture documentation | 🟠 | 1h | - | Architecture docs |
| 4.4.2.2 | Update API documentation | 🟠 | 1h | - | API docs |
| 4.4.2.3 | Create deployment runbook | 🔴 | 1h | - | Runbook |
| 4.4.2.4 | Create incident response playbook | 🟠 | 0.5h | - | Playbook |
| 4.4.2.5 | Update README with all new features | 🟠 | 0.5h | - | README |
| **4.4.3** | **Security Audit** | 🔴 | 4h | All sprints | Security |
| 4.4.3.1 | Run OWASP ZAP scan | 🔴 | 1h | - | OWASP scan |
| 4.4.3.2 | Run dependency vulnerability scan | 🔴 | 0.5h | - | Dep scan |
| 4.4.3.3 | Review authentication implementation | 🔴 | 0.5h | - | Auth review |
| 4.4.3.4 | Review data encryption | 🔴 | 0.5h | - | Encryption review |
| 4.4.3.5 | Fix critical findings | 🔴 | 1h | 4.4.3.1 | Fix criticals |
| 4.4.3.6 | Document security posture | 🟠 | 0.5h | 4.4.3.5 | Security docs |
| **4.4.4** | **Production Launch Checklist** | 🔴 | 6h | All sprints | Launch ready |
| 4.4.4.1 | Final staging environment test | 🔴 | 1h | - | Staging test |
| 4.4.4.2 | Verify all environment variables | 🔴 | 0.5h | - | Env check |
| 4.4.4.3 | Verify database migrations | 🔴 | 0.5h | - | Migration check |
| 4.4.4.4 | Verify backup/restore | 🔴 | 0.5h | - | Backup check |
| 4.4.4.5 | Verify monitoring/alerting | 🔴 | 0.5h | - | Monitoring check |
| 4.4.4.6 | Load test production config | 🔴 | 1h | - | Load test |
| 4.4.4.7 | Create rollback plan | 🔴 | 0.5h | - | Rollback plan |
| 4.4.4.8 | Production deployment | 🔴 | 1h | 4.4.4.1-4.4.4.7 | Go live |
| 4.4.4.9 | Post-deployment verification | 🔴 | 0.5h | 4.4.4.8 | Verification |

**Phase 4 & Final Completion Checklist:**
```
□ Custom Claude Skills deployed
□ Mobile responsive design complete
□ Accessibility audit passed
□ Dark mode implemented
□ Payment reminders functional
□ User documentation complete
□ Security audit passed
□ Production deployment successful
□ Monitoring verified
□ Rollback plan tested
```

---

# Summary Tables

## Master Timeline

| Week | Sprint | Focus | Key Deliverables |
|------|--------|-------|------------------|
| 1 | 1.1 | Authentication | User auth, JWT, protected routes |
| 2 | 1.2 | Security | Rate limiting, prompt protection, CORS |
| 3 | 1.3 | CI/CD | GitHub Actions, automated tests, deploy |
| 4 | 1.4 | Observability | Logging, Sentry, health checks |
| 5 | 2.1 | E2E Testing | Playwright setup, auth/CRUD tests |
| 6 | 2.2 | Bug Fixes | Endpoint fixes, AI agent tests |
| 7 | 2.3 | Integration | Contract tests, DB/Redis/Qdrant tests |
| 8 | 2.4 | Performance | Load testing, query optimization |
| 9 | 3.1 | API Versioning | /api/v1/, OpenAPI docs |
| 10 | 3.2 | Database | Indexes, backups, connection pool |
| 11 | 3.3 | Architecture | DI, error handling, resilience |
| 12 | 3.4 | Monitoring | Prometheus, Grafana, alerting |
| 13 | 4.1 | Custom Skills | Financial analysis, debt, savings |
| 14 | 4.2 | Frontend | Mobile, a11y, dark mode |
| 15 | 4.3 | Features | Reminders, budgets, templates |
| 16 | 4.4 | Launch | Docs, security audit, go-live |

## Effort Distribution

| Phase | Hours | Percentage |
|-------|-------|------------|
| Phase 1: Foundation & Security | ~100h | 25% |
| Phase 2: Quality & Testing | ~95h | 24% |
| Phase 3: Architecture & Performance | ~105h | 26% |
| Phase 4: Features & Polish | ~100h | 25% |
| **Total (Main Roadmap)** | **~400h** | **100%** |
| **Future: Settings & AI Features** | **~240h** | *(see [Settings Roadmap](../SETTINGS_ROADMAP.md))* |

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Claude API breaking changes | Medium | High | Version pin, fallback regex |
| Database migration failures | Low | Critical | Test migrations, backup before |
| Security vulnerability discovered | Medium | Critical | Regular scans, quick patches |
| Performance degradation | Medium | High | Load testing, monitoring |
| Scope creep | High | Medium | Strict sprint boundaries |
| Third-party service outages | Low | Medium | Circuit breakers, fallbacks |

## Dependencies Graph

```
Phase 1 (Foundation)
    └── Sprint 1.1 (Auth) ──────────────────────┐
         └── Sprint 1.2 (Security) ────────────┐│
              └── Sprint 1.3 (CI/CD) ──────────┐││
                   └── Sprint 1.4 (Observability) ││
                        │                        ││
Phase 2 (Quality)       │                        ││
    └── Sprint 2.1 (E2E) ◄───────────────────────┤│
         └── Sprint 2.2 (Bug Fixes) ◄────────────┤│
              └── Sprint 2.3 (Integration) ◄─────┤│
                   └── Sprint 2.4 (Performance)  ││
                        │                        ││
Phase 3 (Architecture)  │                        ││
    └── Sprint 3.1 (API) ◄───────────────────────┤│
         └── Sprint 3.2 (Database) ◄─────────────┤│
              └── Sprint 3.3 (Services) ◄────────┘│
                   └── Sprint 3.4 (Monitoring)    │
                        │                         │
Phase 4 (Features)      │                         │
    └── Sprint 4.1 (Skills) ◄─────────────────────┘
         └── Sprint 4.2 (Frontend)
              └── Sprint 4.3 (Features)
                   └── Sprint 4.4 (Launch) ──► 🚀
```

---

## Quick Start Commands

### Phase 1 Setup
```bash
# Week 1: Auth setup
pip install passlib[bcrypt] python-jose

# Week 2: Security
pip install slowapi

# Week 3: CI/CD
# Create .github/workflows/ci.yml

# Week 4: Logging
pip install structlog sentry-sdk[fastapi]
```

### Phase 2 Setup
```bash
# Week 5: E2E
npm install -D @playwright/test
npx playwright install

# Week 8: Performance
pip install locust
```

### Phase 3 Setup
```bash
# Week 11: DI
pip install dependency-injector

# Week 12: Monitoring
# Add prometheus + grafana to docker-compose.yml
```

---

**Document Version**: 1.1.0
**Created**: December 13, 2025
**Updated**: December 15, 2025
**Total Tasks**: 250+
**Total Sub-tasks**: 400+

---

# FUTURE FEATURES: Settings & AI-Powered Features

> **Detailed Plan**: See [Settings Roadmap](../SETTINGS_ROADMAP.md) for comprehensive feature specifications.

## Overview

After completing Phase 4, the next major feature set focuses on user settings, AI-powered features, and third-party integrations.

### Settings Page (10 Tabs)

| Tab | Purpose | Priority | Effort |
|-----|---------|----------|--------|
| **Profile** | User info, password, 2FA | P1 | 8h |
| **Preferences** | Display settings, defaults | P1 | 8h |
| **Payment Cards** | Card management (exists, enhance) | P1 | 6h |
| **Categories** | Custom categories, budgets | P1 | 10h |
| **Notifications** | Reminders, channels, reports | P2 | 12h |
| **Icons & Branding** | Icon library, AI generation | P2 | 15h |
| **AI Assistant** | NL preferences, smart features | P2 | 8h |
| **Data Import** | Bank statements, email scanning | P2 | 30h |
| **Data Export** | PDF reports, scheduled backups | P2 | 12h |
| **Integrations** | Calendar, webhooks, Open Banking | P3 | 40h |

### AI-Powered Features

| Feature | Description | Effort |
|---------|-------------|--------|
| **Bank Statement Import** | AI extracts recurring payments from PDF/CSV | 30h |
| **Email Receipt Scanning** | Scan Gmail/Outlook for subscriptions | 20h |
| **Icon Intelligence** | Auto-fetch from APIs + AI generation | 15h |
| **Smart Suggestions** | Spending insights, savings opportunities | 12h |

### Implementation Timeline

| Phase | Focus | Duration | Total Effort |
|-------|-------|----------|--------------|
| Settings Phase 1 | Profile + Preferences | 2 weeks | ~28h |
| Settings Phase 2 | Cards + Categories | 2 weeks | ~26h |
| Settings Phase 3 | Notifications + Export | 2 weeks | ~28h |
| Settings Phase 4 | Icons + AI Settings | 2 weeks | ~27h |
| Settings Phase 5 | Smart Import (AI) | 3 weeks | ~46h |
| Settings Phase 6 | Integrations | 3 weeks | ~40h |
| Settings Phase 7 | Open Banking | 4 weeks | ~46h |

**Total Estimated Effort**: ~240 hours (additional to main roadmap)

### Key Database Changes

```sql
-- New tables required
CREATE TABLE categories (user_id, name, color, icon, budget_amount);
CREATE TABLE icon_cache (service_name, icon_url, brand_color, source);
CREATE TABLE webhook_subscriptions (user_id, url, events[], secret);

-- User preferences enhancement
ALTER TABLE users ADD COLUMN notification_preferences JSONB;
```

### Key API Endpoints

```
Settings APIs:
- PATCH /api/auth/profile
- POST /api/auth/change-password
- GET/PUT /api/users/preferences

Category APIs:
- GET/POST/PUT/DELETE /api/categories
- POST /api/categories/merge

Icon APIs:
- GET /api/icons/search
- GET /api/icons/service/{name}
- POST /api/icons/generate (AI)

Import APIs:
- POST /api/import/bank-statement
- GET /api/import/bank-statement/{job_id}

Integration APIs:
- GET/POST/DELETE /api/webhooks
- GET /api/calendar/ical
- POST /api/calendar/sync/google
```

---

*This master plan is a living document. Update status and adjust timelines as the project progresses.*
