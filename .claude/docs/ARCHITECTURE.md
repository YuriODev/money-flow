# Money Flow - System Architecture

> **Version**: 2.0.0 (Updated December 2025)
> **Last Updated**: After Phase 4 completion

---

## Overview

Money Flow is a production-ready, microservices-ready application for tracking recurring payments. Built with a clean architecture pattern following Domain-Driven Design (DDD) principles with 6 distinct layers.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      User Interface Layer                            │
│                     (Next.js 16 Frontend)                            │
│                    Port 3001 (localhost)                             │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTP/REST API (v1)
                            │ WebSocket (notifications)
┌───────────────────────────▼─────────────────────────────────────────┐
│                      API Gateway Layer                               │
│                     (FastAPI Backend)                                │
│                    Port 8001 (localhost)                             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Middleware Stack                             │ │
│  │  Security Headers → Rate Limiter → Auth → Logging → Deprecation │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Route Handlers (API v1)                          │   │
│  │  /api/v1/subscriptions  /api/v1/agent  /api/v1/auth          │   │
│  │  /api/v1/cards          /api/v1/notifications                 │   │
│  │  /api/v1/health         /api/v1/calendar                      │   │
│  └─────────────┬─────────────────────┬───────────────────────────┘   │
│                │                     │                               │
│  ┌─────────────▼───────────┐  ┌─────▼──────────────────────────┐   │
│  │   Business Logic        │  │   Agentic Interface            │   │
│  │   (Services)            │  │   (RAG + Parser + Executor)    │   │
│  │   - SubscriptionSvc     │  │   - CommandParser (AI+Regex)   │   │
│  │   - UserService         │  │   - AgentExecutor              │   │
│  │   - CardService         │  │   - RAGService (Vector Search) │   │
│  │   - TelegramService     │  │   - PromptLoader (XML)         │   │
│  │   - CurrencyService     │  │   - SkillsEngine               │   │
│  └─────────────┬───────────┘  └─────┬──────────────────────────┘   │
│                │                     │                               │
│  ┌─────────────▼─────────────────────▼───────────────────────────┐  │
│  │              Data Access Layer (Async ORM)                     │  │
│  │                   SQLAlchemy 2.0                               │  │
│  │  - Connection pooling (5+10 overflow)                         │  │
│  │  - Async sessions with commit/rollback                        │  │
│  └─────────────┬─────────────────────────────────────────────────┘  │
└────────────────┼────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────────┐
│                     Data Layer (Multi-Store)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │ PostgreSQL  │  │   Redis     │  │   Qdrant    │                  │
│  │ Port 5433   │  │ Port 6379   │  │ Port 6333   │                  │
│  │             │  │             │  │             │                  │
│  │ - Users     │  │ - Sessions  │  │ - Vectors   │                  │
│  │ - Subs      │  │ - Cache     │  │ - Semantic  │                  │
│  │ - Cards     │  │ - Rate Lim  │  │   Search    │                  │
│  │ - Prefs     │  │ - Blacklist │  │ - RAG       │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      External Services                               │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐        │
│  │ Anthropic API  │  │ Telegram API   │  │   Sentry       │        │
│  │ (Claude Haiku) │  │ (Bot/Webhook)  │  │ (Error Track)  │        │
│  └────────────────┘  └────────────────┘  └────────────────┘        │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐                             │
│  │  Prometheus    │  │    Grafana     │                             │
│  │  (Metrics)     │  │  (Dashboards)  │                             │
│  └────────────────┘  └────────────────┘                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Layer Breakdown

### 1. Presentation Layer (Frontend)

**Technology**: Next.js 16 + TypeScript + Tailwind CSS v4

**Responsibilities**:
- User interface rendering
- Client-side state management (React Query)
- Form validation (client-side + Zod)
- API communication via Axios
- Route management (App Router)
- Authentication state (Context API)
- Theme management (light/dark)

