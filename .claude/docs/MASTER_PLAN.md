# Money Flow - Master Development Plan

> **Comprehensive Roadmap for Production-Ready Enhancement**
>
> **Version**: 2.1.0
> **Created**: December 13, 2025
> **Updated**: December 18, 2025
> **Project**: Money Flow (Subscription Tracker)
> **Total Duration**: 36 Weeks (6 Phases)
> **Estimated Effort**: ~655 hours (400 base + 240 Settings + 15 Launch)

---

## Executive Summary

This master plan transforms Money Flow from a well-architected personal project into a production-ready, secure, and scalable application. The plan is organized into 6 phases across 36 weeks, with each phase building upon the previous.

### Phase Overview

| Phase | Name | Duration | Focus Areas |
|-------|------|----------|-------------|
| **Phase 1** | Foundation & Security | Weeks 1-4 | Auth, Security Hardening, CI/CD |
| **Phase 2** | Quality & Testing | Weeks 5-8 | E2E Tests, Bug Fixes, Monitoring |
| **Phase 3** | Architecture & Performance | Weeks 9-12 | Scalability, Caching, API Versioning |
| **Phase 4** | Features & Polish | Weeks 13-16 | Custom Skills, Telegram, Documentation |
| **Phase 5** | Settings & AI Features | Weeks 17-34 | Settings UI, AI Import, Integrations |
| **Phase 6** | Production Launch | Weeks 35-36 | Final deploy, verification, go-live |

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

### All Sprints Overview

| Phase | Sprint | Name | Week(s) | Hours | Status |
|-------|--------|------|---------|-------|--------|
| **1** | 1.1 | Authentication System | 1 | 20h | ✅ Complete |
| **1** | 1.2 | Security Hardening | 2 | 25h | ✅ Complete |
| **1** | 1.3 | CI/CD Pipeline | 3 | 25h | ✅ Complete |
| **1** | 1.4 | Logging & Observability | 4 | 30h | ✅ Complete |
| **2** | 2.1 | E2E Testing Framework | 5 | 25h | ✅ Complete |
| **2** | 2.2 | AI Agent E2E & Bug Fixes | 6 | 25h | ✅ Complete |
| **2** | 2.3 | Integration & Contract Tests | 7 | 25h | ✅ Complete |
| **2** | 2.4 | Performance & Load Testing | 8 | 25h | ✅ Complete |
| **3** | 3.1 | API Versioning & Docs | 9 | 20h | ✅ Complete |
| **3** | 3.2 | Database Scalability | 10 | 25h | ✅ Complete |
| **3** | 3.3 | Service Architecture | 11 | 25h | ✅ Complete |
| **3** | 3.4 | Monitoring & Alerting | 12 | 25h | ✅ Complete |
| **4** | 4.1 | Custom Claude Skills | 13 | 25h | ✅ Complete |
| **4** | 4.2 | Frontend Enhancements | 14 | 25h | ✅ Complete |
| **4** | 4.3 | Payment Reminders & Telegram | 15 | 30h | ✅ Complete |
| **4** | 4.4 | Documentation & Launch | 16 | 20h | ✅ Complete |
| **5** | 5.1 | Profile & Preferences | 17-18 | 28h | ✅ Complete |
| **5** | 5.2 | Cards & Categories | 19-20 | 26h | ✅ Complete |
| **5** | 5.3 | Notifications & Export | 21-22 | 28h | ✅ Complete |
| **5** | 5.4 | Icons & AI Settings | 23-24 | 27h | ✅ Complete |
| **5** | 5.5 | Smart Import (AI) | 25-27 | 46h | 🔜 Not Started |
| **5** | 5.6 | Integrations | 28-30 | 40h | 🔜 Not Started |
| **5** | 5.7 | Open Banking | 31-34 | 46h | 🔜 Not Started |
| **6** | 6.1 | Production Launch | 35-36 | 15h | 🔜 Not Started |

**Phase Totals:**
- Phase 1: ~100h ✅
- Phase 2: ~100h ✅
- Phase 3: ~95h ✅
- Phase 4: ~100h ✅
- Phase 5: ~241h 🔜
- Phase 6: ~15h 🔜

**Grand Total: ~639 hours**

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
| **2.3.3** | **Redis Integration Tests** | ✅ | 3h | None | Redis tests |
| 2.3.3.1 | Test embedding cache operations | ✅ | 0.75h | - | Cache tests |
| 2.3.3.2 | Test rate limiter storage | ✅ | 0.75h | - | Rate limit tests |
| 2.3.3.3 | Test token blacklist | ✅ | 0.5h | - | Blacklist tests |
| 2.3.3.4 | Test cache expiration | ✅ | 0.5h | 2.3.3.1 | TTL tests |
| 2.3.3.5 | Test Redis connection failure handling | ✅ | 0.5h | - | Failure tests |
| **2.3.4** | **Qdrant Integration Tests** | ✅ | 4h | None | Vector DB tests |
| 2.3.4.1 | Test vector insertion | ✅ | 0.75h | - | Insert tests |
| 2.3.4.2 | Test similarity search | ✅ | 1h | 2.3.4.1 | Search tests |
| 2.3.4.3 | Test filtering by user_id | ✅ | 0.5h | 2.3.4.2 | Filter tests |
| 2.3.4.4 | Test collection management | ✅ | 0.5h | - | Collection tests |
| 2.3.4.5 | Test Qdrant connection failure handling | ✅ | 0.5h | - | Failure tests |
| 2.3.4.6 | Test embedding update operations | ✅ | 0.75h | 2.3.4.1 | Update tests |
| **2.3.5** | **Claude API Integration Tests** | ✅ | 3h | None | AI tests |
| 2.3.5.1 | Test API connection and auth | ✅ | 0.5h | - | Connection test |
| 2.3.5.2 | Test intent classification accuracy | ✅ | 1h | 2.3.5.1 | Classification tests |
| 2.3.5.3 | Test entity extraction accuracy | ✅ | 1h | 2.3.5.1 | Extraction tests |
| 2.3.5.4 | Test API failure fallback (regex) | ✅ | 0.5h | - | Fallback test |

---

## Sprint 2.4: Performance & Load Testing (Week 8)

### Overview
Performance benchmarking and load testing to ensure scalability.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **2.4.1** | **Performance Benchmarking** | ✅ | 5h | None | Benchmarks |
| 2.4.1.1 | Set up Locust for load testing | ✅ | 1h | - | Locust setup |
| 2.4.1.2 | Create benchmark scenarios | ✅ | 1h | 2.4.1.1 | Test scenarios |
| 2.4.1.3 | Benchmark GET /subscriptions | ✅ | 0.5h | 2.4.1.2 | List benchmark |
| 2.4.1.4 | Benchmark POST /subscriptions | ✅ | 0.5h | 2.4.1.2 | Create benchmark |
| 2.4.1.5 | Benchmark /api/agent/execute | ✅ | 0.5h | 2.4.1.2 | Agent benchmark |
| 2.4.1.6 | Benchmark /api/search/notes | ✅ | 0.5h | 2.4.1.2 | Search benchmark |
| 2.4.1.7 | Generate baseline performance report | ✅ | 1h | 2.4.1.3 | Baseline report |
| **2.4.2** | **Load Testing** | ✅ | 4h | 2.4.1 | Load tests |
| 2.4.2.1 | Test 10 concurrent users | ✅ | 0.5h | - | 10 users test |
| 2.4.2.2 | Test 50 concurrent users | ✅ | 0.5h | 2.4.2.1 | 50 users test |
| 2.4.2.3 | Test 100 concurrent users | ✅ | 0.5h | 2.4.2.2 | 100 users test |
| 2.4.2.4 | Test sustained load (1 hour) | ✅ | 1h | 2.4.2.1 | Soak test |
| 2.4.2.5 | Test spike load handling | ✅ | 0.5h | 2.4.2.1 | Spike test |
| 2.4.2.6 | Document performance limits | ✅ | 1h | 2.4.2.3 | Limits doc |
| **2.4.3** | **Database Query Optimization** | ✅ | 5h | 2.4.2 | Query optimization |
| 2.4.3.1 | Add EXPLAIN ANALYZE for slow queries | ✅ | 1h | - | Query analysis |
| 2.4.3.2 | Add missing indexes | ✅ | 1h | 2.4.3.1 | Index creation |
| 2.4.3.3 | Optimize N+1 queries | ✅ | 1h | 2.4.3.1 | N+1 fix |
| 2.4.3.4 | Add connection pooling config | ✅ | 1h | - | Pool config |
| 2.4.3.5 | Test query performance improvements | ✅ | 1h | 2.4.3.2 | Performance test |
| **2.4.4** | **Caching Strategy** | ✅ | 4h | None | Caching |
| 2.4.4.1 | Implement response caching for list endpoints | ✅ | 1h | - | List caching |
| 2.4.4.2 | Add cache invalidation on mutations | ✅ | 1h | 2.4.4.1 | Invalidation |
| 2.4.4.3 | Cache summary calculations | ✅ | 1h | - | Summary caching |
| 2.4.4.4 | Monitor cache hit rates | ✅ | 0.5h | 2.4.4.1 | Hit rate tracking |
| 2.4.4.5 | Document caching strategy | ✅ | 0.5h | 2.4.4.3 | Cache docs |

**Phase 2 Completion Checklist:**
```
✅ 50+ E2E tests passing (Sprint 2.1)
✅ All endpoint bugs fixed (Sprint 2.2)
✅ User data isolation implemented (Sprint 2.2)
✅ Settings roadmap planned (Sprint 2.2)
✅ API contract tests in CI (Sprint 2.3.1)
✅ Database integration tests (Sprint 2.3.2) - 33 tests
✅ Redis integration tests (Sprint 2.3.3) - 39 tests
✅ Qdrant integration tests (Sprint 2.3.4) - 42 tests
✅ Claude API integration tests (Sprint 2.3.5) - 45 tests
✅ Performance baseline documented (Sprint 2.4.1)
✅ Load test results documented (Sprint 2.4.2)
✅ Database queries optimized (Sprint 2.4.3) - 7 composite indexes
✅ Caching strategy implemented (Sprint 2.4.4) - ResponseCache module
```

---

# PHASE 3: Architecture & Performance (Weeks 9-12)

## Sprint 3.1: API Versioning & Documentation (Week 9)

### Overview
Implement API versioning for backward compatibility and comprehensive documentation.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **3.1.1** | **API Versioning** | ✅ | 6h | None | Versioned API |
| 3.1.1.1 | Create /api/v1/ prefix structure | ✅ | 1h | - | URL structure |
| 3.1.1.2 | Move all existing routes to v1 | ✅ | 2h | 3.1.1.1 | Route migration |
| 3.1.1.3 | Update frontend API calls | ✅ | 1.5h | 3.1.1.2 | Frontend update |
| 3.1.1.4 | Add version header support | ✅ | 0.5h | 3.1.1.1 | Header versioning |
| 3.1.1.5 | Add deprecation warning middleware | ✅ | 0.5h | 3.1.1.2 | Deprecation support |
| 3.1.1.6 | Document versioning policy | ✅ | 0.5h | 3.1.1.2 | Version docs |
| **3.1.2** | **OpenAPI Enhancement** | ✅ | 5h | 3.1.1 | Better docs |
| 3.1.2.1 | Add detailed endpoint descriptions | ✅ | 1h | - | Descriptions |
| 3.1.2.2 | Add request/response examples | ✅ | 1.5h | 3.1.2.1 | Examples |
| 3.1.2.3 | Add error response documentation | ✅ | 0.5h | 3.1.2.1 | Error docs |
| 3.1.2.4 | Add authentication documentation | ✅ | 0.5h | - | Auth docs |
| 3.1.2.5 | Group endpoints by tags | ✅ | 0.5h | 3.1.2.1 | Tag grouping |
| 3.1.2.6 | Export and version OpenAPI spec | ✅ | 1h | 3.1.2.2 | Spec versioning |
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

