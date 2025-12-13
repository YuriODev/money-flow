# System Architecture

## Overview

Subscription Tracker is a modern, microservices-ready application built with a clean architecture pattern. The system follows Domain-Driven Design (DDD) principles and separates concerns into distinct layers.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   User Interface Layer                   │
│                  (Next.js Frontend)                       │
│              Port 3002 (localhost)                        │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP/REST API
                  │ (Proxied via Next.js)
┌─────────────────▼───────────────────────────────────────┐
│                  API Gateway Layer                        │
│                   (FastAPI Backend)                       │
│                Port 8001 (localhost)                      │
│                                                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Route Handlers (API)                    │   │
│  │  - /api/subscriptions  - /api/agent               │   │
│  └────────────┬────────────────┬─────────────────────┘   │
│               │                │                          │
│  ┌────────────▼────────┐  ┌───▼──────────────────────┐  │
│  │  Business Logic      │  │   Agentic Interface       │  │
│  │  (Services)          │  │   (Parser/Executor)       │  │
│  │  - Subscription Svc  │  │   - CommandParser         │  │
│  │  - Currency Svc      │  │   - AgentExecutor         │  │
│  └────────────┬─────────┘  │   - PromptLoader          │  │
│               │             └───┬──────────────────────┘  │
│               │                 │                          │
│  ┌────────────▼─────────────────▼─────────────────────┐  │
│  │           Data Access Layer (ORM)                   │  │
│  │                SQLAlchemy 2.0                        │  │
│  └────────────┬─────────────────────────────────────────┘ │
└───────────────┼───────────────────────────────────────────┘
                │
┌───────────────▼───────────────────────────────────────────┐
│                  Data Persistence Layer                    │
│                  PostgreSQL Database                        │
│                   Port 5433 (localhost)                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  External Services                        │
│  - Anthropic Claude API (Haiku 4.5)                      │
│  - Currency Exchange APIs (Future)                       │
└─────────────────────────────────────────────────────────┘
```

## Layer Breakdown

### 1. Presentation Layer (Frontend)

**Technology**: Next.js 14 + TypeScript + Tailwind CSS

**Responsibilities**:
- User interface rendering
- Client-side state management (React Query)
- Form validation (client-side)
- API communication
- Route management

**Key Components**:
```
frontend/src/
├── app/                    # Next.js app router
│   ├── page.tsx           # Main dashboard
│   ├── layout.tsx         # Root layout
│   └── providers.tsx      # React Query provider
├── components/            # React components
│   ├── Header.tsx
│   ├── StatsPanel.tsx
│   ├── SubscriptionList.tsx
│   ├── AddSubscriptionModal.tsx
│   └── AgentChat.tsx
├── lib/                   # Utilities
│   ├── api.ts            # API client
│   └── utils.ts          # Helper functions
└── hooks/                # Custom hooks
    └── useSubscriptions.ts
```

**Design Patterns**:
- Container/Presentational components
- Custom hooks for reusable logic
- React Query for server state
- Context API for global UI state

### 2. API Layer (Backend - FastAPI)

**Technology**: FastAPI + Pydantic

**Responsibilities**:
- HTTP request/response handling
- Request validation
- Response serialization
- Error handling
- API documentation (Swagger/OpenAPI)

**Key Endpoints**:
```
src/api/
├── subscriptions.py      # CRUD endpoints
│   - GET    /api/subscriptions
│   - POST   /api/subscriptions
│   - GET    /api/subscriptions/{id}
│   - PUT    /api/subscriptions/{id}
│   - DELETE /api/subscriptions/{id}
│   - GET    /api/subscriptions/summary
│
└── agent.py             # AI agent endpoints
    - POST /api/agent/execute
```

### 3. Business Logic Layer (Services)

**Technology**: Python 3.11+ (async)

**Responsibilities**:
- Business rules implementation
- Domain logic
- Data transformation
- Inter-service communication
- Transaction management

**Services**:
```
src/services/
├── subscription_service.py    # Subscription CRUD + analytics
├── currency_service.py        # Currency conversion
└── notification_service.py    # (Future) Email notifications
```

**Example Service Pattern**:
```python
class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: SubscriptionCreate) -> Subscription:
        # 1. Validate data
        # 2. Calculate next payment date
        # 3. Create record
        # 4. Return subscription

    async def get_summary(self) -> SubscriptionSummary:
        # 1. Query all active subscriptions
        # 2. Calculate totals by frequency
        # 3. Group by category
        # 4. Find upcoming payments
        # 5. Return summary
```

### 4. Agentic Layer (AI Integration)

**Technology**: Anthropic Claude Haiku 4.5 + XML Prompts

**Responsibilities**:
- Natural language understanding
- Intent classification
- Entity extraction
- Command execution

**Components**:
```
src/agent/
├── prompts.xml          # XML-based prompt definitions
├── prompt_loader.py     # XML parser and loader
├── parser.py           # Command parsing (AI + regex)
└── executor.py         # Command execution
```

**Flow**:
```
User Command
    ↓
Parser (AI/Regex)
    ↓