**Key Components**:
```
frontend/src/
├── app/                       # Next.js app router
│   ├── page.tsx              # Main dashboard
│   ├── login/page.tsx        # Login page
│   ├── register/page.tsx     # Registration page
│   ├── layout.tsx            # Root layout
│   ├── globals.css           # Tailwind styles
│   └── providers.tsx         # React Query + Theme
├── components/               # React components
│   ├── Header.tsx            # Navigation + user menu
│   ├── StatsPanel.tsx        # Statistics cards
│   ├── SubscriptionList.tsx  # Payment list with filters
│   ├── PaymentCalendar.tsx   # Calendar view
│   ├── CardsDashboard.tsx    # Payment cards view
│   ├── AgentChat.tsx         # AI chat interface
│   ├── SettingsModal.tsx     # Settings (profile, notifications)
│   ├── AddSubscriptionModal.tsx
│   ├── EditSubscriptionModal.tsx
│   ├── ImportExportModal.tsx
│   └── ErrorBoundary.tsx
├── lib/                      # Utilities
│   ├── api.ts               # API client (v1 endpoints)
│   ├── auth-context.tsx     # Auth state management
│   ├── theme-context.tsx    # Theme provider
│   ├── service-icons.ts     # Service icon mappings
│   └── utils.ts             # Helper functions
└── hooks/                   # Custom hooks
    ├── useSubscriptions.ts
    └── useKeyboardShortcuts.ts
```

**Design Patterns**:
- Container/Presentational components
- Custom hooks for reusable logic
- React Query for server state (caching, refetch)
- Context API for auth and theme
- Protected routes with auto-redirect

### 2. API Layer (Backend - FastAPI)

**Technology**: FastAPI 0.104+ + Pydantic v2

**Responsibilities**:
- HTTP request/response handling
- Request validation (Pydantic schemas)
- Response serialization
- Error handling (centralized)
- API documentation (OpenAPI 3.0)
- Rate limiting (slowapi + Redis)
- API versioning (/api/v1/)

**Route Structure**:
```
src/api/
├── v1/                       # Versioned API
│   ├── __init__.py          # v1 router aggregation
│   └── (imports from parent)
├── auth.py                   # Authentication endpoints
│   - POST /api/v1/auth/register
│   - POST /api/v1/auth/login
│   - POST /api/v1/auth/refresh
│   - POST /api/v1/auth/logout
│   - GET  /api/v1/auth/me
├── subscriptions.py          # Payment CRUD
│   - GET    /api/v1/subscriptions
│   - POST   /api/v1/subscriptions
│   - GET    /api/v1/subscriptions/{id}
│   - PUT    /api/v1/subscriptions/{id}
│   - DELETE /api/v1/subscriptions/{id}
│   - GET    /api/v1/subscriptions/summary
│   - GET    /api/v1/subscriptions/upcoming
├── cards.py                  # Payment cards
│   - CRUD for payment cards
├── agent.py                  # AI agent
│   - POST /api/v1/agent/execute
├── notifications.py          # Notification settings
│   - GET/PUT /api/v1/notifications/preferences
│   - POST /api/v1/notifications/telegram/link
│   - DELETE /api/v1/notifications/telegram/unlink
│   - POST /api/v1/notifications/test
│   - POST /api/v1/notifications/trigger
├── calendar.py               # Calendar exports
│   - GET /api/v1/calendar/events
├── health.py                 # Health checks
│   - GET /health
│   - GET /health/live
│   - GET /health/ready
└── telegram.py               # Telegram webhook
    - POST /api/telegram/webhook
```

**Middleware Stack** (order matters):
1. `SecurityHeadersMiddleware` - CSP, HSTS, X-Frame-Options
2. `RateLimitMiddleware` - slowapi rate limiting
3. `CORSMiddleware` - Cross-origin requests
4. `RequestLoggingMiddleware` - Structured request logs
5. `APIVersionMiddleware` - Version header handling
6. `DeprecationMiddleware` - Legacy endpoint warnings

### 3. Business Logic Layer (Services)

**Technology**: Python 3.11+ (async/await)

**Responsibilities**:
- Business rules implementation
- Domain logic encapsulation
- Data transformation
- Inter-service communication
- Transaction management
- External API integration

**Services**:
```
src/services/
├── subscription_service.py   # Payment CRUD + analytics
│   - create, get_all, get_by_id, update, delete
│   - get_summary, get_upcoming
│   - User-scoped data isolation
├── user_service.py          # User management
│   - register, authenticate, update_profile
│   - Password hashing (bcrypt)
├── payment_card_service.py  # Card management
│   - CRUD for payment cards
│   - Card-subscription relationships
├── currency_service.py      # Currency conversion
│   - GBP, USD, EUR, UAH support
│   - Exchange rate management
├── telegram_service.py      # Telegram integration
│   - send_message, send_reminder
│   - send_daily_digest, send_weekly_digest
│   - Long polling for local dev
├── telegram_handler.py      # Bot command handling
│   - /start, /status, /help commands
│   - Verification code processing
├── rag_service.py           # RAG implementation
│   - Vector search (Qdrant)
│   - Context retrieval
│   - Session management
└── cache_service.py         # Redis caching
    - Response caching
    - Embedding caching
    - Session storage
```