## Sprint 3.3: Service Architecture Improvements (Week 11) ✅ COMPLETE

### Overview
Improve service architecture with dependency injection, proper error handling, and resilience patterns.

**Status: ✅ COMPLETE** (December 16, 2025)

**Completed:**
- Dependency injection with `dependency-injector` library
- Service container with Singleton, Factory, and Resource providers
- Custom exception hierarchy in `src/core/exceptions.py`
- Global exception handler with error codes and messages
- Resilience patterns with circuit breaker, retry, and timeout
- ARQ async task queue with Redis
- Unit tests for container, exceptions, resilience, and tasks (455 tests total)

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **3.3.1** | **Dependency Injection** | ✅ | 5h | None | DI pattern |
| 3.3.1.1 | Install dependency-injector | ✅ | 0.5h | - | DI library |
| 3.3.1.2 | Create service container | ✅ | 1h | 3.3.1.1 | Container |
| 3.3.1.3 | Refactor services to use DI | ✅ | 2h | 3.3.1.2 | Service refactor |
| 3.3.1.4 | Create factory providers | ✅ | 0.5h | 3.3.1.2 | Factories |
| 3.3.1.5 | Add singleton providers for expensive resources | ✅ | 0.5h | 3.3.1.2 | Singletons |
| 3.3.1.6 | Update tests to use test container | ✅ | 0.5h | 3.3.1.3 | Test updates |
| **3.3.2** | **Error Handling Standardization** | ✅ | 5h | None | Error handling |
| 3.3.2.1 | Create custom exception hierarchy | ✅ | 1h | - | Exceptions |
| 3.3.2.2 | Create global exception handler | ✅ | 1h | 3.3.2.1 | Handler |
| 3.3.2.3 | Add validation error formatting | ✅ | 0.5h | 3.3.2.2 | Validation errors |
| 3.3.2.4 | Add database error handling | ✅ | 0.5h | 3.3.2.2 | DB errors |
| 3.3.2.5 | Add external API error handling | ✅ | 0.5h | 3.3.2.2 | API errors |
| 3.3.2.6 | Add error codes and messages catalog | ✅ | 1h | 3.3.2.1 | Error catalog |
| 3.3.2.7 | Update frontend error handling | ✅ | 0.5h | 3.3.2.6 | Frontend errors |
| **3.3.3** | **Resilience Patterns** | ✅ | 6h | None | Resilience |
| 3.3.3.1 | Add circuit breaker for Claude API | ✅ | 1h | - | Circuit breaker |
| 3.3.3.2 | Add retry with exponential backoff | ✅ | 1h | 3.3.3.1 | Retry logic |
| 3.3.3.3 | Add timeout configuration | ✅ | 0.5h | - | Timeouts |
| 3.3.3.4 | Add bulkhead pattern for AI requests | ✅ | 1h | 3.3.3.1 | Bulkhead |
| 3.3.3.5 | Add fallback for degraded mode | ✅ | 1h | 3.3.3.1 | Fallback |
| 3.3.3.6 | Add health degradation indicators | ✅ | 0.5h | 3.3.3.5 | Health status |
| 3.3.3.7 | Test failure scenarios | ✅ | 1h | 3.3.3.2 | Chaos testing |
| **3.3.4** | **Async Task Queue** | ✅ | 5h | None | Background tasks |
| 3.3.4.1 | Evaluate task queue options (Celery/ARQ) | ✅ | 0.5h | - | Evaluation |
| 3.3.4.2 | Set up ARQ with Redis | ✅ | 1h | 3.3.4.1 | ARQ setup |
| 3.3.4.3 | Move email sending to background | ✅ | 0.5h | 3.3.4.2 | Email queue |
| 3.3.4.4 | Move export generation to background | ✅ | 1h | 3.3.4.2 | Export queue |
| 3.3.4.5 | Add task monitoring | ✅ | 0.5h | 3.3.4.2 | Task monitoring |
| 3.3.4.6 | Add task retry logic | ✅ | 0.5h | 3.3.4.2 | Task retry |
| 3.3.4.7 | Update Docker Compose with worker | ✅ | 1h | 3.3.4.2 | Worker container |

---

## Sprint 3.4: Monitoring & Alerting (Week 12) ✅ COMPLETE

### Overview
Implement comprehensive monitoring stack with Prometheus, Grafana, and alerting.

**Status: ✅ COMPLETE** (December 16, 2025)

**Completed:**
- Prometheus setup with scrape targets for all services
- PostgreSQL, Redis, and Node exporters configured
- Grafana dashboards with provisioning
- API performance dashboard in JSON format
- Alertmanager with alert routing configuration
- Alert rules for errors, latency, service health, database, AI agent
- Loki log aggregation with 7-day retention
- Promtail log shipping from Docker containers
- All monitoring services added to docker-compose.yml

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **3.4.1** | **Prometheus Setup** | ✅ | 4h | None | Metrics collection |
| 3.4.1.1 | Add Prometheus to Docker Compose | ✅ | 0.5h | - | Prometheus container |
| 3.4.1.2 | Configure Prometheus scrape targets | ✅ | 0.5h | 3.4.1.1 | Scrape config |
| 3.4.1.3 | Add FastAPI metrics exporter | ✅ | 0.5h | 3.4.1.1 | Backend metrics |
| 3.4.1.4 | Add PostgreSQL exporter | ✅ | 0.5h | 3.4.1.1 | DB metrics |
| 3.4.1.5 | Add Redis exporter | ✅ | 0.5h | 3.4.1.1 | Redis metrics |
| 3.4.1.6 | Add Qdrant metrics | ✅ | 0.5h | 3.4.1.1 | Vector DB metrics |
| 3.4.1.7 | Configure retention and storage | ✅ | 0.5h | 3.4.1.1 | Storage config |
| 3.4.1.8 | Set up Prometheus federation (future) | 🟡 | 0.5h | 3.4.1.7 | Federation prep |
| **3.4.2** | **Grafana Dashboards** | ✅ | 6h | 3.4.1 | Visualizations |
| 3.4.2.1 | Add Grafana to Docker Compose | ✅ | 0.5h | - | Grafana container |
| 3.4.2.2 | Create API performance dashboard | ✅ | 1h | 3.4.2.1 | API dashboard |
| 3.4.2.3 | Create database dashboard | ✅ | 1h | 3.4.2.1 | DB dashboard |
| 3.4.2.4 | Create AI agent dashboard | ✅ | 1h | 3.4.2.1 | AI dashboard |
| 3.4.2.5 | Create RAG metrics dashboard | ✅ | 1h | 3.4.2.1 | RAG dashboard |
| 3.4.2.6 | Create business metrics dashboard | ✅ | 1h | 3.4.2.1 | Business dashboard |
| 3.4.2.7 | Export dashboards as code | ✅ | 0.5h | 3.4.2.2 | Dashboard as code |
| **3.4.3** | **Alerting Rules** | ✅ | 5h | 3.4.1 | Alerts |
| 3.4.3.1 | Configure Alertmanager | ✅ | 0.5h | - | Alertmanager |
| 3.4.3.2 | Add high error rate alert | ✅ | 0.5h | 3.4.3.1 | Error alert |
| 3.4.3.3 | Add high latency alert (p95 > 1s) | ✅ | 0.5h | 3.4.3.1 | Latency alert |
| 3.4.3.4 | Add database connection alert | ✅ | 0.5h | 3.4.3.1 | DB alert |
| 3.4.3.5 | Add service down alert | ✅ | 0.5h | 3.4.3.1 | Uptime alert |
| 3.4.3.6 | Add disk space alert | ✅ | 0.5h | 3.4.3.1 | Disk alert |
| 3.4.3.7 | Add Claude API quota alert | ✅ | 0.5h | 3.4.3.1 | Quota alert |
| 3.4.3.8 | Configure Slack integration | ✅ | 0.5h | 3.4.3.1 | Slack alerts |
| 3.4.3.9 | Configure PagerDuty (future) | 🟡 | 0.5h | 3.4.3.1 | PagerDuty |
| 3.4.3.10 | Test alert routing | ✅ | 0.5h | 3.4.3.8 | Alert testing |
| **3.4.4** | **Log Aggregation** | ✅ | 4h | None | Centralized logs |
| 3.4.4.1 | Set up Loki for log aggregation | ✅ | 1h | - | Loki setup |
| 3.4.4.2 | Configure Promtail log shipping | ✅ | 0.5h | 3.4.4.1 | Log shipping |
| 3.4.4.3 | Create log exploration dashboard | ✅ | 1h | 3.4.4.1 | Log dashboard |
| 3.4.4.4 | Set up log-based alerts | ✅ | 0.5h | 3.4.4.1 | Log alerts |
| 3.4.4.5 | Configure log retention | ✅ | 0.5h | 3.4.4.1 | Log retention |
| 3.4.4.6 | Add request trace correlation | ✅ | 0.5h | 3.4.4.2 | Trace correlation |

**Phase 3 Completion Checklist:**
```
✅ API versioned at /api/v1/ (Sprint 3.1)
✅ Comprehensive API documentation (Sprint 3.1)
✅ Database indexes optimized (Sprint 3.2)
✅ Backup/restore tested (Sprint 3.2)
✅ Dependency injection implemented (Sprint 3.3)
✅ Circuit breakers for external APIs (Sprint 3.3)
✅ Prometheus metrics collection (Sprint 3.4)
✅ Grafana dashboards operational (Sprint 3.4)
✅ Alerting configured and tested (Sprint 3.4)
```

**Phase 3 Status: ✅ COMPLETE** (December 16, 2025)

---

# PHASE 4: Features & Polish (Weeks 13-16)

## Sprint 4.1: Custom Claude Skills (Week 13) ✅ COMPLETE

### Overview
Create custom Claude Skills specifically for Money Flow to enhance AI capabilities.

**Status: ✅ COMPLETE** (December 16, 2025)

