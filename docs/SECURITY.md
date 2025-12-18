# Money Flow - Security Documentation

> Comprehensive security posture documentation and security practices

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Data Protection](#data-protection)
4. [API Security](#api-security)
5. [Infrastructure Security](#infrastructure-security)
6. [Dependency Security](#dependency-security)
7. [Security Testing](#security-testing)
8. [Incident Response](#incident-response)
9. [Compliance](#compliance)

---

## Security Overview

### Security Principles

Money Flow follows these core security principles:

1. **Defense in Depth** - Multiple layers of security controls
2. **Least Privilege** - Minimal access permissions
3. **Secure by Default** - Security enabled out of the box
4. **Fail Secure** - Errors default to denying access

### Security Features Summary

| Feature | Status | Implementation |
|---------|--------|----------------|
| JWT Authentication | Implemented | HS256 with configurable secrets |
| Password Hashing | Implemented | bcrypt with 12 rounds |
| Rate Limiting | Implemented | Redis-backed, per-endpoint limits |
| Input Validation | Implemented | Pydantic schemas |
| SQL Injection Prevention | Implemented | SQLAlchemy ORM |
| XSS Prevention | Implemented | Response encoding, CSP headers |
| CORS Protection | Implemented | Configurable allowed origins |
| Security Headers | Implemented | CSP, HSTS, X-Frame-Options |
| Secrets Management | Implemented | Environment variables, validation |
| Audit Logging | Implemented | structlog with request tracing |

---

## Authentication & Authorization

### JWT Token System

**Implementation**: `src/auth/jwt.py`

#### Token Types

| Type | Purpose | Expiration | Storage |
|------|---------|------------|---------|
| Access Token | API authentication | 30 minutes | Client memory/localStorage |
| Refresh Token | Obtain new access tokens | 7 days | httpOnly cookie recommended |

#### Security Features

1. **Token Type Validation**
   - Separate access and refresh token types
   - Prevents token substitution attacks
   - Type claim (`type`) required in all tokens

2. **Unique Token IDs (JTI)**
   - Each token has a unique `jti` claim
   - Enables token revocation tracking
   - UUIDv4 for unpredictability

3. **Required Claims**
   - `sub` (user_id) - Token subject
   - `email` - User email
   - `type` - Token type
   - `exp` - Expiration timestamp
   - `iat` - Issued at timestamp
   - `jti` - Unique token identifier

#### Token Validation

```python
# Always validate token type to prevent misuse
payload = decode_token(token, expected_type=TokenType.ACCESS)
```

### Password Security

**Implementation**: `src/auth/security.py`

#### Hashing Configuration

| Setting | Value | Rationale |
|---------|-------|-----------|
| Algorithm | bcrypt | Industry standard, resistant to GPU attacks |
| Rounds | 12 | 2^12 iterations, ~300ms hashing time |
| Salt | Automatic | Random salt per password |

#### Password Requirements

| Requirement | Value |
|-------------|-------|
| Minimum length | 8 characters |
| Maximum length | 128 characters |
| Uppercase | At least 1 |
| Lowercase | At least 1 |
| Digit | At least 1 |
| Special character | At least 1 |

#### Security Measures

1. **Constant-Time Comparison**
   - Prevents timing attacks
   - Uses passlib's secure comparison

2. **Hash Upgrade Support**
   - `needs_rehash()` for upgrading old hashes
   - Transparent algorithm migration

3. **Input Validation**
   - Length limits prevent DoS
   - Character validation before hashing

### Authorization System

**Implementation**: `src/auth/dependencies.py`

#### Dependency Chain

```
get_current_user
    └── get_current_active_user
            ├── require_admin
            ├── require_verified
            └── RoleChecker(roles)
```

#### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| USER | Standard user operations |
| ADMIN | Full administrative access |

### Account Security

1. **Account Locking**
   - 5 failed login attempts triggers lock
   - 15-minute automatic unlock
   - Password reset unlocks immediately

2. **Session Management**
   - Token blacklist for logout
   - Refresh token rotation recommended
   - Concurrent session limit (configurable)

---

## Data Protection

### Data at Rest

| Data Type | Protection |
|-----------|------------|
| Passwords | bcrypt hash (never stored plaintext) |
| User PII | Database encryption (if enabled) |
| Tokens | Blacklist stored in Redis |
| Backups | Encrypted with pgp/age |

### Data in Transit

| Component | Protection |
|-----------|------------|
| API Traffic | HTTPS/TLS 1.2+ |
| Database | SSL connections |
| Redis | AUTH + optional TLS |
| Internal | Docker network isolation |

### Sensitive Data Handling

**Logging Redaction** (`src/core/logging_config.py`):

Automatically redacted:
- API keys (`ANTHROPIC_API_KEY`, etc.)
- JWT tokens
- Passwords
- Email addresses (partial)
- Credit card numbers (if present)

```python
# Redaction patterns
REDACT_PATTERNS = [
    (r'"password":\s*"[^"]*"', '"password": "[REDACTED]"'),
    (r'Bearer\s+[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+', 'Bearer [REDACTED]'),
    # ... more patterns
]
```

### Data Isolation

- All queries filtered by `user_id`
- No cross-user data access
- Service layer enforces isolation
- Database indexes include `user_id`

---

## API Security

### Rate Limiting

**Implementation**: `src/middleware/rate_limiter.py` (slowapi + Redis)

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| GET requests | 100 | per minute |
| Write operations | 20 | per minute |
| Agent (AI) | 10 | per minute |
| Auth (login) | 5 | per minute |

### Input Validation

**Implementation**: Pydantic v2 schemas

1. **Type Validation**
   - Strong typing for all inputs
   - Automatic coercion with validation

2. **Custom Validators**
   - Email format validation
   - URL safety checks
   - Amount/currency validation
   - Date range validation

3. **XSS Prevention**
   - HTML entity encoding
   - Content-Type enforcement
   - CSP headers

4. **SQL Injection Prevention**
   - SQLAlchemy ORM (parameterized queries)
   - No raw SQL execution

### Security Headers

**Implementation**: `src/middleware/security_headers.py`

```python
# Applied to all responses
headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; ...",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}
```

### CORS Configuration

**Implementation**: `src/main.py`

| Environment | Allowed Origins |
|-------------|-----------------|
| Development | localhost:3001, localhost:3002 |
| Staging | staging.moneyflow.app |
| Production | moneyflow.app (no wildcards) |

### Prompt Injection Protection

**Implementation**: `src/middleware/prompt_injection.py`

**Blocked Patterns:**
- System prompt manipulation
- Role instruction injection
- Dangerous command keywords
- Markdown code blocks with system text

```python
BLOCKED_PATTERNS = [
    r"ignore\s+.*instructions",
    r"system\s*:\s*",
    r"<\|.*\|>",
    r"###\s*system",
    # ... 20+ patterns
]
```

---

## Infrastructure Security

### Container Security

1. **Non-root Users**
   - Containers run as non-root
   - Minimal base images (python:3.11-slim)

2. **Image Security**
   - Multi-stage builds
   - No secrets in images
   - Regular base image updates

3. **Network Isolation**
   - Internal Docker network
   - Only necessary ports exposed
   - Service-to-service via internal DNS

### Secret Management

**Required Secrets:**
- `SECRET_KEY` - Application secret
- `JWT_SECRET_KEY` - JWT signing key
- `DATABASE_URL` - Database connection
- `ANTHROPIC_API_KEY` - AI service
- `TELEGRAM_BOT_TOKEN` - Notifications

**Validation:**
- Secrets validated at startup
- Production blocks default values
- Environment-specific requirements

### Database Security

1. **Authentication**
   - Strong passwords required
   - SSL connections (production)
   - Connection pooling limits

2. **Access Control**
   - Application-specific user
   - Minimal required privileges
   - No superuser in application

3. **Data Protection**
   - Regular backups
   - Point-in-time recovery
   - Encryption at rest (optional)

---

## Dependency Security

### Python Dependencies

**Scanning Tool**: pip-audit

**Last Scan**: December 2025

**Results**: 0 vulnerabilities (after patching)

**Patched Packages**:
| Package | Old Version | New Version | CVE |
|---------|-------------|-------------|-----|
| filelock | 3.20.0 | 3.20.1 | CVE-2025-68146 |
| urllib3 | 2.5.0 | 2.6.2 | CVE-2025-66418, CVE-2025-66471 |
| setuptools | 65.5.0 | 80.9.0 | CVE-2022-40897, CVE-2024-6345 |

### Frontend Dependencies

**Scanning Tool**: npm audit

**Last Scan**: December 2025

**Results**: 0 vulnerabilities

### Automated Scanning

```yaml
# CI/CD Pipeline
- pip-audit on every PR
- npm audit on every PR
- Bandit security scan
- Safety dependency check
- Trivy container scan
```

---

## Security Testing

### Static Analysis

| Tool | Purpose | Integration |
|------|---------|-------------|
| Bandit | Python security linter | CI/CD |
| ESLint | JavaScript security rules | CI/CD |
| Ruff | Python linting | Pre-commit |

### Dynamic Testing

| Type | Tool | Frequency |
|------|------|-----------|
| API Fuzz Testing | Schemathesis | Every PR |
| Contract Testing | OpenAPI validation | Every PR |
| Load Testing | Locust | Pre-release |

### Penetration Testing

**Recommended Tools**:
- OWASP ZAP (automated scanning)
- Burp Suite (manual testing)

**Testing Schedule**:
- Pre-production launch
- Quarterly automated scans
- Annual manual penetration test

---

## Incident Response

### Detection

1. **Monitoring Alerts**
   - Error rate spikes
   - Failed login attempts
   - Unusual API patterns

2. **Log Analysis**
   - Structured logging with request IDs
   - Centralized in Loki
   - Anomaly detection

### Response Process

1. **Identify** - Confirm incident, assess scope
2. **Contain** - Isolate affected systems
3. **Eradicate** - Remove threat
4. **Recover** - Restore services
5. **Document** - Post-mortem analysis

**See**: [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md)

### Communication

| Severity | Notification |
|----------|--------------|
| SEV-1 (Critical) | Immediate, all stakeholders |
| SEV-2 (High) | Within 1 hour |
| SEV-3 (Medium) | Within 4 hours |
| SEV-4 (Low) | Next business day |

---

## Compliance

### Data Privacy

- User data isolated by user_id
- No cross-user data access
- Data export capability
- Account deletion capability

### Security Best Practices

Following industry standards:
- OWASP Top 10 mitigations
- NIST Cybersecurity Framework principles
- CWE/SANS Top 25 awareness

### Audit Trail

All security-relevant events logged:
- Login attempts (success/failure)
- Password changes
- Permission changes
- Data exports
- Account deletions

---

## Security Contacts

| Role | Responsibility |
|------|----------------|
| Security Lead | Security architecture, incident response |
| DevOps Lead | Infrastructure security, monitoring |
| Backend Lead | Application security, code review |

---

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT** create a public GitHub issue
2. **Email**: security@example.com
3. **Include**: Description, steps to reproduce, impact
4. **Response**: Within 48 hours

---

*Last Updated: December 2025*
*Security Review Version: 1.0.0*