**Service Pattern**:
```python
class SubscriptionService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id  # Data isolation

    async def create(self, data: SubscriptionCreate) -> Subscription:
        # 1. Validate business rules
        # 2. Calculate next payment date
        # 3. Create record (user_id enforced)
        # 4. Invalidate cache
        # 5. Return subscription

    async def get_summary(self) -> SubscriptionSummary:
        # User-scoped aggregations
        pass
```

### 4. Agentic Layer (AI Integration)

**Technology**: Anthropic Claude Haiku 4.5 + XML Prompts + RAG

**Responsibilities**:
- Natural language understanding
- Intent classification (CREATE, READ, UPDATE, DELETE, SUMMARY, etc.)
- Entity extraction (name, amount, frequency, currency, payment_type)
- Command execution
- Conversational context (RAG)
- Semantic search

**Components**:
```
src/agent/
├── prompts.xml              # XML-based prompt definitions
│   - System prompts
│   - Intent classification
│   - Entity extraction
│   - Response templates
├── prompt_loader.py         # XML parser and caching
├── parser.py               # Command parsing
│   - Primary: Claude AI parsing
│   - Fallback: Regex patterns
│   - Payment type detection
├── executor.py             # Command execution
│   - Intent routing
│   - Service invocation
│   - Response formatting
└── classifier.py           # Intent classification
    - 8 intents supported
    - Confidence scoring

src/services/rag_service.py  # RAG Implementation
├── Vector storage (Qdrant)
├── Embedding generation
├── Semantic search
├── Context retrieval
└── Session management

skills/                      # Custom Claude Skills
├── financial-analysis/      # Spending analysis
├── payment-reminder/        # Smart reminders
├── debt-management/         # Payoff strategies
└── savings-goal/           # Goal tracking
```

**Agentic Flow**:
```
User Message
    ↓
RAG Context Retrieval (semantic search)
    ↓
Parser (Claude AI + regex fallback)
    ↓
Intent Classification + Entity Extraction
    ↓
Executor (intent routing)
    ↓
Service Layer (business logic)
    ↓
Response + Context Storage
    ↓
User Response
```

### 5. Data Access Layer (ORM)

**Technology**: SQLAlchemy 2.0 (async) + Alembic

**Responsibilities**:
- Database abstractions
- Query building (async)
- Relationship management
- Transaction handling
- Connection pooling
- Migration management

**Models**:
```
src/models/
├── user.py                  # User model
│   - id, email, hashed_password
│   - full_name, is_active, is_verified
│   - preferences (JSONB)
│   - created_at, updated_at
├── subscription.py          # Subscription model
│   - All payment types supported
│   - user_id (FK), card_id (FK)
│   - payment_type enum
│   - Debt/Savings specific fields
├── payment_card.py          # Payment card model
│   - user_id (FK)
│   - name, last_four_digits
│   - card_type, is_default
├── notification.py          # NotificationPreferences
│   - user_id (one-to-one)
│   - Telegram settings
│   - Reminder settings
│   - Digest settings
├── payment_history.py       # Payment tracking
└── conversation.py          # RAG conversations
```

**Database Configuration**:
```python
# Connection Pool Settings
pool_size = 5           # Persistent connections
max_overflow = 10       # Additional on demand
pool_timeout = 30       # Wait for connection
pool_recycle = 1800     # Recycle after 30min
pool_pre_ping = True    # Verify connections
```

### 6. Data Layer (Multi-Store)

**PostgreSQL** (Port 5433):
- Primary data store
- ACID compliance
- Performance indexes
- Full-text search ready

**Redis** (Port 6379):
- Session storage
- Response caching (TTL-based)
- Rate limit counters
- Token blacklist
- Embedding cache

**Qdrant** (Port 6333):
- Vector embeddings
- Semantic search
- RAG context storage
- User-isolated collections

---

## Cross-Cutting Concerns

### 1. Authentication & Security

**JWT Token System**:
- Access tokens: 15 minutes
- Refresh tokens: 7 days
- Token blacklist on logout
- Auto-refresh on frontend

**Security Features**:
- bcrypt password hashing
- Rate limiting (slowapi)
- Prompt injection protection
- Input validation (Pydantic)
- Security headers (CSP, HSTS)
- CORS hardening

### 2. Error Handling