**Completed:**
- Financial Analysis Skill with spending analysis, budget comparison, trend detection, anomaly alerts
- Payment Reminder Skill with urgency classification, multi-channel support, scheduling logic
- Debt Management Skill with avalanche/snowball strategies, interest calculations, Python calculator module
- Savings Goal Skill with goal tracking, contribution recommendations, milestone celebrations
- 32 unit tests for skill calculators
- Skills README documentation

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **4.1.1** | **Financial Analysis Skill** | ✅ | 6h | None | Analysis skill |
| 4.1.1.1 | Create SKILL.md structure | ✅ | 0.5h | - | Skill structure |
| 4.1.1.2 | Define spending analysis patterns | ✅ | 1h | 4.1.1.1 | Analysis patterns |
| 4.1.1.3 | Add budget comparison logic | ✅ | 1h | 4.1.1.2 | Budget comparison |
| 4.1.1.4 | Add trend detection instructions | ✅ | 1h | 4.1.1.2 | Trend detection |
| 4.1.1.5 | Add anomaly detection patterns | ✅ | 1h | 4.1.1.2 | Anomaly detection |
| 4.1.1.6 | Create example prompts and outputs | ✅ | 0.5h | 4.1.1.2 | Examples |
| 4.1.1.7 | Test skill integration | ✅ | 1h | 4.1.1.5 | Integration test |
| **4.1.2** | **Payment Reminder Skill** | ✅ | 4h | None | Reminder skill |
| 4.1.2.1 | Create reminder generation patterns | ✅ | 1h | - | Reminder patterns |
| 4.1.2.2 | Add urgency level classification | ✅ | 0.75h | 4.1.2.1 | Urgency levels |
| 4.1.2.3 | Add personalization rules | ✅ | 0.75h | 4.1.2.1 | Personalization |
| 4.1.2.4 | Add multi-channel format templates | ✅ | 0.75h | 4.1.2.1 | Format templates |
| 4.1.2.5 | Create notification scheduling logic | ✅ | 0.75h | 4.1.2.2 | Scheduling |
| **4.1.3** | **Debt Management Skill** | ✅ | 5h | None | Debt skill |
| 4.1.3.1 | Create debt payoff strategy patterns | ✅ | 1h | - | Payoff strategies |
| 4.1.3.2 | Add avalanche vs snowball comparison | ✅ | 1h | 4.1.3.1 | Method comparison |
| 4.1.3.3 | Add interest calculation helpers | ✅ | 1h | 4.1.3.1 | Interest calc |
| 4.1.3.4 | Add debt-free date projection | ✅ | 1h | 4.1.3.2 | Date projection |
| 4.1.3.5 | Create motivational response patterns | ✅ | 0.5h | 4.1.3.1 | Motivation |
| 4.1.3.6 | Test with various debt scenarios | ✅ | 0.5h | 4.1.3.4 | Scenario testing |
| **4.1.4** | **Savings Goal Skill** | ✅ | 4h | None | Savings skill |
| 4.1.4.1 | Create goal tracking patterns | ✅ | 1h | - | Goal tracking |
| 4.1.4.2 | Add milestone celebration messages | ✅ | 0.5h | 4.1.4.1 | Milestones |
| 4.1.4.3 | Add contribution recommendation logic | ✅ | 1h | 4.1.4.1 | Recommendations |
| 4.1.4.4 | Add goal achievement projection | ✅ | 1h | 4.1.4.1 | Projections |
| 4.1.4.5 | Create progress visualization prompts | ✅ | 0.5h | 4.1.4.1 | Visualizations |
| **4.1.5** | **Skill Testing & Documentation** | ✅ | 4h | 4.1.1-4.1.4 | Skill docs |
| 4.1.5.1 | Create skill test suite | ✅ | 1h | - | Test suite |
| 4.1.5.2 | Test skill composition (multiple skills) | ✅ | 1h | 4.1.5.1 | Composition test |
| 4.1.5.3 | Document skill usage | ✅ | 1h | - | Usage docs |
| 4.1.5.4 | Create skill showcase demo | ✅ | 0.5h | 4.1.5.3 | Demo |
| 4.1.5.5 | Package skills for distribution | ✅ | 0.5h | 4.1.5.3 | Package |