Intent + Entities
    ↓
Executor
    ↓
Service Layer
    ↓
Response
```

### 5. Data Access Layer (ORM)

**Technology**: SQLAlchemy 2.0 (async)

**Responsibilities**:
- Database abstractions
- Query building
- Relationship management
- Transaction handling

**Models**:
```
src/models/
├── subscription.py      # Subscription ORM model
└── __init__.py
```

**Schemas** (Pydantic):
```
src/schemas/
├── subscription.py      # Request/Response schemas
│   - SubscriptionBase
│   - SubscriptionCreate
│   - SubscriptionUpdate
│   - SubscriptionResponse
│   - SubscriptionSummary
└── __init__.py
```

### 6. Database Layer

**Technology**: PostgreSQL 15

**Responsibilities**:
- Data persistence
- ACID compliance
- Indexing
- Full-text search (future)

**Schema**:
```sql
CREATE TABLE subscriptions (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'GBP',
    frequency VARCHAR(20) NOT NULL,
    frequency_interval INTEGER DEFAULT 1,
    start_date DATE NOT NULL,
    next_payment_date DATE NOT NULL,
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_active ON subscriptions(is_active);
CREATE INDEX idx_subscriptions_next_payment ON subscriptions(next_payment_date);
CREATE INDEX idx_subscriptions_category ON subscriptions(category);
```

## Cross-Cutting Concerns

### 1. Configuration Management

**File**: `src/core/config.py`

```python
class Settings(BaseSettings):
    # Database
    database_url: str

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    cors_origins: list[str]

    # External Services
    anthropic_api_key: str

    class Config:
        env_file = ".env"
```

### 2. Error Handling

**Strategy**: Hierarchical exception handling

```
ApplicationException (Base)
├── ValidationException
├── NotFoundException
├── CurrencyConversionException
└── AIParsingException
```

### 3. Logging

**Configuration**: Structured logging with context

```python
logger = logging.getLogger(__name__)
logger.info("Processing subscription", extra={
    "subscription_id": sub.id,
    "user_id": user.id
})
```

### 4. Dependency Injection

**Pattern**: FastAPI dependency injection

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

@router.post("/subscriptions")
async def create(
    data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db)
):
    service = SubscriptionService(db)
    return await service.create(data)
```

## Data Flow Examples

### Example 1: Create Subscription via UI

```
1. User fills form in AddSubscriptionModal
2. Form validates client-side
3. React Query mutation calls api.subscriptions.create()
4. Next.js proxies to http://backend:8000/api/subscriptions
5. FastAPI validates request body (Pydantic)
6. SubscriptionService.create() called
7. Service calculates next_payment_date
8. SQLAlchemy creates database record
9. Response serialized to SubscriptionResponse
10. Frontend updates cache and shows success
```

### Example 2: Natural Language Command

```
1. User types: "Add Netflix for £15.99 monthly"
2. AgentChat sends to /api/agent/execute
3. AgentExecutor creates CommandParser
4. Parser loads XML prompts
5. Claude Haiku 4.5 analyzes command
6. Returns: {intent: "CREATE", entities: {...}}
7. Executor calls SubscriptionService.create()
8. Database record created
9. Success message returned
10. UI shows new subscription
```

## Security Architecture

### 1. Input Validation

- **Frontend**: Client-side validation (Zod/Yup)
- **Backend**: Pydantic schemas (strict validation)
- **Database**: SQL injection protection via ORM

### 2. Authentication (Future)

```
Planned:
- JWT tokens
- OAuth2 with Password (and hashing)
- API key authentication
```

### 3. CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Scalability Considerations

### Current (Monolith)

```
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │
┌──────▼──────┐
│  Backend    │
└──────┬──────┘
       │
┌──────▼──────┐
│  Database   │
└─────────────┘
```

### Future (Microservices)

```
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │
┌──────▼────────────────────┐
│    API Gateway            │
└─┬────┬────────┬──────────┘
  │    │        │
  ▼    ▼        ▼
┌────┐┌────┐  ┌─────────┐
│Sub ││Curr│  │ AI Agent│
│Svc ││Svc │  │ Service │
└─┬──┘└─┬──┘  └────┬────┘
  │     │          │
  ▼     ▼          ▼
┌────────────────────┐
│   Database Layer   │
└────────────────────┘
```

## Performance Optimization

### 1. Database

- Indexes on frequently queried fields
- Connection pooling (SQLAlchemy)
- Query optimization
- Read replicas (future)

### 2. Caching

- React Query cache (frontend)
- Redis cache (future, backend)
- Static generation (Next.js)

### 3. Async Operations

- All I/O is async
- Concurrent request handling
- Background jobs (future: Celery)

## Monitoring & Observability

### Planned

1. **Metrics**: Prometheus + Grafana
2. **Logging**: Structured logs → ELK stack
3. **Tracing**: OpenTelemetry
4. **Alerts**: PagerDuty integration

---

**Last Updated**: 2025-11-28
**Version**: 1.0
**Status**: Production-ready monolith, microservices-ready architecture