**Centralized Exception Hierarchy**:
```
MoneyFlowError (Base)
├── ValidationError (422)
├── AuthenticationError (401)
├── AuthorizationError (403)
├── NotFoundError (404)
├── ConflictError (409)
├── RateLimitError (429)
├── ExternalServiceError (503)
└── BusinessLogicError (400)
```

**Global Handler**: `src/middleware/exception_handler.py`
- Automatic status code mapping
- Structured error responses
- Sentry integration

### 3. Observability

**Logging**:
- Structured JSON logging (structlog)
- Request ID tracking
- User ID context
- Sensitive data redaction

**Metrics** (Prometheus):
- HTTP request metrics
- Business metrics
- AI agent latency
- RAG performance

**Monitoring**:
- Grafana dashboards
- Alertmanager rules
- Loki log aggregation

### 4. Resilience

**Patterns Implemented**:
- Circuit breaker (tenacity)
- Retry with backoff
- Timeouts
- Graceful degradation

### 5. Background Tasks

**ARQ (Async Redis Queue)**:
- Payment reminders
- Daily/weekly digests
- Cleanup jobs
- Cron scheduling

---

## Deployment Architecture

### Docker Compose (Local Dev)

```yaml
services:
  db:        PostgreSQL 15 (port 5433)
  redis:     Redis 7 (port 6379)
  qdrant:    Qdrant (port 6333)
  backend:   FastAPI (port 8001)
  frontend:  Next.js (port 3001)
  prometheus: Metrics (port 9090)
  grafana:   Dashboards (port 3003)
```

### Production (GCP Cloud Run)

```
┌─────────────────────────────────────────┐
│              Cloud Run                   │
│  ┌─────────────┐  ┌─────────────┐       │
│  │  Backend    │  │  Frontend   │       │
│  │  (FastAPI)  │  │  (Next.js)  │       │
│  └──────┬──────┘  └──────┬──────┘       │
└─────────┼────────────────┼──────────────┘
          │                │
┌─────────▼────────────────▼──────────────┐
│           Cloud SQL (PostgreSQL)         │
└──────────────────────────────────────────┘
          │
┌─────────▼────────────────────────────────┐
│           Memorystore (Redis)            │
└──────────────────────────────────────────┘
```

---

## Data Flow Examples

### 1. User Login Flow

```
Frontend                Backend                 Database
   │                       │                       │
   │──POST /auth/login────▶│                       │
   │                       │──Query user──────────▶│
   │                       │◀─────User data────────│
   │                       │                       │
   │                       │──Verify password      │
   │                       │──Generate JWT         │
   │◀──Access+Refresh─────│                       │
   │                       │                       │
   │──Store tokens         │                       │
```

### 2. AI Agent Command Flow

```
Frontend          Backend           AI Service        Database
   │                 │                   │                │
   │──"Add Netflix"─▶│                   │                │
   │                 │──Get RAG context──│                │
   │                 │──Parse command───▶│                │
   │                 │◀──Intent+Entities─│                │
   │                 │                   │                │
   │                 │──Create sub──────────────────────▶│
   │                 │◀─────────Subscription─────────────│
   │                 │                   │                │
   │                 │──Store context────│                │
   │◀──"Added!"─────│                   │                │
```

### 3. Telegram Notification Flow

```
Backend              Telegram API       User's Telegram
   │                      │                    │
   │──ARQ task trigger    │                    │
   │                      │                    │
   │──Query upcoming subs │                    │
   │                      │                    │
   │──sendMessage────────▶│                    │
   │                      │──Push notification─▶│
   │◀──Message sent───────│                    │
```

---

## Performance Considerations

### Database
- Connection pooling (5+10)
- Composite indexes on common queries
- User_id filtering for data isolation
- Eager loading for relationships

### Caching
- Response cache (60-300s TTL)
- Embedding cache (reduce AI calls)
- Rate limit counters in Redis

### API
- Async throughout
- Pagination for lists
- Efficient serialization (Pydantic v2)
- Response compression (gzip)

---

## Security Model

### Authentication
- JWT with short-lived access tokens
- Refresh token rotation
- Token blacklist on logout/password change

### Authorization
- User-scoped data (user_id filter)
- No cross-user data access
- Admin endpoints (future)

### Data Protection
- Passwords: bcrypt hashed
- Tokens: Redis blacklist
- API keys: Environment only
- PII: Redacted in logs

---

*Last Updated: December 2025*
*Architecture Version: 2.0.0*