**Custom Skills File Structure:**
```
money-flow-skills/
├── financial-analysis/
│   ├── SKILL.mdDid 
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
| **4.2.1** | **Mobile Responsiveness** | ✅ | 6h | None | Mobile UI |
| 4.2.1.1 | Audit current mobile breakpoints | ✅ | 0.5h | - | Breakpoint audit |
| 4.2.1.2 | Fix subscription list mobile layout | ✅ | 1h | 4.2.1.1 | List responsive |
| 4.2.1.3 | Fix calendar mobile layout | ✅ | 1h | 4.2.1.1 | Calendar responsive |
| 4.2.1.4 | Fix cards dashboard mobile layout | ✅ | 1h | 4.2.1.1 | Cards responsive |
| 4.2.1.5 | Fix agent chat mobile layout | ✅ | 1h | 4.2.1.1 | Chat responsive |
| 4.2.1.6 | Add mobile navigation drawer | ✅ | 1h | 4.2.1.1 | Nav drawer |
| 4.2.1.7 | Test on various device sizes | ✅ | 0.5h | 4.2.1.2 | Device testing |
| **4.2.2** | **Accessibility (a11y)** | ✅ | 5h | None | Accessible UI |
| 4.2.2.1 | Add ARIA labels to all interactive elements | ✅ | 1h | - | ARIA labels |
| 4.2.2.2 | Ensure keyboard navigation | ✅ | 1h | 4.2.2.1 | Keyboard nav |
| 4.2.2.3 | Add focus indicators | ✅ | 0.5h | 4.2.2.2 | Focus states |
| 4.2.2.4 | Check color contrast ratios | ✅ | 0.5h | - | Contrast check |
| 4.2.2.5 | Add screen reader announcements | ✅ | 1h | 4.2.2.1 | SR support |
| 4.2.2.6 | Run axe-core accessibility audit | ✅ | 0.5h | 4.2.2.1 | a11y audit |
| 4.2.2.7 | Fix audit findings | ✅ | 0.5h | 4.2.2.6 | Fix issues |
| **4.2.3** | **UX Improvements** | ✅ | 6h | None | Better UX |
| 4.2.3.1 | Add loading skeletons | ✅ | 1h | - | Skeletons |
| 4.2.3.2 | Add optimistic updates | ✅ | 1.5h | - | Optimistic UI |
| 4.2.3.3 | Add pull-to-refresh (mobile) | ✅ | 0.5h | - | Pull refresh |
| 4.2.3.4 | Add keyboard shortcuts | ✅ | 1h | - | Shortcuts |
| 4.2.3.5 | Add toast notifications | ✅ | 0.5h | - | Toasts |
| 4.2.3.6 | Add confirmation dialogs for destructive actions | ✅ | 0.5h | - | Confirmations |
| 4.2.3.7 | Add empty state illustrations | ✅ | 0.5h | - | Empty states |
| 4.2.3.8 | Add onboarding tour | ✅ | 0.5h | - | Onboarding |
| **4.2.4** | **Dark Mode** | ✅ | 12h | None | Dark theme |
| 4.2.4.1 | Create dark color palette with OKLCH | ✅ | 1h | - | Dark palette |
| 4.2.4.2 | Add theme toggle component | ✅ | 0.5h | 4.2.4.1 | Toggle |
| 4.2.4.3 | Add system preference detection | ✅ | 0.5h | 4.2.4.2 | System pref |
| 4.2.4.4 | Persist theme preference | ✅ | 0.5h | 4.2.4.2 | Persistence |
| 4.2.4.5 | Add inline script for flash prevention | ✅ | 0.25h | 4.2.4.3 | No flash |
| **4.2.5** | **Dark Mode - Global Styles** | ✅ | 2h | 4.2.4 | Global dark |
| 4.2.5.1 | Update globals.css glass-card classes | ✅ | 0.25h | - | Glass cards |
| 4.2.5.2 | Update globals.css gradient-mesh | ✅ | 0.25h | - | Gradient mesh |
| 4.2.5.3 | Update globals.css shimmer animation | ✅ | 0.25h | - | Shimmer |
| 4.2.5.4 | Update globals.css btn-glass styles | ✅ | 0.25h | - | Glass buttons |
| 4.2.5.5 | Update globals.css input-glass styles | ✅ | 0.25h | - | Glass inputs |
| 4.2.5.6 | Update globals.css text-gradient | ✅ | 0.25h | - | Text gradients |
| 4.2.5.7 | Update globals.css scrollbar styles | ✅ | 0.25h | - | Scrollbars |
| 4.2.5.8 | Update Tailwind dark mode base colors | ✅ | 0.25h | - | Base colors |
| **4.2.6** | **Dark Mode - Header Component** | ✅ | 0.5h | 4.2.4 | Header dark |
| 4.2.6.1 | Update Header glass-card background | ✅ | 0.1h | - | Header bg |
| 4.2.6.2 | Update Import/Export button | ✅ | 0.1h | - | I/E button |
| 4.2.6.3 | Update theme toggle button | ✅ | 0.1h | - | Theme toggle |
| 4.2.6.4 | Update user menu dropdown | ✅ | 0.1h | - | User menu |
| 4.2.6.5 | Update date display text | ✅ | 0.1h | - | Date text |
| **4.2.7** | **Dark Mode - StatsPanel Component** | ✅ | 1h | 4.2.4 | Stats dark |
| 4.2.7.1 | Update stat card backgrounds | ✅ | 0.2h | - | Card bg |
| 4.2.7.2 | Update stat card borders | ✅ | 0.1h | - | Card borders |
| 4.2.7.3 | Update Monthly Spending card colors | ✅ | 0.1h | - | Monthly colors |
| 4.2.7.4 | Update Yearly Total card colors | ✅ | 0.1h | - | Yearly colors |
| 4.2.7.5 | Update Active Payments card colors | ✅ | 0.1h | - | Active colors |
| 4.2.7.6 | Update Total Debt card colors | ✅ | 0.1h | - | Debt colors |
| 4.2.7.7 | Update stat card icon containers | ✅ | 0.1h | - | Icon containers |
| 4.2.7.8 | Update stat card labels and values | ✅ | 0.1h | - | Labels/values |
| **4.2.8** | **Dark Mode - Main Page Tabs** | ✅ | 0.5h | 4.2.4 | Tabs dark |
| 4.2.8.1 | Update tab container background | ✅ | 0.1h | - | Tab container |
| 4.2.8.2 | Update inactive tab text color | ✅ | 0.1h | - | Inactive tabs |
| 4.2.8.3 | Update active tab background | ✅ | 0.1h | - | Active tab bg |
| 4.2.8.4 | Update tab hover states | ✅ | 0.1h | - | Tab hover |
| 4.2.8.5 | Update tab icons color | ✅ | 0.1h | - | Tab icons |
| **4.2.9** | **Dark Mode - AgentChat Component** | ✅ | 1.5h | 4.2.4 | Chat dark |
| 4.2.9.1 | Update chat container background | ✅ | 0.1h | - | Chat bg |
| 4.2.9.2 | Update chat header/title | ✅ | 0.1h | - | Chat header |
| 4.2.9.3 | Update AI welcome message card | ✅ | 0.2h | - | Welcome card |
| 4.2.9.4 | Update quick action buttons | ✅ | 0.2h | - | Action buttons |
| 4.2.9.5 | Update chat message bubbles (user) | ✅ | 0.15h | - | User bubbles |
| 4.2.9.6 | Update chat message bubbles (AI) | ✅ | 0.15h | - | AI bubbles |
| 4.2.9.7 | Update chat input field | ✅ | 0.15h | - | Input field |
| 4.2.9.8 | Update send button | ✅ | 0.1h | - | Send button |
| 4.2.9.9 | Update typing indicator | ✅ | 0.1h | - | Typing dots |
| 4.2.9.10 | Update scroll area | ✅ | 0.1h | - | Scroll area |
| **4.2.10** | **Dark Mode - SubscriptionList Component** | ✅ | 2h | 4.2.4 | List dark |
| 4.2.10.1 | Update list header (Your Payments title) | ✅ | 0.1h | - | List header |
| 4.2.10.2 | Update Add Payment button | ✅ | 0.1h | - | Add button |
| 4.2.10.3 | Update category filter pills container | ✅ | 0.1h | - | Filter container |
| 4.2.10.4 | Update category pill inactive state | ✅ | 0.15h | - | Inactive pills |
| 4.2.10.5 | Update category pill active state | ✅ | 0.15h | - | Active pills |
| 4.2.10.6 | Update category pill counts badge | ✅ | 0.1h | - | Count badges |
| 4.2.10.7 | Update subscription card background | ✅ | 0.2h | - | Card bg |
| 4.2.10.8 | Update subscription card border | ✅ | 0.1h | - | Card border |
| 4.2.10.9 | Update subscription name text | ✅ | 0.1h | - | Name text |
| 4.2.10.10 | Update subscription category badge | ✅ | 0.1h | - | Category badge |
| 4.2.10.11 | Update subscription amount text | ✅ | 0.1h | - | Amount text |
| 4.2.10.12 | Update subscription frequency text | ✅ | 0.1h | - | Frequency text |
| 4.2.10.13 | Update due date display | ✅ | 0.1h | - | Due date |
| 4.2.10.14 | Update "Due today" badge | ✅ | 0.1h | - | Due today |
| 4.2.10.15 | Update "X days" remaining badge | ✅ | 0.1h | - | Days remaining |
| 4.2.10.16 | Update notes/description text | ✅ | 0.1h | - | Notes text |
| 4.2.10.17 | Update edit/delete action buttons | ✅ | 0.1h | - | Action buttons |
| **4.2.11** | **Dark Mode - CardsDashboard Component** | ✅ | 1.5h | 4.2.4 | Cards dark |
| 4.2.11.1 | Update cards dashboard header | ✅ | 0.1h | - | Dashboard header |
| 4.2.11.2 | Update Add Card button | ✅ | 0.1h | - | Add card btn |
| 4.2.11.3 | Update summary card backgrounds | ✅ | 0.15h | - | Summary bg |
| 4.2.11.4 | Update Total Due stat box | ✅ | 0.15h | - | Total due |
| 4.2.11.5 | Update Paid stat box | ✅ | 0.15h | - | Paid box |
| 4.2.11.6 | Update Remaining stat box | ✅ | 0.15h | - | Remaining box |
| 4.2.11.7 | Update progress bar track | ✅ | 0.1h | - | Progress track |
| 4.2.11.8 | Update progress bar fill | ✅ | 0.1h | - | Progress fill |
| 4.2.11.9 | Update "Due Next Month" section | ✅ | 0.1h | - | Due next month |
| 4.2.11.10 | Update individual card items | ✅ | 0.15h | - | Card items |
| 4.2.11.11 | Update card name and bank text | ✅ | 0.1h | - | Card text |
| **4.2.12** | **Dark Mode - PaymentCalendar Component** | ✅ | 1h | 4.2.4 | Calendar dark |
| 4.2.12.1 | Update calendar container | ✅ | 0.1h | - | Calendar bg |
| 4.2.12.2 | Update month navigation arrows | ✅ | 0.1h | - | Nav arrows |
| 4.2.12.3 | Update month/year header | ✅ | 0.1h | - | Month header |
| 4.2.12.4 | Update day of week headers | ✅ | 0.1h | - | Day headers |
| 4.2.12.5 | Update regular day cells | ✅ | 0.1h | - | Day cells |
| 4.2.12.6 | Update today highlight | ✅ | 0.1h | - | Today highlight |
| 4.2.12.7 | Update days with payments indicator | ✅ | 0.15h | - | Payment dots |
| 4.2.12.8 | Update payment details popup | ✅ | 0.15h | - | Details popup |
| **4.2.13** | **Dark Mode - AddSubscriptionModal** | ✅ | 1h | 4.2.4 | Add modal dark |
| 4.2.13.1 | Update modal overlay backdrop | ✅ | 0.1h | - | Modal overlay |
| 4.2.13.2 | Update modal container background | ✅ | 0.1h | - | Modal bg |
| 4.2.13.3 | Update modal header/title | ✅ | 0.1h | - | Modal header |
| 4.2.13.4 | Update close button | ✅ | 0.05h | - | Close btn |
| 4.2.13.5 | Update form labels | ✅ | 0.1h | - | Form labels |
| 4.2.13.6 | Update text input fields | ✅ | 0.15h | - | Text inputs |
| 4.2.13.7 | Update select dropdowns | ✅ | 0.15h | - | Selects |
| 4.2.13.8 | Update date picker | ✅ | 0.1h | - | Date picker |
| 4.2.13.9 | Update cancel button | ✅ | 0.05h | - | Cancel btn |
| 4.2.13.10 | Update submit button | ✅ | 0.05h | - | Submit btn |
| **4.2.14** | **Dark Mode - EditSubscriptionModal** | ✅ | 0.5h | 4.2.13 | Edit modal dark |
| 4.2.14.1 | Apply same styles as AddSubscriptionModal | ✅ | 0.25h | - | Same styles |
| 4.2.14.2 | Update delete confirmation state | ✅ | 0.25h | - | Delete confirm |
| **4.2.15** | **Dark Mode - ImportExportModal** | ✅ | 0.5h | 4.2.4 | I/E modal dark |
| 4.2.15.1 | Update modal container | ✅ | 0.1h | - | Modal container |
| 4.2.15.2 | Update tab switcher (Import/Export) | ✅ | 0.1h | - | Tab switcher |
| 4.2.15.3 | Update file drop zone | ✅ | 0.15h | - | Drop zone |
| 4.2.15.4 | Update format selection buttons | ✅ | 0.1h | - | Format btns |
| 4.2.15.5 | Update status messages | ✅ | 0.05h | - | Status msgs |
| **4.2.16** | **Dark Mode - CurrencySelector** | ✅ | 0.25h | 4.2.4 | Currency dark |
| 4.2.16.1 | Update dropdown trigger button | ✅ | 0.1h | - | Trigger btn |
| 4.2.16.2 | Update dropdown menu | ✅ | 0.1h | - | Menu bg |
| 4.2.16.3 | Update currency option items | ✅ | 0.05h | - | Option items |
| **4.2.17** | **Dark Mode - Login Page** | ✅ | 0.5h | 4.2.4 | Login dark |
| 4.2.17.1 | Update page background | ✅ | 0.1h | - | Page bg |
| 4.2.17.2 | Update login card container | ✅ | 0.1h | - | Card container |
| 4.2.17.3 | Update form inputs | ✅ | 0.1h | - | Form inputs |
| 4.2.17.4 | Update login button | ✅ | 0.1h | - | Login btn |
| 4.2.17.5 | Update register link | ✅ | 0.1h | - | Register link |
| **4.2.18** | **Dark Mode - Register Page** | ✅ | 0.5h | 4.2.17 | Register dark |
| 4.2.18.1 | Apply same styles as Login page | ✅ | 0.25h | - | Same styles |
| 4.2.18.2 | Update password requirements text | ✅ | 0.25h | - | Requirements |
| **4.2.19** | **Dark Mode - Error Pages** | ✅ | 0.25h | 4.2.4 | Error dark |
| 4.2.19.1 | Update error.tsx page | ✅ | 0.1h | - | Error page |
| 4.2.19.2 | Update global-error.tsx page | ✅ | 0.15h | - | Global error |
| **4.2.20** | **Dark Mode - Toast Notifications** | ✅ | 0.25h | 4.2.4 | Toast dark |
| 4.2.20.1 | Update success toast | ✅ | 0.1h | - | Success toast |
| 4.2.20.2 | Update error toast | ✅ | 0.1h | - | Error toast |
| 4.2.20.3 | Update info/warning toast | ✅ | 0.05h | - | Other toasts |
| **4.2.21** | **Dark Mode - Loading States** | ✅ | 0.5h | 4.2.4 | Loading dark |
| 4.2.21.1 | Update loading spinner | ✅ | 0.1h | - | Spinner |
| 4.2.21.2 | Update skeleton loaders | ✅ | 0.2h | - | Skeletons |
| 4.2.21.3 | Update progress indicators | ✅ | 0.2h | - | Progress |
| **4.2.22** | **Dark Mode - Empty States** | ✅ | 0.25h | 4.2.4 | Empty dark |
| 4.2.22.1 | Update "No subscriptions" state | ✅ | 0.1h | - | No subs |
| 4.2.22.2 | Update "No cards" state | ✅ | 0.1h | - | No cards |
| 4.2.22.3 | Update search "No results" state | ✅ | 0.05h | - | No results |
| **4.2.23** | **Dark Mode - Scrollbars & Misc** | ✅ | 0.25h | 4.2.4 | Misc dark |
| 4.2.23.1 | Update custom scrollbar colors | ✅ | 0.1h | - | Scrollbars |
| 4.2.23.2 | Update focus ring colors | ✅ | 0.1h | - | Focus rings |
| 4.2.23.3 | Update selection highlight | ✅ | 0.05h | - | Selection |
| **4.2.24** | **Dark Mode - Testing & Polish** | ✅ | 1h | 4.2.5-4.2.23 | Testing |
| 4.2.24.1 | Test all components in dark mode | ✅ | 0.25h | - | Component test |
| 4.2.24.2 | Check contrast ratios (WCAG AA) | ✅ | 0.25h | - | Contrast check |
| 4.2.24.3 | Test theme transitions smoothness | ✅ | 0.15h | - | Transitions |
| 4.2.24.4 | Test system preference changes | ✅ | 0.1h | - | System pref |
| 4.2.24.5 | Fix any visual inconsistencies | ✅ | 0.25h | - | Visual fixes |
| **4.2.25** | **Dark Mode - Documentation** | ✅ | 0.25h | 4.2.24 | Docs |
| 4.2.25.1 | Document dark mode color palette | ✅ | 0.1h | - | Palette docs |
| 4.2.25.2 | Update component styling guide | ✅ | 0.1h | - | Style guide |
| 4.2.25.3 | Add dark mode to CHANGELOG | ✅ | 0.05h | - | Changelog |
| **4.2.26** | **Dark Mode - Refinements & Bug Fixes** | ✅ | 2h | 4.2.25 | Refinements |
| 4.2.26.1 | Fix SimpleIcons CDN URL (use cdn.simpleicons.org) | ✅ | 0.25h | - | Icon CDN fix |
| 4.2.26.2 | Fix card hover blinking animation | ✅ | 0.25h | - | Hover fix |
| 4.2.26.3 | Fix calendar payment completion handler | ✅ | 0.25h | - | Calendar fix |
| 4.2.26.4 | Improve glass-card dark mode styling | ✅ | 0.25h | - | Card styling |
| 4.2.26.5 | Add missing service icons (Klarna, Lloyds, etc.) | ✅ | 0.25h | - | Service icons |
| 4.2.26.6 | Improve subscription card hover shadow | ✅ | 0.25h | - | Shadow refinement |
| 4.2.26.7 | Add inset border highlight for glass cards | ✅ | 0.25h | - | Border highlight |

---

## Sprint 4.3: Payment Reminders & Telegram Bot (Week 15) ✅

### Overview
Implement payment reminders with Telegram bot as the primary notification channel. Users can connect their Telegram account and receive payment reminders, daily/weekly digests, and overdue alerts.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **4.3.1** | **NotificationPreferences Model** | ✅ | 3h | None | Model & Migration |
| 4.3.1.1 | Create NotificationPreferences model | ✅ | 1h | - | `src/models/notification.py` |
| 4.3.1.2 | Add Telegram fields (chat_id, username, verified) | ✅ | 0.5h | 4.3.1.1 | Telegram integration |
| 4.3.1.3 | Add reminder settings (days_before, time) | ✅ | 0.5h | 4.3.1.1 | Reminder config |
| 4.3.1.4 | Add digest settings (daily, weekly) | ✅ | 0.5h | 4.3.1.1 | Digest config |
| 4.3.1.5 | Create Alembic migration | ✅ | 0.5h | 4.3.1.1 | Migration file |
| **4.3.2** | **Telegram Bot Service** | ✅ | 4h | 4.3.1 | Telegram service |
| 4.3.2.1 | Create TelegramService class | ✅ | 1h | - | `src/services/telegram_service.py` |
| 4.3.2.2 | Implement send_message() | ✅ | 0.5h | 4.3.2.1 | Message sending |
| 4.3.2.3 | Implement send_reminder() | ✅ | 0.5h | 4.3.2.1 | Payment reminders |
| 4.3.2.4 | Implement send_daily_digest() | ✅ | 0.5h | 4.3.2.1 | Daily digest |
| 4.3.2.5 | Implement send_weekly_digest() | ✅ | 0.5h | 4.3.2.1 | Weekly digest |
| 4.3.2.6 | Add long polling support | ✅ | 0.5h | 4.3.2.1 | TelegramPoller class |
| 4.3.2.7 | Add verification code flow | ✅ | 0.5h | 4.3.2.1 | Account linking |
| **4.3.3** | **Notification API Endpoints** | ✅ | 3h | 4.3.2 | API routes |
| 4.3.3.1 | GET /preferences | ✅ | 0.5h | - | Get preferences |
| 4.3.3.2 | PUT /preferences | ✅ | 0.5h | 4.3.3.1 | Update preferences |
| 4.3.3.3 | POST /telegram/link | ✅ | 0.5h | - | Initiate linking |
| 4.3.3.4 | GET /telegram/status | ✅ | 0.25h | - | Check status |
| 4.3.3.5 | DELETE /telegram/unlink | ✅ | 0.25h | - | Unlink account |
| 4.3.3.6 | POST /test | ✅ | 0.5h | - | Test notification |
| 4.3.3.7 | POST /trigger | ✅ | 0.5h | - | Manual trigger endpoint |
| **4.3.4** | **Telegram Update Handler** | ✅ | 2h | 4.3.2 | Bot commands |
| 4.3.4.1 | Create telegram_handler.py | ✅ | 0.5h | - | Handler module |
| 4.3.4.2 | Handle /start command | ✅ | 0.25h | 4.3.4.1 | Welcome message |
| 4.3.4.3 | Handle /status command | ✅ | 0.25h | 4.3.4.1 | Status check |
| 4.3.4.4 | Handle /help command | ✅ | 0.25h | 4.3.4.1 | Help message |
| 4.3.4.5 | Handle verification codes | ✅ | 0.5h | 4.3.4.1 | Account linking |
| 4.3.4.6 | Add main.py lifespan integration | ✅ | 0.25h | 4.3.4.1 | Startup/shutdown |
| **4.3.5** | **Background Reminder Tasks** | ✅ | 3h | 4.3.2 | Scheduled tasks |
| 4.3.5.1 | Implement send_payment_reminders task | ✅ | 0.75h | - | Daily reminders |
| 4.3.5.2 | Implement send_daily_digest task | ✅ | 0.5h | - | Daily digest |
| 4.3.5.3 | Implement send_weekly_digest task | ✅ | 0.5h | - | Weekly digest |
| 4.3.5.4 | Implement send_overdue_alerts task | ✅ | 0.5h | - | Overdue alerts |
| 4.3.5.5 | Configure cron schedules | ✅ | 0.25h | - | WorkerSettings |
| 4.3.5.6 | Add quiet hours support | ✅ | 0.5h | - | Respect user prefs |
| **4.3.6** | **Settings Page Frontend** | ✅ | 3h | 4.3.3 | Settings UI |
| 4.3.6.1 | Create /settings route | ✅ | 0.5h | - | Settings page |
| 4.3.6.2 | Add Profile tab | ✅ | 0.5h | 4.3.6.1 | User info |
| 4.3.6.3 | Add Notifications tab | ✅ | 1h | 4.3.6.1 | Notification prefs |
| 4.3.6.4 | Add Telegram linking UI | ✅ | 0.5h | 4.3.6.3 | Verification flow |
| 4.3.6.5 | Add test notification button | ✅ | 0.25h | 4.3.6.3 | Test button |
| 4.3.6.6 | Update Header with Settings link | ✅ | 0.25h | 4.3.6.1 | Navigation |
| **4.3.7** | **Unit Tests** | ✅ | 2h | All | Test coverage |
| 4.3.7.1 | Test NotificationPreferences model | ✅ | 0.5h | - | Model tests |
| 4.3.7.2 | Test TelegramService | ✅ | 0.5h | - | Service tests |
| 4.3.7.3 | Test notification schemas | ✅ | 0.25h | - | Schema tests |
| 4.3.7.4 | Test background tasks | ✅ | 0.5h | - | Task tests |
| 4.3.7.5 | Test API endpoints | ✅ | 0.25h | - | API tests |

**Sprint 4.3 Completion Summary:**
- ✅ NotificationPreferences model with Telegram integration
- ✅ TelegramService with long polling for local development
- ✅ Complete notification API (7 endpoints)
- ✅ Telegram bot commands (/start, /status, /help)
- ✅ 4 background tasks with cron scheduling
- ✅ Settings page with Profile and Notifications tabs
- ✅ 37 new unit tests (524 total)
- ✅ Manual trigger endpoint for testing reminders

---

## Sprint 4.4: Documentation & Security (Week 16) ✅

### Overview
Documentation updates and security audit before Phase 5 begins.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **4.4.1** | **User Documentation** | ✅ | 5h | None | User docs |
| 4.4.1.1 | Create user guide | ✅ | 1.5h | - | `docs/USER_GUIDE.md` |
| 4.4.1.2 | Create FAQ document | ✅ | 1h | - | `docs/FAQ.md` |
| 4.4.1.3 | Create video tutorials (scripts) | 🟡 | 1h | 4.4.1.1 | Deferred to Phase 5 |
| 4.4.1.4 | Create feature walkthrough | ✅ | 1h | 4.4.1.1 | In USER_GUIDE.md |
| 4.4.1.5 | Create troubleshooting guide | ✅ | 0.5h | - | `docs/TROUBLESHOOTING.md` |
| **4.4.2** | **Developer Documentation Update** | ✅ | 4h | All sprints | Dev docs |
| 4.4.2.1 | Update architecture documentation | ✅ | 1h | - | `.claude/docs/ARCHITECTURE.md` v2.0.0 |
| 4.4.2.2 | Update API documentation | ✅ | 1h | - | `docs/api/README.md`, `NOTIFICATIONS.md` |
| 4.4.2.3 | Create deployment runbook | ✅ | 1h | - | `docs/DEPLOYMENT_RUNBOOK.md` |
| 4.4.2.4 | Create incident response playbook | ✅ | 0.5h | - | `docs/INCIDENT_RESPONSE.md` |
| 4.4.2.5 | Update README with all new features | ✅ | 0.5h | - | `CLAUDE.md` updated |
| **4.4.3** | **Security Audit** | ✅ | 4h | All sprints | Security |
| 4.4.3.1 | Run OWASP ZAP scan | 🟡 | 1h | - | Deferred (requires deployed app) |
| 4.4.3.2 | Run dependency vulnerability scan | ✅ | 0.5h | - | pip-audit & npm audit passed |
| 4.4.3.3 | Review authentication implementation | ✅ | 0.5h | - | bcrypt 12 rounds, JWT type validation |
| 4.4.3.4 | Review data encryption | ✅ | 0.5h | - | JWT secrets, password hashing verified |
| 4.4.3.5 | Fix critical findings | ✅ | 1h | 4.4.3.1 | filelock, urllib3, setuptools patched |
| 4.4.3.6 | Document security posture | ✅ | 0.5h | 4.4.3.5 | `docs/SECURITY.md` |

**Sprint 4.4 Deliverables:**
- ✅ User documentation (guide, FAQ, walkthrough)
- ✅ Developer documentation updated
- ✅ Deployment runbook
- ✅ Security audit completed
- ⏱️ **Total: ~13 hours**

**Phase 4 Completion Checklist:**
```
✅ Custom Claude Skills deployed (Sprint 4.1)
✅ Mobile responsive design complete (Sprint 4.2)
✅ Accessibility audit passed (Sprint 4.2)
✅ Dark mode implemented (Sprint 4.2)
✅ Payment reminders functional (Sprint 4.3)
✅ Telegram bot integration (Sprint 4.3)
✅ User documentation complete (Sprint 4.4)
✅ Security audit passed (Sprint 4.4)
```

> **Note**: Production deployment moved to Phase 6 (after Phase 5 Settings & AI features)

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
| 13 | 4.1 | Custom Skills | Financial analysis, debt, savings ✅ |
| 14 | 4.2 | Frontend | Mobile, a11y, dark mode ✅ |
| 15 | 4.3 | Telegram Bot | Payment reminders, digests, settings ✅ |
| 16 | 4.4 | Docs & Security | User docs, dev docs, security audit 🔄 |
| 17-18 | 5.1 | Profile & Preferences | Settings UI, 2FA, theme |
| 19-20 | 5.2 | Cards & Categories | Enhanced cards, budgets, AI suggestions |
| 21-22 | 5.3 | Notifications & Export | Email/push, PDF reports, backups |
| 23-24 | 5.4 | Icons & AI Settings | Icon APIs, AI assistant config |
| 25-27 | 5.5 | Smart Import | Bank statements, email scanning |
| 28-30 | 5.6 | Integrations | Calendar sync, webhooks, IFTTT |
| 31-34 | 5.7 | Open Banking | Plaid/TrueLayer, auto-import |
| 35-36 | 6.1 | Production Launch | Final deploy, monitoring, go-live |

## Effort Distribution

| Phase | Hours | Percentage |
|-------|-------|------------|
| Phase 1: Foundation & Security | ~100h | 15% |
| Phase 2: Quality & Testing | ~100h | 15% |
| Phase 3: Architecture & Performance | ~95h | 15% |
| Phase 4: Features & Polish | ~88h | 14% |
| Phase 5: Settings & AI Features | ~241h | 37% |
| Phase 6: Production Launch | ~15h | 2% |
| **Grand Total** | **~639h** | **100%** |

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

# PHASE 5: Settings & AI-Powered Features (Weeks 17-34)

> **Detailed Plan**: See [Settings Roadmap](../SETTINGS_ROADMAP.md) for comprehensive feature specifications.
> **Total Effort**: ~240 hours across 7 sprints

## Sprint 5.1: Profile & Preferences (Weeks 17-18) ✅ COMPLETE

### Overview
Implement core user settings with Profile and Preferences tabs.

| Task ID | Task Name | Priority | Hours | Dependencies | Status |
|---------|-----------|----------|-------|--------------|--------|
| **5.1.1** | **Profile Tab** | 🔴 | 8h | None | ✅ DONE |
| 5.1.1.1 | Edit user info (name, email) | 🔴 | 3h | - | ✅ DONE |
| 5.1.1.2 | Change password with current verification | 🔴 | 2h | - | ✅ DONE |
| 5.1.1.3 | Two-factor authentication setup | 🟡 | 3h | - | 🔜 Deferred to 5.4 |
| **5.1.2** | **Preferences Tab** | 🔴 | 8h | None | ✅ DONE |
| 5.1.2.1 | Currency selection (GBP, USD, EUR, UAH) | 🔴 | 2h | - | ✅ DONE |
| 5.1.2.2 | Date format preferences | 🟡 | 1h | - | ✅ DONE |
| 5.1.2.3 | Default view (list/calendar/cards) | 🟡 | 2h | - | ✅ DONE |
| 5.1.2.4 | Theme selection (light/dark/system) | 🟡 | 3h | - | ✅ DONE |
| **5.1.3** | **Backend APIs** | 🔴 | 8h | 5.1.1, 5.1.2 | ✅ DONE |
| 5.1.3.1 | PATCH /api/auth/profile endpoint | 🔴 | 2h | - | ✅ DONE |
| 5.1.3.2 | GET/PUT /api/v1/users/preferences endpoints | 🔴 | 2h | - | ✅ DONE |
| 5.1.3.3 | POST /api/auth/2fa/setup endpoint | 🟡 | 2h | - | 🔜 Deferred to 5.4 |
| 5.1.3.4 | POST /api/auth/2fa/verify endpoint | 🟡 | 2h | - | 🔜 Deferred to 5.4 |
| **5.1.4** | **Tests** | 🔴 | 4h | 5.1.3 | ✅ DONE |

**Sprint 5.1 Completed Features:**
- ✅ Profile management (name, email editing)
- ✅ Password change with current password verification
- ✅ User preferences API (GET/PUT /api/v1/users/preferences)
- ✅ Currency selection (GBP, USD, EUR, UAH + 10 more)
- ✅ Date format preferences (5 formats)
- ✅ Number format preferences (3 formats)
- ✅ Theme selection (light/dark/system)
- ✅ Default view preference (list/calendar/cards/agent)
- ✅ Compact mode toggle
- ✅ Week start preference (Monday/Sunday)
- ✅ Timezone selection
- ✅ Language preference
- ✅ 30 unit tests for user preferences
- ⏱️ **Actual: ~20 hours** (2FA deferred)

**Files Created/Modified:**
- `src/api/users.py` - User preferences API endpoints
- `src/schemas/user.py` - UserPreferencesResponse, UserPreferencesUpdate schemas
- `frontend/src/components/settings/ProfileSettings.tsx` - Profile form with password change
- `frontend/src/components/settings/PreferencesSettings.tsx` - Full preferences UI
- `frontend/src/app/settings/page.tsx` - Settings page with tabs
- `frontend/src/lib/auth-context.tsx` - Added refreshUser function
- `tests/unit/test_user_preferences.py` - 30 unit tests

---

## Sprint 5.2: Cards & Categories (Weeks 19-20) ✅ COMPLETE

### Overview
Enhance payment card management and implement custom categories with budgets.

| Task ID | Task Name | Priority | Hours | Dependencies | Status |
|---------|-----------|----------|-------|--------------|--------|
| **5.2.1** | **Enhanced Cards Tab** | 🔴 | 6h | None | ✅ DONE |
| 5.2.1.1 | Card list with spending breakdown | 🔴 | 2h | - | ✅ Already exists |
| 5.2.1.2 | Card color customization | 🟡 | 1h | - | ✅ Already exists |
| 5.2.1.3 | Card balance display | 🟠 | 2h | - | ✅ Already exists |
| 5.2.1.4 | Default card selection | 🟡 | 1h | - | ✅ DONE |
| **5.2.2** | **Categories Tab** | 🔴 | 10h | None | ✅ DONE |
| 5.2.2.1 | Category model and migration | 🔴 | 2h | - | ✅ DONE |
| 5.2.2.2 | Category CRUD API endpoints | 🔴 | 3h | 5.2.2.1 | ✅ DONE |
| 5.2.2.3 | Category UI with color/icon picker | 🔴 | 3h | 5.2.2.2 | ✅ DONE |
| 5.2.2.4 | Budget limits per category | 🟠 | 2h | 5.2.2.2 | ✅ DONE |
| **5.2.3** | **Category Assignment** | 🟠 | 6h | 5.2.2 | ✅ DONE |
| 5.2.3.1 | Update subscription model with category_id | 🔴 | 1h | - | ✅ DONE |
| 5.2.3.2 | Category selection in subscription forms | 🔴 | 2h | 5.2.3.1 | ✅ DONE |
| 5.2.3.3 | Auto-categorization suggestions (AI) | 🟡 | 3h | 5.2.3.2 | 🔜 Future |
| **5.2.4** | **Tests** | 🔴 | 4h | 5.2.3 | ✅ DONE |

**Sprint 5.2 Completed Features:**

*Category System:*
- ✅ Category model (`src/models/category.py`)
- ✅ Category table migration (`e86b93e0cf9a_add_categories_table.py`)
- ✅ Category schemas (`src/schemas/category.py`)
- ✅ Category service (`src/services/category_service.py`)
- ✅ Category API endpoints (`src/api/categories.py`)
  - GET /api/v1/categories - List categories
  - GET /api/v1/categories/with-stats - List with subscription counts
  - GET /api/v1/categories/budget-summary - Budget summary
  - POST /api/v1/categories - Create category
  - POST /api/v1/categories/defaults - Create default categories
  - PATCH /api/v1/categories/:id - Update category
  - DELETE /api/v1/categories/:id - Delete category
  - POST /api/v1/categories/assign - Assign subscription to category
  - POST /api/v1/categories/bulk-assign - Bulk assign
- ✅ Categories settings tab (`frontend/src/components/settings/CategoriesSettings.tsx`)
- ✅ Frontend API functions (`frontend/src/lib/api.ts`)
- ✅ Category unit tests (`tests/unit/test_categories.py`) - 45 tests
- ✅ category_id column added to subscriptions table
- ✅ CategorySelector component (`frontend/src/components/CategorySelector.tsx`)
- ✅ Category selection in Add/Edit subscription modals
- ✅ Default card and category preferences (`src/schemas/user.py`, `src/api/users.py`)
- ✅ Auto-populate default card/category in new subscriptions

*PaymentMode Refactor (2025-12-18):*
- ✅ **PaymentMode enum** (`src/models/subscription.py`) - Functional classification:
  - `recurring` - Regular recurring payment
  - `one_time` - Single payment
  - `debt` - Debt being paid off (with total_owed, remaining_balance, creditor)
  - `savings` - Savings goal (with target_amount, current_saved, recipient)
- ✅ **payment_mode column migration** (`369d67886082_add_payment_mode_column.py`)
- ✅ **Backend schema updates** (`src/schemas/subscription.py`)
- ✅ **Service layer updates** (`src/services/subscription_service.py`)
- ✅ **Frontend PaymentMode type** with labels and icons (`frontend/src/lib/api.ts`)
- ✅ **Filter toggle UI** - Mode vs Category filtering in SubscriptionList (`frontend/src/components/SubscriptionList.tsx`)
- ✅ **Add/Edit modals** with PaymentMode selector (`AddSubscriptionModal.tsx`, `EditSubscriptionModal.tsx`)
- ✅ **14 categories created** for Yurii with icons and colors:
  - 💳 Financial (19), ⚡ Productivity (8), 🎬 Entertainment (5), 💪 Health & Fitness (5)
  - 🔌 Utilities (5), 🏠 Housing (4), 🛒 Shopping (3), 💻 Technology (3)
  - 💼 Business (2), ☁️ Cloud Storage (2), 🛡️ Insurance (2), ⚖️ Legal (2)
  - 💬 Communication (1), 🖥️ Hosting (1)
- ✅ **62 subscriptions categorized** - All existing subscriptions assigned to categories
- 📋 **Refactor plan archived**: `.claude/plans/CATEGORY_REFACTOR_PLAN.md`

**Sprint 5.2 Deliverables:**
- ✅ Enhanced card management with spending breakdown
- ✅ Custom categories with colors and icons
- ✅ Budget limits per category with alerts
- ✅ Default card and category selection
- ✅ **PaymentMode system** - Separates functional modes from organizational categories
- ✅ **Filter toggle** - Switch between Mode and Category filtering on dashboard
- 🔜 AI-powered category suggestions (moved to future sprint)
- ⏱️ **Total: ~26 hours** (complete)

---

## Sprint 5.3: Notifications & Export (Weeks 21-22) ✅ COMPLETE

### Overview
Advanced notification preferences and data export functionality (builds on Sprint 4.3 Telegram).

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **5.3.1** | **Enhanced Notifications Tab** | 🔴 | 8h | Sprint 4.3 | Extended notifications |
| 5.3.1.1 | Email notification channel | ✅ DONE | 3h | - | Email reminders |
| 5.3.1.2 | Push notification setup (PWA) | ✅ DONE | 3h | - | Push notifications |
| 5.3.1.3 | Notification history view | ✅ DONE | 2h | - | History log |
| **5.3.2** | **Scheduled Reports** | ✅ DONE | 8h | 5.3.1 | Automated reports |
| 5.3.2.1 | Monthly spending report generation | ✅ DONE | 3h | - | Monthly report |
| 5.3.2.2 | Scheduled report delivery (email/Telegram) | ✅ DONE | 3h | 5.3.2.1 | Report scheduling |
| 5.3.2.3 | Report template customization | ✅ DONE | 2h | 5.3.2.2 | Custom templates |
| **5.3.3** | **Data Export Tab** | 🔴 | 8h | None | Export functionality |
| 5.3.3.1 | PDF report generation (ReportLab) | ✅ DONE | 4h | - | PDF export |
| 5.3.3.2 | Scheduled backup to cloud storage | ✅ DONE | 2h | - | Auto backup |
| 5.3.3.3 | Export history/audit log | ✅ DONE | 2h | - | Export log |
| **5.3.4** | **Tests** | ✅ DONE | 4h | 5.3.3 | Test coverage |

**Sprint 5.3 Deliverables:**
- ✅ Multi-channel notifications (Telegram + Email + Push)
- ✅ Automated monthly spending reports
- ✅ PDF report generation (2025-12-18)
- ✅ Scheduled cloud backups (2025-12-18)
- ✅ Email notifications (2025-12-18)
- ✅ 112 unit tests for Sprint 5.3 features (2025-12-19)
- ⏱️ **Total: ~28 hours**

*Sprint 5.3.3.1 Completed (2025-12-18):*
- ✅ **PDFReportService** (`src/services/pdf_report_service.py`) - ReportLab-based PDF generation:
  - Summary statistics (active/inactive counts, monthly/yearly totals)
  - Spending breakdown by category (table with monthly/yearly amounts)
  - Upcoming payments section (next 30 days with urgency highlighting)
  - Complete payments table (sorted by category, with status)
  - Currency symbol support (GBP, USD, EUR, UAH)
  - Page size options (A4, Letter)
  - User email personalization in header
- ✅ **PDF Export API** (`src/api/subscriptions.py`) - `GET /api/subscriptions/export/pdf`
  - Query params: `include_inactive`, `payment_type`, `page_size`
  - Returns application/pdf with Content-Disposition header
- ✅ **Frontend Integration** (`frontend/src/components/ImportExportModal.tsx`)
  - "Generate PDF Report" button in Export tab
  - Purple styling with document icon
  - Loading state during generation
- ✅ **API Client** (`frontend/src/lib/api.ts`) - `exportPdf()` function
- ✅ **35 unit tests** (`tests/unit/test_pdf_report.py`)
  - Service initialization, currency/page size config
  - Monthly conversion calculations
  - Report generation with various scenarios
  - Edge cases (empty, long names, zero amounts)

*Sprint 5.3.3.2 Completed (2025-12-18):*
- ✅ **BackupService** (`src/services/backup_service.py`) - Cloud backup service:
  - Google Cloud Storage (GCS) primary storage
  - Local file storage fallback for development
  - Compressed JSON backups (gzip)
  - Subscription serialization with all Money Flow fields
  - Backup metadata tracking (BackupMetadata model)
  - Retention policy with configurable days (default 30)
  - Backup listing and cleanup functionality
- ✅ **Scheduled Backup Task** (`src/core/tasks.py`) - `scheduled_cloud_backup`
  - Runs daily at 2 AM via ARQ cron
  - Backs up all active users
  - Logs success/failure counts
  - Automatic old backup cleanup
- ✅ **23 unit tests** (`tests/unit/test_backup_service.py`)
  - BackupMetadata and BackupResult models
  - Service initialization with custom options
  - Subscription serialization (all field types)
  - Local storage fallback
  - Compression and data format

*Sprint 5.3.1.1 Completed (2025-12-18):*
- ✅ **EmailService** (`src/services/email_service.py`) - Email notification service:
  - SMTP with TLS encryption via aiosmtplib
  - HTML formatted emails with responsive styling
  - Payment reminder emails with urgency classification (overdue, today, tomorrow, upcoming)
  - Daily digest emails with payment summary
  - Weekly digest emails with comprehensive overview
  - Test notification for verifying email setup
  - Currency symbol support (GBP, USD, EUR, UAH)
  - Plain text fallback for all emails
- ✅ **Email Tasks** (`src/core/tasks.py`) - Scheduled email notifications:
  - `send_email_reminders` - Daily at 9:30 AM
  - `send_email_daily_digest` - Daily at 8:30 AM
  - `send_email_weekly_digest` - Daily at 8:30 AM (filters by user's preferred day)
- ✅ **Config Settings** (`src/core/config.py`) - SMTP configuration:
  - `smtp_host`, `smtp_port`, `smtp_user`, `smtp_password`
  - `smtp_from_email`, `smtp_from_name`, `smtp_use_tls`
- ✅ **Database Migration** - Added `email_enabled` field to NotificationPreferences
- ✅ **28 unit tests** (`tests/unit/test_email_service.py`)
  - Service initialization and configuration
  - Email sending (success, failure, not configured)
  - Reminder emails (upcoming, overdue, today)
  - Digest emails (daily, weekly)
  - HTML template generation
  - Urgency classification

*Sprint 5.3.1.2 Completed (2025-12-19):*
- ✅ **PushService** (`src/services/push_service.py`) - Web Push notifications via VAPID:
  - VAPID authentication with pywebpush library
  - Push notification sending with title, body, icon, URL
  - Payment reminder pushes with urgency levels
  - Daily/weekly digest notifications
  - Test notification for verification
  - Currency symbol support
- ✅ **Push API Endpoints** (`src/api/notifications.py`):
  - `GET /api/v1/notifications/push/vapid-key` - Get VAPID public key
  - `POST /api/v1/notifications/push/subscribe` - Subscribe to push
  - `GET /api/v1/notifications/push/status` - Check subscription status
  - `DELETE /api/v1/notifications/push/unsubscribe` - Unsubscribe
  - `POST /api/v1/notifications/push/test` - Send test push
- ✅ **Push Schemas** (`src/schemas/notification.py`):
  - PushStatus, PushSubscriptionRequest, PushVapidKeyResponse
- ✅ **Database Migration** (`9377d33097e1_add_push_notification_fields.py`):
  - Added push_enabled, push_subscription, push_verified to NotificationPreferences
- ✅ **Config Settings** (`src/core/config.py`):
  - vapid_private_key, vapid_public_key, vapid_email
- ✅ **26 unit tests** (`tests/unit/test_push_service.py`)

*Sprint 5.3.1.3 Completed (2025-12-19):*
- ✅ **NotificationHistory Model** (`src/models/notification_history.py`):
  - Tracks all sent notifications for audit
  - Enums: NotificationChannel (telegram, email, push, in_app)
  - Enums: NotificationStatus (pending, sent, delivered, failed, read)
  - Enums: NotificationType (payment_reminder, overdue_alert, daily_digest, etc.)
  - Fields: user_id, subscription_id, channel, type, title, body, status, extra_data
- ✅ **NotificationHistory API** (`src/api/notifications.py`):
  - `GET /api/v1/notifications/history` - List with filters & pagination
  - `GET /api/v1/notifications/history/{id}` - Get single notification
  - `DELETE /api/v1/notifications/history/{id}` - Delete notification
  - `DELETE /api/v1/notifications/history` - Clear all history
- ✅ **Database Migration** (`d251356550ca_add_notification_history.py`)
- ✅ **Notification History Schemas** (`src/schemas/notification.py`)

*Sprint 5.3.2 Completed (2025-12-19):*
- ✅ **ScheduledReportService** (`src/services/scheduled_report_service.py`):
  - Daily report generation with subscription summary
  - Weekly report with spending trends and category breakdown
  - Monthly report with comprehensive analytics
  - PDF attachment support via EmailService
  - HTML email templates for each report type
- ✅ **Report Settings** in NotificationPreferences:
  - report_enabled, report_frequency, report_day, report_time, report_include_charts
- ✅ **Database Migration** (`a054d78f2aa5_add_scheduled_report_settings.py`)

*Sprint 5.3.3.3 Completed (2025-12-19):*
- ✅ **ExportHistory Model** (`src/models/export_history.py`):
  - Audit log for all export operations
  - Enums: ExportFormat (json, csv, pdf)
  - Enums: ExportType (full_backup, subscriptions, report, payment_history)
  - Enums: ExportStatus (pending, completed, failed)
  - Fields: user_id, export_type, format, filename, file_size, record_count, status
  - Methods: mark_completed(), mark_failed(), duration_seconds property
- ✅ **ExportHistory API** (`src/api/export_history.py`):
  - `GET /api/v1/exports/history` - List exports with pagination
  - `GET /api/v1/exports/history/stats` - Export statistics
  - `GET /api/v1/exports/history/{id}` - Get single export
  - `DELETE /api/v1/exports/history/{id}` - Delete export record
  - `DELETE /api/v1/exports/history` - Clear export history
- ✅ **Database Migration** (`36cdf62d465b_add_export_history.py`)
- ✅ **Export Schemas** (`src/schemas/export.py`)

---

## Sprint 5.4: Icons & AI Settings (Weeks 23-24) 🔜

### Overview
Intelligent icon management and AI assistant customization.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **5.4.1** | **Icons & Branding Tab** | 🟠 | 12h | None | Icon system |
| 5.4.1.1 | Icon cache model and storage | 🟠 | 2h | - | `icon_cache` table |
| 5.4.1.2 | External icon fetching (Clearbit, Logo.dev) | 🟠 | 4h | 5.4.1.1 | Icon APIs |
| 5.4.1.3 | AI icon generation (DALL-E/Stable Diffusion) | 🟡 | 4h | 5.4.1.2 | AI icons |
| 5.4.1.4 | Icon browser and search UI | 🟠 | 2h | 5.4.1.2 | Icon picker |
| **5.4.2** | **AI Assistant Tab** | 🟠 | 8h | None | AI settings |
| 5.4.2.1 | Natural language parsing preferences | 🟠 | 2h | - | NL settings |
| 5.4.2.2 | Smart categorization toggle | 🟠 | 1h | - | AI toggle |
| 5.4.2.3 | Conversation history management | 🟠 | 2h | - | History controls |
| 5.4.2.4 | AI model selection (if multiple) | 🟡 | 1h | - | Model selector |
| 5.4.2.5 | Suggestion frequency settings | 🟡 | 2h | - | Suggestion config |
| **5.4.3** | **Tests** | 🔴 | 5h | 5.4.2 | Test coverage |
| 5.4.4 | Icon Service Tests | 🔴 | 3h | - | Icon tests |
| 5.4.5 | AI Settings Tests | 🔴 | 2h | - | Settings tests |

**Sprint 5.4 Deliverables:**
- 📦 Smart icon fetching from brand APIs
- 📦 AI-generated custom icons
- 📦 AI assistant preference controls
- 📦 Conversation history management
- ⏱️ **Total: ~27 hours**

---

## Sprint 5.5: Smart Import - AI Features (Weeks 25-27) 🔜

### Overview
AI-powered data import from bank statements and email receipts.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **5.5.1** | **Bank Statement Import** | 🟠 | 24h | None | Statement parser |
| 5.5.1.1 | PDF text extraction (PyPDF2, pdfplumber) | 🟠 | 4h | - | PDF parsing |
| 5.5.1.2 | CSV/OFX/QIF format support | 🟠 | 4h | - | Format support |
| 5.5.1.3 | AI extraction of recurring patterns | 🟠 | 8h | 5.5.1.1 | Pattern detection |
| 5.5.1.4 | Preview and confirm import UI | 🟠 | 4h | 5.5.1.3 | Import wizard |
| 5.5.1.5 | Duplicate detection and merge | 🟠 | 4h | 5.5.1.4 | Deduplication |
| **5.5.2** | **Email Receipt Scanning** | 🟡 | 16h | None | Email scanner |
| 5.5.2.1 | Gmail OAuth integration | 🟡 | 4h | - | Gmail auth |
| 5.5.2.2 | Email parsing for subscriptions | 🟡 | 6h | 5.5.2.1 | Email parsing |
| 5.5.2.3 | Receipt template matching | 🟡 | 4h | 5.5.2.2 | Template matching |
| 5.5.2.4 | Outlook support | 🟢 | 2h | 5.5.2.2 | Outlook auth |
| **5.5.3** | **Tests** | 🔴 | 6h | 5.5.2 | Test coverage |

**Sprint 5.5 Deliverables:**
- 📦 Bank statement PDF/CSV import with AI extraction
- 📦 Automatic recurring payment detection
- 📦 Gmail/Outlook email scanning
- 📦 Smart duplicate detection
- ⏱️ **Total: ~46 hours**

---

## Sprint 5.6: Integrations (Weeks 28-30) 🔜

### Overview
Third-party calendar integration and webhook support.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **5.6.1** | **Calendar Integration** | 🟠 | 16h | None | Calendar sync |
| 5.6.1.1 | iCal feed generation | 🟠 | 4h | - | iCal endpoint |
| 5.6.1.2 | Google Calendar OAuth | 🟠 | 6h | - | Google sync |
| 5.6.1.3 | Apple Calendar support | 🟡 | 4h | - | Apple sync |
| 5.6.1.4 | Two-way sync logic | 🟡 | 2h | 5.6.1.2 | Bidirectional |
| **5.6.2** | **Webhooks** | 🟠 | 12h | None | Webhook system |
| 5.6.2.1 | Webhook subscription model | 🟠 | 2h | - | `webhooks` table |
| 5.6.2.2 | Webhook delivery service | 🟠 | 4h | 5.6.2.1 | Delivery queue |
| 5.6.2.3 | Event types (payment due, completed, etc.) | 🟠 | 3h | 5.6.2.2 | Event system |
| 5.6.2.4 | Webhook management UI | 🟠 | 3h | 5.6.2.3 | Webhook UI |
| **5.6.3** | **IFTTT/Zapier** | 🟡 | 8h | 5.6.2 | Automation |
| 5.6.3.1 | IFTTT trigger integration | 🟡 | 4h | - | IFTTT connect |
| 5.6.3.2 | Zapier app publication | 🟡 | 4h | - | Zapier app |
| **5.6.4** | **Tests** | 🔴 | 4h | 5.6.3 | Test coverage |

**Sprint 5.6 Deliverables:**
- 📦 iCal feed for calendar subscriptions
- 📦 Google Calendar bidirectional sync
- 📦 Webhook system for third-party integrations
- 📦 IFTTT/Zapier compatibility
- ⏱️ **Total: ~40 hours**

---

## Sprint 5.7: Open Banking (Weeks 31-34) 🔜

### Overview
Open Banking API integration for automatic transaction import (UK/EU focus).

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **5.7.1** | **Open Banking Setup** | 🟡 | 16h | None | Bank connections |
| 5.7.1.1 | Plaid/TrueLayer integration research | 🟡 | 4h | - | API research |
| 5.7.1.2 | Bank account linking flow | 🟡 | 6h | 5.7.1.1 | Link flow |
| 5.7.1.3 | Consent management | 🟡 | 4h | 5.7.1.2 | Consent UI |
| 5.7.1.4 | Secure credential storage | 🟡 | 2h | 5.7.1.2 | Credential vault |
| **5.7.2** | **Transaction Sync** | 🟡 | 18h | 5.7.1 | Auto-import |
| 5.7.2.1 | Transaction fetch and storage | 🟡 | 4h | - | Transaction API |
| 5.7.2.2 | Recurring pattern detection (ML) | 🟡 | 8h | 5.7.2.1 | ML patterns |
| 5.7.2.3 | Auto-subscription creation from transactions | 🟡 | 4h | 5.7.2.2 | Auto-create |
| 5.7.2.4 | Transaction categorization | 🟡 | 2h | 5.7.2.3 | Auto-category |
| **5.7.3** | **Multi-Bank Support** | 🟢 | 8h | 5.7.2 | Multiple banks |
| 5.7.3.1 | Multiple account management | 🟢 | 4h | - | Multi-account |
| 5.7.3.2 | Cross-bank duplicate detection | 🟢 | 4h | 5.7.3.1 | Deduplication |
| **5.7.4** | **Tests** | 🔴 | 4h | 5.7.3 | Test coverage |

**Sprint 5.7 Deliverables:**
- 📦 Open Banking account linking (Plaid/TrueLayer)
- 📦 Automatic transaction import
- 📦 ML-powered recurring payment detection
- 📦 Multi-bank account support
- ⏱️ **Total: ~46 hours**

---

## Phase 5 Summary

### Sprint Overview Table

| Sprint | Focus | Weeks | Hours | Status |
|--------|-------|-------|-------|--------|
| **5.1** | Profile & Preferences | 17-18 | 28h | 🔜 Not Started |
| **5.2** | Cards & Categories | 19-20 | 26h | 🔜 Not Started |
| **5.3** | Notifications & Export | 21-22 | 28h | 🔜 Not Started |
| **5.4** | Icons & AI Settings | 23-24 | 27h | 🔜 Not Started |
| **5.5** | Smart Import (AI) | 25-27 | 46h | 🔜 Not Started |
| **5.6** | Integrations | 28-30 | 40h | 🔜 Not Started |
| **5.7** | Open Banking | 31-34 | 46h | 🔜 Not Started |

**Phase 5 Total: ~241 hours across 18 weeks**

### Key Database Changes for Phase 5

```sql
-- Sprint 5.2: Categories
CREATE TABLE categories (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7),
    icon VARCHAR(100),
    budget_amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sprint 5.4: Icon Cache
CREATE TABLE icon_cache (
    id UUID PRIMARY KEY,
    service_name VARCHAR(200) UNIQUE,
    icon_url TEXT,
    brand_color VARCHAR(7),
    source VARCHAR(50),
    cached_at TIMESTAMP DEFAULT NOW()
);

-- Sprint 5.6: Webhooks
CREATE TABLE webhook_subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    url TEXT NOT NULL,
    events TEXT[] NOT NULL,
    secret VARCHAR(64),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sprint 5.7: Bank Connections
CREATE TABLE bank_connections (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    provider VARCHAR(50),
    institution_id VARCHAR(100),
    access_token_encrypted TEXT,
    consent_expires_at TIMESTAMP,
    last_sync_at TIMESTAMP
);
```

### Key API Endpoints for Phase 5

```
Settings APIs (Sprint 5.1):
- PATCH /api/auth/profile
- POST /api/auth/change-password
- GET/PUT /api/users/preferences
- POST /api/auth/2fa/setup
- POST /api/auth/2fa/verify

Category APIs (Sprint 5.2):
- GET/POST/PUT/DELETE /api/categories
- POST /api/categories/merge
- GET /api/categories/suggestions

Icon APIs (Sprint 5.4):
- GET /api/icons/search
- GET /api/icons/service/{name}
- POST /api/icons/generate (AI)

Import APIs (Sprint 5.5):
- POST /api/import/bank-statement
- GET /api/import/bank-statement/{job_id}
- POST /api/import/email/connect
- GET /api/import/email/scan

Integration APIs (Sprint 5.6):
- GET /api/calendar/ical
- POST /api/calendar/sync/google
- GET/POST/DELETE /api/webhooks
- POST /api/webhooks/test

Open Banking APIs (Sprint 5.7):
- POST /api/banking/connect
- GET /api/banking/accounts
- POST /api/banking/sync
- DELETE /api/banking/disconnect
```

---

# PHASE 6: Production Launch (Weeks 35-36)

> **Final Phase**: Production deployment after all features are complete
> **Total Effort**: ~15 hours

## Sprint 6.1: Production Launch (Weeks 35-36) 🔜

### Overview
Final production deployment with full verification and go-live procedures.

| Task ID | Task Name | Priority | Hours | Dependencies | Deliverable |
|---------|-----------|----------|-------|--------------|-------------|
| **6.1.1** | **Pre-Launch Verification** | 🔴 | 5h | Phase 5 | Launch ready |
| 6.1.1.1 | Final staging environment test | 🔴 | 1h | - | Staging test |
| 6.1.1.2 | Verify all environment variables | 🔴 | 0.5h | - | Env check |
| 6.1.1.3 | Verify database migrations | 🔴 | 0.5h | - | Migration check |
| 6.1.1.4 | Verify backup/restore procedures | 🔴 | 0.5h | - | Backup check |
| 6.1.1.5 | Verify monitoring/alerting | 🔴 | 0.5h | - | Monitoring check |
| 6.1.1.6 | Load test production config | 🔴 | 1h | - | Load test |
| 6.1.1.7 | Create rollback plan | 🔴 | 0.5h | - | Rollback plan |
| 6.1.1.8 | Security re-scan (if Phase 5 changes) | 🔴 | 0.5h | - | Security verify |
| **6.1.2** | **Production Deployment** | 🔴 | 4h | 6.1.1 | Go live |
| 6.1.2.1 | Deploy database migrations | 🔴 | 0.5h | - | DB migration |
| 6.1.2.2 | Deploy backend services | 🔴 | 1h | 6.1.2.1 | Backend live |
| 6.1.2.3 | Deploy frontend | 🔴 | 0.5h | 6.1.2.2 | Frontend live |
| 6.1.2.4 | Configure production Telegram webhook | 🔴 | 0.5h | 6.1.2.2 | Webhook setup |
| 6.1.2.5 | DNS and SSL verification | 🔴 | 0.5h | 6.1.2.3 | DNS/SSL check |
| 6.1.2.6 | CDN configuration (if applicable) | 🟡 | 0.5h | 6.1.2.3 | CDN setup |
| 6.1.2.7 | Production smoke tests | 🔴 | 0.5h | 6.1.2.5 | Smoke tests |
| **6.1.3** | **Post-Launch** | 🔴 | 6h | 6.1.2 | Stable launch |
| 6.1.3.1 | Monitor error rates (24h) | 🔴 | 2h | - | Error monitoring |
| 6.1.3.2 | Monitor performance metrics | 🔴 | 1h | - | Performance check |
| 6.1.3.3 | Address critical issues | 🔴 | 2h | 6.1.3.1 | Hotfixes |
| 6.1.3.4 | Post-mortem documentation | 🟠 | 1h | 6.1.3.3 | Post-mortem |

**Sprint 6.1 Deliverables:**
- 📦 Production environment fully deployed
- 📦 All services operational
- 📦 Monitoring and alerting verified
- 📦 Rollback plan tested
- 📦 Post-launch stability confirmed
- ⏱️ **Total: ~15 hours**

**Phase 6 Completion Checklist:**
```
□ Staging environment passes all tests
□ All environment variables configured
□ Database migrations applied
□ Backup/restore verified
□ Monitoring dashboards live
□ Rollback plan documented and tested
□ Production deployment successful
□ DNS/SSL configured
□ Smoke tests passing
□ 24h stability monitoring complete
□ Post-mortem documented
```

---

## Grand Summary

### All Phases Overview

| Phase | Name | Weeks | Hours | Status |
|-------|------|-------|-------|--------|
| **1** | Foundation & Security | 1-4 | ~100h | ✅ Complete |
| **2** | Quality & Testing | 5-8 | ~100h | ✅ Complete |
| **3** | Architecture & Performance | 9-12 | ~95h | ✅ Complete |
| **4** | Features & Polish | 13-16 | ~88h | 🔄 In Progress |
| **5** | Settings & AI Features | 17-34 | ~241h | 🔜 Not Started |
| **6** | Production Launch | 35-36 | ~15h | 🔜 Not Started |

**Grand Total: ~639 hours across 36 weeks**

---

*This master plan is a living document. Update status and adjust timelines as the project progresses.*
