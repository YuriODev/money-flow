# Money Flow - Comprehensive Project Documentation

> **Complete Technical Documentation for the Money Flow (Subscription Tracker) Application**
>
> **Version**: 2.0.0
> **Last Updated**: December 13, 2025
> **Author**: Yurii Jupus
> **Status**: Production-Ready

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Overview](#2-project-overview)
3. [Architecture Overview](#3-architecture-overview)
4. [Technology Stack](#4-technology-stack)
5. [Complete File Structure](#5-complete-file-structure)
6. [Backend Deep Dive](#6-backend-deep-dive)
7. [Frontend Deep Dive](#7-frontend-deep-dive)
8. [Database Schema](#8-database-schema)
9. [API Reference](#9-api-reference)
10. [AI Agent System](#10-ai-agent-system)
11. [RAG Implementation](#11-rag-implementation)
12. [Docker Infrastructure](#12-docker-infrastructure)
13. [Data Flow Diagrams](#13-data-flow-diagrams)
14. [Payment Types](#14-payment-types)
15. [Currency System](#15-currency-system)
16. [Testing Strategy](#16-testing-strategy)
17. [Development Workflow](#17-development-workflow)
18. [Deployment Guide](#18-deployment-guide)
19. [Configuration Reference](#19-configuration-reference)
20. [Troubleshooting](#20-troubleshooting)
21. [Future Roadmap](#21-future-roadmap)

---

## 1. Executive Summary

**Money Flow** is a comprehensive recurring payment management application designed to track all types of financial outflows - from streaming subscriptions to mortgage payments, debts, savings goals, and transfers. The application features an **agentic natural language interface** powered by Claude Haiku 4.5, enabling users to manage their finances through conversational commands like "Add Netflix for £15.99 monthly" or "How much do I owe in total?"

### Key Differentiators

| Feature | Description |
|---------|-------------|
| **9 Payment Types** | Comprehensive coverage: subscriptions, housing, utilities, professional services, insurance, debts, savings, transfers, one-time payments |
| **Natural Language Interface** | Claude Haiku 4.5 powered agent with tool-use capability |
| **RAG-Powered Context** | Semantic search and conversation memory using Qdrant vector database |
| **Multi-Currency Support** | GBP (default), USD, EUR, UAH with live exchange rates |
| **Installment Tracking** | Track payment plans with progress indicators |
| **Debt/Savings Goals** | Visual progress tracking for financial goals |
| **Payment Cards** | Link payments to specific cards with balance tracking |
| **Calendar View** | Visual payment schedule with monthly summaries |
| **Import/Export** | Full backup and restore with JSON/CSV support |

### Current Metrics

- **62 Active Payments** tracked
- **9 Payment Types** supported
- **4 Currencies** with conversion
- **5 Docker Services** orchestrated
- **7 API Routers** with 30+ endpoints
- **13 Backend Services** for business logic
- **10 React Components** for UI
- **18+ Test Modules** with comprehensive coverage

---

## 2. Project Overview

### 2.1 Project Identity

```
Project Name:     Money Flow (formerly Subscription Tracker)
Repository:       subscription-tracker/
Version:          2.0.0
License:          MIT
Python Version:   3.11+
Node Version:     18+
```

### 2.2 Problem Statement

Traditional subscription trackers focus narrowly on digital services like Netflix or Spotify. Real-world financial management requires tracking diverse payment types:

- **Fixed Costs**: Rent, mortgage, insurance
- **Variable Costs**: Utilities (electric, gas, water)
- **Debts**: Credit cards, loans, money owed to friends
- **Savings**: Goal-based saving with targets
- **Transfers**: Regular support to family members

Money Flow addresses this by providing a unified platform for **all recurring payments** with intelligent categorization and AI-powered management.

### 2.3 Solution Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │   List      │ │  Calendar   │ │   Cards     │ │   Agent     │   │
│  │   View      │ │   View      │ │  Dashboard  │ │   Chat      │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         NEXT.JS FRONTEND                             │
│  React 19 │ TypeScript │ TanStack Query │ Tailwind CSS │ Framer    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ HTTP/JSON
┌─────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND                              │
│  7 API Routers │ Pydantic Validation │ CORS │ Async/Await           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
         ▼                          ▼                          ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   POSTGRESQL    │    │     REDIS       │    │     QDRANT      │
│  Primary Data   │    │   Cache Layer   │    │  Vector Store   │
│  Subscriptions  │    │   Embeddings    │    │  RAG Search     │
│  Payment Cards  │    │   Query Cache   │    │  Conversations  │
│  History        │    │   Sessions      │    │  Semantic       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 3. Architecture Overview

### 3.1 Six-Layer Architecture

The application follows a clean six-layer architecture pattern:

```
┌────────────────────────────────────────────────────────────────┐
│ Layer 1: PRESENTATION                                          │
│ - React Components (AddSubscriptionModal, PaymentCalendar)     │
│ - Custom Hooks (useCurrencyFormat)                             │
│ - State Management (TanStack Query, React Context)             │
│ - Styling (Tailwind CSS, Framer Motion)                        │
├────────────────────────────────────────────────────────────────┤
│ Layer 2: API GATEWAY                                           │
│ - FastAPI Application (src/main.py)                            │
│ - Route Handlers (7 routers)                                   │
│ - Request/Response Validation (Pydantic)                       │
│ - CORS Middleware                                              │
├────────────────────────────────────────────────────────────────┤
│ Layer 3: AGENTIC INTERFACE                                     │
│ - ConversationalAgent (Claude Haiku 4.5)                       │
│ - CommandParser (NL → Intent + Entities)                       │
│ - AgentExecutor (Intent → Database Operations)                 │
│ - PromptLoader (XML-based prompts)                             │
├────────────────────────────────────────────────────────────────┤
│ Layer 4: BUSINESS LOGIC                                        │
│ - SubscriptionService (CRUD + analytics)                       │
│ - PaymentService (history, calendar)                           │
│ - CurrencyService (conversion, rates)                          │
│ - RAGService (context, search)                                 │
│ - InsightsService (analytics, recommendations)                 │
├────────────────────────────────────────────────────────────────┤
│ Layer 5: DATA ACCESS                                           │
│ - SQLAlchemy 2.0 ORM (async sessions)                          │
│ - Qdrant Client (vector operations)                            │
│ - Redis Client (caching)                                       │
│ - Sentence Transformers (embeddings)                           │
├────────────────────────────────────────────────────────────────┤
│ Layer 6: PERSISTENCE                                           │
│ - PostgreSQL 15 (relational data)                              │
│ - Redis 7 (cache, sessions)                                    │
│ - Qdrant 1.7.4 (vector embeddings)                             │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Interaction Flow

```
User Input → Frontend → API Gateway → Service Layer → Database
                ↓           ↓              ↓
              React      FastAPI       SQLAlchemy
              Query      Pydantic      PostgreSQL
                ↓           ↓              ↓
            State        Validation    Persistence
            Update       Response      Commit
                ↓           ↓              ↓
              UI ← ─ ─ ─ JSON ← ─ ─ ─ Data ←
            Update      Response      Retrieved
```

### 3.3 Network Architecture

All services communicate via Docker bridge network:

```
┌─────────────────────────────────────────────────────────────────┐
│                    subscription-network (bridge)                 │
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   frontend   │────▶│   backend    │────▶│      db      │    │
│  │  :3000→:3002 │     │  :8000→:8001 │     │  :5432→:5433 │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│                              │                                   │
│                              │                                   │
│                    ┌─────────┴─────────┐                        │
│                    │                   │                        │
│              ┌──────────────┐   ┌──────────────┐               │
│              │    redis     │   │    qdrant    │               │
│              │  :6379→:6380 │   │  :6333/:6334 │               │
│              └──────────────┘   └──────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Technology Stack

### 4.1 Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Core language |
| **FastAPI** | ≥0.109.0 | Web framework |
| **SQLAlchemy** | ≥2.0.25 | ORM with async support |
| **Pydantic** | ≥2.5.0 | Data validation |
| **Alembic** | ≥1.13.0 | Database migrations |
| **Anthropic** | ≥0.18.0 | Claude API client |
| **asyncpg** | ≥0.29.0 | PostgreSQL async driver |
| **Uvicorn** | ≥0.27.0 | ASGI server |
| **python-dateutil** | ≥2.8.2 | Date calculations |
| **httpx** | ≥0.26.0 | Async HTTP client |

### 4.2 RAG Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Qdrant** | 1.7.4 | Vector database |
| **Sentence Transformers** | ≥2.2.0 | Text embeddings |
| **all-MiniLM-L6-v2** | - | Embedding model (384 dims) |
| **Redis** | ≥5.0.0 | Cache layer |
| **PyTorch** | ≥2.0.0 | ML framework |

### 4.3 Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.0.5 | React framework |
| **React** | 19.2.0 | UI library |
| **TypeScript** | 5.7.0 | Type safety |
| **TanStack Query** | 5.62.0 | Server state management |
| **Tailwind CSS** | 4.1.17 | Utility-first styling |
| **Framer Motion** | 12.23.24 | Animations |
| **Lucide React** | 0.460.0 | Icon library |
| **date-fns** | 4.1.0 | Date utilities |
| **Axios** | 1.7.7 | HTTP client |
| **clsx** | 2.1.1 | Class merging |

### 4.4 Infrastructure

| Technology | Version | Purpose |
|------------|---------|---------|
| **Docker** | Latest | Containerization |
| **Docker Compose** | Latest | Multi-container orchestration |
| **PostgreSQL** | 15-alpine | Primary database |
| **Redis** | 7-alpine | Caching |
| **Qdrant** | 1.7.4 | Vector storage |

### 4.5 Development Tools

| Tool | Purpose |
|------|---------|
| **Ruff** | Python linting and formatting |
| **MyPy** | Static type checking |
| **Pytest** | Testing framework |
| **pytest-asyncio** | Async test support |
| **pytest-cov** | Coverage reporting |
| **pre-commit** | Git hooks |
| **ESLint** | JavaScript linting |

---

## 5. Complete File Structure

```
subscription-tracker/
│
├── 📁 .claude/                          # Development configuration
│   ├── CHANGELOG.md                     # Complete development history
│   ├── README.md                        # .claude directory overview
│   ├── settings.local.json              # Local Claude Code settings
│   │
│   ├── 📁 docs/                         # Documentation
│   │   ├── ARCHITECTURE.md              # System architecture
│   │   ├── MCP_SETUP.md                 # Model Context Protocol guide
│   │   ├── PRE_COMMIT_HOOKS.md          # Git hooks documentation
│   │   ├── PYTHON_STANDARDS.md          # Python coding standards
│   │   ├── RAG_CONSIDERATIONS.md        # RAG analysis and patterns
│   │   └── TYPESCRIPT_STANDARDS.md      # TypeScript/React standards
│   │
│   ├── 📁 plans/                        # Implementation plans
│   │   ├── MONEY_FLOW_REFACTOR_PLAN.md  # Payment types expansion
│   │   ├── PAYMENT_TRACKING_PLAN.md     # Calendar and history
│   │   ├── RAG_PLAN.md                  # RAG implementation (4 phases)
│   │   └── SUBSCRIPTION_TEMPLATES_PLAN.md # Template system
│   │
│   ├── 📁 scripts/                      # Utility scripts
│   │   ├── README.md                    # Script documentation
│   │   ├── check_code_quality.sh        # Ruff + MyPy runner
│   │   ├── db_reset.sh                  # Database reset utility
│   │   ├── run_tests.sh                 # Test runner with coverage
│   │   └── setup_dev.sh                 # Development setup
│   │
│   └── 📁 templates/                    # Code templates
│       ├── README.md                    # Template usage guide
│       ├── fastapi_router.py            # API router template
│       ├── python_service.py            # Service class template
│       ├── react_component.tsx          # React component template
│       └── react_hook.ts                # Custom hook template
│
├── 📁 deploy/                           # Deployment configurations
│   └── 📁 gcp/                          # Google Cloud Platform
│       ├── README.md                    # GCP deployment guide
│       └── cloudbuild.yaml              # Cloud Build config
│
├── 📁 frontend/                         # Next.js Application
│   ├── Dockerfile                       # Frontend container
│   ├── package.json                     # NPM dependencies
│   ├── package-lock.json                # Lockfile
│   ├── tsconfig.json                    # TypeScript config
│   ├── postcss.config.mjs               # PostCSS config
│   ├── .eslintrc.json                   # ESLint config
│   │
│   └── 📁 src/
│       ├── 📁 app/                      # Next.js App Router
│       │   ├── globals.css              # Global styles
│       │   ├── layout.tsx               # Root layout
│       │   ├── page.tsx                 # Main dashboard
│       │   └── providers.tsx            # Context providers
│       │
│       ├── 📁 components/               # React Components
│       │   ├── AddSubscriptionModal.tsx # Create payment modal
│       │   ├── AgentChat.tsx            # AI chat interface
│       │   ├── CardsDashboard.tsx       # Payment cards view
│       │   ├── CurrencySelector.tsx     # Currency dropdown
│       │   ├── EditSubscriptionModal.tsx # Edit payment modal
│       │   ├── Header.tsx               # Navigation header
│       │   ├── ImportExportModal.tsx    # Import/export UI
│       │   ├── PaymentCalendar.tsx      # Calendar view
│       │   ├── StatsPanel.tsx           # Statistics dashboard
│       │   └── SubscriptionList.tsx     # Main list view
│       │
│       ├── 📁 hooks/                    # Custom React Hooks
│       │   └── useCurrencyFormat.ts     # Currency formatting
│       │
│       └── 📁 lib/                      # Utilities
│           ├── api.ts                   # Backend API client
│           ├── currency-context.tsx     # Currency state
│           ├── service-icons.ts         # 150+ service icons
│           └── utils.ts                 # Helper functions
│
├── 📁 scripts/                          # Python scripts
│   ├── migrate_payment_types.py         # Type migration script
│   └── seed_data.py                     # Database seeding
│
├── 📁 src/                              # Backend Application
│   ├── __init__.py
│   ├── main.py                          # FastAPI entry point
│   │
│   ├── 📁 agent/                        # Agentic Interface
│   │   ├── __init__.py
│   │   ├── conversational_agent.py      # Claude integration
│   │   ├── executor.py                  # Command execution
│   │   ├── parser.py                    # NL parsing
│   │   ├── prompt_loader.py             # Prompt management
│   │   │
│   │   ├── 📁 prompts/                  # XML Prompts
│   │   │   ├── command_patterns.xml     # Pattern definitions
│   │   │   ├── command_prompt_template.xml
│   │   │   ├── currency.xml             # Currency handling
│   │   │   ├── response_templates.xml   # Response formats
│   │   │   └── system.xml               # System prompt
│   │   │
│   │   └── 📁 utils/                    # Agent utilities
│   │       ├── __init__.py
│   │       ├── prompt_builder.py        # Prompt construction
│   │       └── xml_parser.py            # XML parsing
│   │
│   ├── 📁 api/                          # REST API Routers
│   │   ├── __init__.py
│   │   ├── agent.py                     # Agent endpoints
│   │   ├── analytics.py                 # RAG analytics
│   │   ├── calendar.py                  # Calendar endpoints
│   │   ├── cards.py                     # Payment cards
│   │   ├── insights.py                  # Analytics/insights
│   │   ├── search.py                    # RAG search
│   │   └── subscriptions.py             # CRUD operations
│   │
│   ├── 📁 core/                         # Core Configuration
│   │   ├── __init__.py
│   │   ├── config.py                    # Settings management
│   │   └── dependencies.py              # FastAPI dependencies
│   │
│   ├── 📁 db/                           # Database Layer
│   │   ├── __init__.py
│   │   ├── database.py                  # Engine and session
│   │   │
│   │   └── 📁 migrations/               # Alembic Migrations
│   │       ├── env.py                   # Migration environment
│   │       │
│   │       └── 📁 versions/             # Migration versions
│   │           ├── 41ee05d4b675_add_payment_tracking_fields.py
│   │           ├── 8288763654e3_add_funding_card_id.py
│   │           ├── c7a8f3d2e591_add_rag_tables.py
│   │           ├── d8b9e4f5a123_add_money_flow_payment_types.py
│   │           ├── e9c0f5g6b234_add_one_time_payment_type.py
│   │           ├── f1a2b3c4d567_add_end_date_field.py
│   │           └── g2b3c4d5e678_add_payment_cards.py
│   │
│   ├── 📁 models/                       # SQLAlchemy Models
│   │   ├── __init__.py
│   │   ├── payment_card.py              # Payment card model
│   │   ├── rag.py                       # RAG models
│   │   └── subscription.py              # Subscription model
│   │
│   ├── 📁 schemas/                      # Pydantic Schemas
│   │   ├── __init__.py
│   │   ├── payment_card.py              # Card schemas
│   │   └── subscription.py              # Subscription schemas
│   │
│   └── 📁 services/                     # Business Logic
│       ├── __init__.py
│       ├── cache_service.py             # Redis caching
│       ├── conversation_service.py      # Conversation storage
│       ├── currency_service.py          # Currency conversion
│       ├── embedding_service.py         # Text embeddings
│       ├── historical_query_service.py  # Pattern analysis
│       ├── insights_service.py          # Analytics
│       ├── payment_card_service.py      # Card operations
│       ├── payment_service.py           # Payment tracking
│       ├── rag_analytics.py             # RAG metrics
│       ├── rag_service.py               # RAG orchestration
│       ├── subscription_service.py      # Core CRUD
│       └── vector_store.py              # Qdrant operations
│
├── 📁 tests/                            # Test Suite
│   ├── __init__.py
│   ├── conftest.py                      # Pytest fixtures
│   │
│   ├── 📁 agent/                        # Agent tests
│   │   └── __init__.py
│   │
│   ├── 📁 integration/                  # Integration tests
│   │   ├── __init__.py
│   │   ├── test_analytics_api.py
│   │   ├── test_api.py
│   │   ├── test_import_export_api.py
│   │   └── test_search_api.py
│   │
│   └── 📁 unit/                         # Unit tests
│       ├── __init__.py
│       ├── test_cache_service.py
│       ├── test_conversation_service.py
│       ├── test_currency_service.py
│       ├── test_executor.py
│       ├── test_historical_query_service.py
│       ├── test_insights_service.py
│       ├── test_models.py
│       ├── test_parser.py
│       ├── test_rag_analytics.py
│       ├── test_rag_services.py
│       ├── test_schemas.py
│       ├── test_subscription_service.py
│       └── test_vector_store_hybrid.py
│
├── .env                                 # Environment variables (git-ignored)
├── .env.example                         # Example environment
├── .pre-commit-config.yaml              # Pre-commit hooks
├── alembic.ini                          # Alembic configuration
├── CLAUDE.md                            # Claude Code instructions
├── docker-compose.yml                   # Multi-container config
├── Dockerfile                           # Backend container
├── IMPROVEMENTS.md                      # Future improvements
├── PROJECT_DOCUMENTATION.md             # THIS FILE
├── pyproject.toml                       # Python project config
├── README.md                            # Quick start guide
└── subscriptions_20251201.json          # Backup export
```

### 5.1 File Count Summary

| Category | Count |
|----------|-------|
| Python Files | 51 |
| TypeScript/TSX Files | 15 |
| Configuration Files | 12 |
| Documentation Files | 18 |
| Test Files | 15 |
| Migration Files | 7 |
| **Total** | **118** |

---

## 6. Backend Deep Dive

### 6.1 Entry Point (`src/main.py`)

The FastAPI application is configured with:

```python
# Lifespan management for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()           # Initialize database tables
    await get_cache_service() # Connect to Redis
    yield
    await close_cache_service() # Cleanup on shutdown

# Application instance
app = FastAPI(
    title="Subscription Tracker",
    description="Track subscriptions with agentic interface",
    version="0.1.0",
    lifespan=lifespan,
)

# 7 API routers registered
app.include_router(subscriptions.router, prefix="/api/subscriptions")
app.include_router(calendar.router, prefix="/api/calendar")
app.include_router(agent.router, prefix="/api/agent")
app.include_router(search.router, prefix="/api/search")
app.include_router(insights.router, prefix="/api/insights")
app.include_router(analytics.router, prefix="/api/analytics")
app.include_router(cards.router, prefix="/api")
```

### 6.2 Configuration (`src/core/config.py`)

Environment-based settings using Pydantic:

```python
class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://..."

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:3002"]

    # Claude API
    anthropic_api_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # RAG
    embedding_model: str = "all-MiniLM-L6-v2"
    rag_enabled: bool = True
```

### 6.3 Models Deep Dive

#### 6.3.1 Subscription Model (`src/models/subscription.py`)

The core model with 35+ fields:

```python
class Subscription(Base):
    __tablename__ = "subscriptions"

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Core Fields
    name: Mapped[str] = mapped_column(String(255), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="GBP")

    # Scheduling
    frequency: Mapped[Frequency] = mapped_column(Enum(Frequency))
    frequency_interval: Mapped[int] = mapped_column(Integer, default=1)
    start_date: Mapped[date]
    end_date: Mapped[date | None]
    next_payment_date: Mapped[date]
    last_payment_date: Mapped[date | None]

    # Classification
    payment_type: Mapped[PaymentType] = mapped_column(index=True)
    category: Mapped[str | None]
    is_active: Mapped[bool] = mapped_column(default=True)

    # Installment Tracking
    is_installment: Mapped[bool] = mapped_column(default=False)
    total_installments: Mapped[int | None]
    completed_installments: Mapped[int] = mapped_column(default=0)

    # Debt-Specific (PaymentType.DEBT)
    total_owed: Mapped[Decimal | None]
    remaining_balance: Mapped[Decimal | None]
    creditor: Mapped[str | None]

    # Savings-Specific (PaymentType.SAVINGS)
    target_amount: Mapped[Decimal | None]
    current_saved: Mapped[Decimal | None]
    recipient: Mapped[str | None]

    # Payment Card Link
    card_id: Mapped[str | None] = mapped_column(
        ForeignKey("payment_cards.id", ondelete="SET NULL")
    )

    # Computed Properties
    @property
    def days_until_payment(self) -> int:
        return (self.next_payment_date - date.today()).days

    @property
    def debt_paid_percentage(self) -> float | None:
        if self.payment_type != PaymentType.DEBT:
            return None
        paid = self.total_owed - self.remaining_balance
        return round((paid / self.total_owed) * 100, 1)

    @property
    def savings_progress_percentage(self) -> float | None:
        if self.payment_type != PaymentType.SAVINGS:
            return None
        return round((self.current_saved / self.target_amount) * 100, 1)
```

#### 6.3.2 Payment Type Enum

```python
class PaymentType(str, enum.Enum):
    SUBSCRIPTION = "subscription"        # Netflix, Spotify
    HOUSING = "housing"                  # Rent, mortgage
    UTILITY = "utility"                  # Electric, water, internet
    PROFESSIONAL_SERVICE = "professional_service"  # Therapist, coach
    INSURANCE = "insurance"              # Health, device, vehicle
    DEBT = "debt"                        # Credit cards, loans
    SAVINGS = "savings"                  # Goals with targets
    TRANSFER = "transfer"                # Family support
    ONE_TIME = "one_time"                # One-off payments
```

#### 6.3.3 Frequency Enum

```python
class Frequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"  # Uses frequency_interval
```

### 6.4 Services Deep Dive

#### 6.4.1 SubscriptionService (`src/services/subscription_service.py`)

Core CRUD operations with analytics:

```python
class SubscriptionService:
    async def create(
        self,
        db: AsyncSession,
        data: SubscriptionCreate
    ) -> Subscription:
        """Create subscription with calculated next_payment_date."""

    async def get_all(
        self,
        db: AsyncSession,
        is_active: bool | None = None,
        payment_type: PaymentType | None = None,
        category: str | None = None,
    ) -> list[Subscription]:
        """List subscriptions with filters."""

    async def update(
        self,
        db: AsyncSession,
        id: str,
        data: SubscriptionUpdate
    ) -> Subscription:
        """Partial update with recalculated dates."""

    async def get_summary(
        self,
        db: AsyncSession
    ) -> SubscriptionSummary:
        """Spending analytics by type/category."""

    async def get_upcoming(
        self,
        db: AsyncSession,
        days: int = 7
    ) -> list[Subscription]:
        """Payments due within N days."""
```

#### 6.4.2 CurrencyService (`src/services/currency_service.py`)

Live exchange rates with caching:

```python
class CurrencyService:
    SUPPORTED_CURRENCIES = ["GBP", "USD", "EUR", "UAH"]
    DEFAULT_CURRENCY = "GBP"

    async def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Decimal:
        """Get rate with Redis caching (1hr TTL)."""

    async def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str
    ) -> Decimal:
        """Convert amount between currencies."""

    # Fallback static rates if API unavailable
    FALLBACK_RATES = {
        "GBP": {"USD": 1.27, "EUR": 1.17, "UAH": 52.0},
        "USD": {"GBP": 0.79, "EUR": 0.92, "UAH": 41.0},
        ...
    }
```

#### 6.4.3 CacheService (`src/services/cache_service.py`)

Redis caching with graceful degradation:

```python
class CacheService:
    """Singleton Redis cache with connection pooling."""

    async def get(self, key: str) -> Any | None:
        """Get cached value, None if not found."""

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> bool:
        """Set value with TTL (default 1hr)."""

    async def delete(self, key: str) -> bool:
        """Delete key."""

    async def get_stats(self) -> dict:
        """Return cache hit rate and stats."""

    # Key patterns
    # emb:{model}:{hash}     - Embedding cache
    # ctx:{user}:{session}   - Context cache
    # query:{hash}           - Query result cache
```

#### 6.4.4 EmbeddingService (`src/services/embedding_service.py`)

Sentence Transformers integration:

```python
class EmbeddingService:
    """Singleton with lazy model loading."""

    MODEL_NAME = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384

    async def embed(self, text: str) -> list[float]:
        """Generate embedding with cache check."""
        cache_key = f"emb:{self.MODEL_NAME}:{md5(text)}"

        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        embedding = self.model.encode(text).tolist()
        await self.cache.set(cache_key, embedding, ttl=3600)
        return embedding

    async def embed_batch(
        self,
        texts: list[str]
    ) -> list[list[float]]:
        """Batch embed with partial cache hits."""
```

#### 6.4.5 VectorStore (`src/services/vector_store.py`)

Qdrant operations:

```python
class VectorStore:
    """Qdrant client wrapper."""

    COLLECTIONS = {
        "conversations": "conversation_embeddings",
        "notes": "note_embeddings",
    }

    async def upsert(
        self,
        collection: str,
        id: str,
        vector: list[float],
        payload: dict
    ):
        """Store/update vector with metadata."""

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float = 0.7,
        user_id: str | None = None,
    ) -> list[ScoredPoint]:
        """Similarity search with user filtering."""

    async def hybrid_search(
        self,
        collection: str,
        query_vector: list[float],
        keywords: list[str],
        limit: int = 5,
    ) -> list[ScoredPoint]:
        """Combined semantic + keyword search."""
```

---

## 7. Frontend Deep Dive

### 7.1 Application Structure

```
frontend/src/
├── app/           # Next.js App Router (pages, layouts)
├── components/    # React Components (UI building blocks)
├── hooks/         # Custom React Hooks (reusable logic)
└── lib/           # Utilities (API client, helpers, context)
```

### 7.2 Main Page (`src/app/page.tsx`)

Dashboard with view switching:

```typescript
type ViewType = "list" | "calendar" | "cards" | "agent";

export default function Home() {
  const [currentView, setCurrentView] = useState<ViewType>("list");

  // URL sync for view persistence
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const view = params.get("view") as ViewType;
    if (view) setCurrentView(view);
  }, []);

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <Header currentView={currentView} onViewChange={setCurrentView} />

      <AnimatePresence mode="wait">
        {currentView === "list" && <SubscriptionList />}
        {currentView === "calendar" && <PaymentCalendar />}
        {currentView === "cards" && <CardsDashboard />}
        {currentView === "agent" && <AgentChat />}
      </AnimatePresence>
    </main>
  );
}
```

### 7.3 Key Components

#### 7.3.1 SubscriptionList

Main list view with filtering and search:

```typescript
interface SubscriptionListProps {
  // Props for filtering
}

export function SubscriptionList() {
  // Payment type filter tabs
  const [activeTab, setActiveTab] = useState<PaymentType | "all" | "no_card">("all");

  // Search state
  const [searchQuery, setSearchQuery] = useState("");

  // React Query for data fetching
  const { data: subscriptions, isLoading } = useQuery({
    queryKey: ["subscriptions"],
    queryFn: () => api.getSubscriptions(),
  });

  // Filtered subscriptions
  const filtered = useMemo(() => {
    return subscriptions?.filter(sub => {
      // Filter by type
      if (activeTab !== "all" && activeTab !== "no_card") {
        if (sub.payment_type !== activeTab) return false;
      }
      if (activeTab === "no_card" && sub.card_id) return false;

      // Filter by search
      if (searchQuery) {
        return sub.name.toLowerCase().includes(searchQuery.toLowerCase());
      }
      return true;
    });
  }, [subscriptions, activeTab, searchQuery]);

  return (
    <div className="space-y-4">
      {/* Filter Tabs */}
      <div className="flex gap-2 overflow-x-auto">
        {PAYMENT_TYPE_TABS.map(tab => (
          <button
            key={tab.value}
            onClick={() => setActiveTab(tab.value)}
            className={cn(
              "px-4 py-2 rounded-full transition-colors",
              activeTab === tab.value
                ? "bg-blue-600 text-white"
                : "bg-gray-100 hover:bg-gray-200"
            )}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Subscription Cards */}
      <motion.div layout className="space-y-3">
        {filtered?.map(sub => (
          <SubscriptionCard
            key={sub.id}
            subscription={sub}
            onEdit={() => setEditing(sub)}
            onDelete={() => handleDelete(sub.id)}
          />
        ))}
      </motion.div>
    </div>
  );
}
```

#### 7.3.2 PaymentCalendar

Calendar view with dynamic month totals:

```typescript
export function PaymentCalendar() {
  const [currentMonth, setCurrentMonth] = useState(new Date());

  // Fetch current month events
  const { data: events = [] } = useQuery({
    queryKey: ["calendar-events", formatDate(startOfMonth(currentMonth))],
    queryFn: () => calendarApi.getEvents(
      formatDate(startOfMonth(currentMonth)),
      formatDate(endOfMonth(currentMonth))
    ),
  });

  // Fetch NEXT month events for summary card
  const nextMonthStart = startOfMonth(addMonths(currentMonth, 1));
  const { data: nextMonthEvents = [] } = useQuery({
    queryKey: ["calendar-events", formatDate(nextMonthStart)],
    queryFn: () => calendarApi.getEvents(
      formatDate(nextMonthStart),
      formatDate(endOfMonth(nextMonthStart))
    ),
  });

  // Calculate totals
  const currentMonthTotal = useMemo(() =>
    events.reduce((sum, e) => sum + convert(e.amount, e.currency), 0),
    [events, convert]
  );

  const nextMonthTotal = useMemo(() =>
    nextMonthEvents.reduce((sum, e) => sum + convert(e.amount, e.currency), 0),
    [nextMonthEvents, convert]
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Summary Cards */}
      <div className="lg:col-span-1 space-y-4">
        <SummaryCard
          title={`Total for ${formatDate(currentMonth, "MMMM")}`}
          value={formatCurrency(currentMonthTotal)}
          icon={<Calendar />}
          gradient="from-purple-500 to-pink-500"
        />
        <SummaryCard
          title={`Due in ${formatDate(addMonths(currentMonth, 1), "MMMM")}`}
          value={formatCurrency(nextMonthTotal)}
          icon={<TrendingUp />}
          gradient="from-blue-500 to-cyan-500"
        />
      </div>

      {/* Calendar Grid */}
      <div className="lg:col-span-3">
        <CalendarGrid
          month={currentMonth}
          events={events}
          onMonthChange={setCurrentMonth}
        />
      </div>
    </div>
  );
}
```

#### 7.3.3 AgentChat

AI chat interface:

```typescript
export function AgentChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const queryClient = useQueryClient();

  const handleSend = async () => {
    if (!input.trim()) return;

    // Add user message
    const userMessage: Message = {
      role: "user",
      content: input,
    };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // Send to agent API
      const response = await agentApi.execute({
        command: input,
        history: messages,
      });

      // Add assistant message
      setMessages(prev => [...prev, {
        role: "assistant",
        content: response.message,
      }]);

      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      queryClient.invalidateQueries({ queryKey: ["calendar-events"] });

    } catch (error) {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px]">
      {/* Message List */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}
        {isLoading && <LoadingIndicator />}
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSend()}
            placeholder="Try: Add Netflix for £15.99 monthly"
            className="flex-1 px-4 py-2 border rounded-lg"
          />
          <button onClick={handleSend} className="px-6 py-2 bg-blue-600 text-white rounded-lg">
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 7.4 Custom Hooks

#### 7.4.1 useCurrencyFormat

```typescript
export function useCurrencyFormat() {
  const { displayCurrency, exchangeRates } = useCurrencyContext();

  const format = useCallback((amount: number, currency?: string) => {
    const symbol = CURRENCY_SYMBOLS[displayCurrency] || "£";
    const converted = currency && currency !== displayCurrency
      ? convert(amount, currency, displayCurrency)
      : amount;

    return `${symbol}${converted.toLocaleString("en-GB", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }, [displayCurrency]);

  const convert = useCallback((
    amount: number,
    from: string,
    to?: string
  ) => {
    const target = to || displayCurrency;
    if (from === target) return amount;

    const rate = exchangeRates[from]?.[target] || 1;
    return amount * rate;
  }, [displayCurrency, exchangeRates]);

  return { format, convert, displayCurrency };
}
```

### 7.5 API Client (`src/lib/api.ts`)

```typescript
const api = axios.create({
  baseURL: "/api", // Proxied through Next.js rewrites
});

export const subscriptionsApi = {
  getAll: () => api.get<Subscription[]>("/subscriptions").then(r => r.data),

  getById: (id: string) =>
    api.get<Subscription>(`/subscriptions/${id}`).then(r => r.data),

  create: (data: SubscriptionCreate) =>
    api.post<Subscription>("/subscriptions", data).then(r => r.data),

  update: (id: string, data: SubscriptionUpdate) =>
    api.put<Subscription>(`/subscriptions/${id}`, data).then(r => r.data),

  delete: (id: string) =>
    api.delete(`/subscriptions/${id}`),

  getSummary: () =>
    api.get<SubscriptionSummary>("/subscriptions/summary").then(r => r.data),

  import: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/subscriptions/import", formData);
  },

  export: (format: "json" | "csv") =>
    api.get(`/subscriptions/export?format=${format}`),
};

export const calendarApi = {
  getEvents: (startDate: string, endDate: string) =>
    api.get<CalendarEvent[]>("/calendar/events", {
      params: { start_date: startDate, end_date: endDate }
    }).then(r => r.data),

  getMonthlySummary: (year: number, month: number) =>
    api.get("/calendar/monthly-summary", {
      params: { year, month }
    }).then(r => r.data),
};

export const agentApi = {
  execute: (request: AgentRequest) =>
    api.post<AgentResponse>("/agent/execute", request).then(r => r.data),

  chat: (request: ChatRequest) =>
    api.post<ChatResponse>("/agent/chat", request).then(r => r.data),
};
```

---

## 8. Database Schema

### 8.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           SUBSCRIPTIONS                              │
├─────────────────────────────────────────────────────────────────────┤
│ id (PK)              │ UUID         │ Primary key                   │
│ name                 │ VARCHAR(255) │ Payment name (indexed)        │
│ amount               │ NUMERIC(10,2)│ Payment amount                │
│ currency             │ VARCHAR(3)   │ ISO currency code             │
│ frequency            │ ENUM         │ Payment frequency             │
│ frequency_interval   │ INTEGER      │ Multiplier (default: 1)       │
│ start_date           │ DATE         │ When payment started          │
│ end_date             │ DATE         │ Optional end date             │
│ next_payment_date    │ DATE         │ Calculated next payment       │
│ last_payment_date    │ DATE         │ Most recent payment           │
│ payment_type         │ ENUM         │ Type classification (indexed) │
│ category             │ VARCHAR(100) │ Subcategory                   │
│ is_active            │ BOOLEAN      │ Active status                 │
│ notes                │ TEXT         │ Freeform notes                │
│ payment_method       │ VARCHAR(50)  │ How paid                      │
│ reminder_days        │ INTEGER      │ Reminder offset (default: 3)  │
│ icon_url             │ VARCHAR(500) │ Service logo URL              │
│ color                │ VARCHAR(7)   │ Brand color (hex)             │
│ auto_renew           │ BOOLEAN      │ Auto-renewal status           │
│ is_installment       │ BOOLEAN      │ Installment plan flag         │
│ total_installments   │ INTEGER      │ Total payment count           │
│ completed_installments│ INTEGER     │ Payments completed            │
│ installment_start_date│ DATE        │ Plan start                    │
│ installment_end_date │ DATE         │ Plan end                      │
│ total_owed           │ NUMERIC(12,2)│ Original debt (DEBT type)     │
│ remaining_balance    │ NUMERIC(12,2)│ Remaining (DEBT type)         │
│ creditor             │ VARCHAR(255) │ Who you owe (DEBT type)       │
│ target_amount        │ NUMERIC(12,2)│ Savings goal (SAVINGS type)   │
│ current_saved        │ NUMERIC(12,2)│ Progress (SAVINGS type)       │
│ recipient            │ VARCHAR(255) │ Who receives (TRANSFER type)  │
│ card_id (FK)         │ UUID         │ → payment_cards.id            │
│ created_at           │ TIMESTAMP    │ Creation time                 │
│ updated_at           │ TIMESTAMP    │ Last update time              │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         PAYMENT_HISTORY                              │
├─────────────────────────────────────────────────────────────────────┤
│ id (PK)              │ UUID         │ Primary key                   │
│ subscription_id (FK) │ UUID         │ → subscriptions.id (CASCADE)  │
│ payment_date         │ DATE         │ Payment date (indexed)        │
│ amount               │ NUMERIC(10,2)│ Payment amount                │
│ currency             │ VARCHAR(3)   │ Currency code                 │
│ status               │ ENUM         │ completed/pending/failed      │
│ payment_method       │ VARCHAR(50)  │ How paid                      │
│ installment_number   │ INTEGER      │ Sequence for installments     │
│ notes                │ TEXT         │ Payment notes                 │
│ created_at           │ TIMESTAMP    │ Record creation               │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          PAYMENT_CARDS                               │
├─────────────────────────────────────────────────────────────────────┤
│ id (PK)              │ UUID         │ Primary key                   │
│ name                 │ VARCHAR(255) │ Card name (e.g., "Monzo")     │
│ card_type            │ ENUM         │ debit/credit/prepaid/bank     │
│ last_four            │ VARCHAR(4)   │ Last 4 digits                 │
│ currency             │ VARCHAR(3)   │ Card currency                 │
│ is_active            │ BOOLEAN      │ Active status                 │
│ color                │ VARCHAR(7)   │ Card color (hex)              │
│ icon                 │ VARCHAR(50)  │ Icon name                     │
│ sort_order           │ INTEGER      │ Display order                 │
│ funding_card_id (FK) │ UUID         │ → payment_cards.id (self-ref) │
│ created_at           │ TIMESTAMP    │ Creation time                 │
│ updated_at           │ TIMESTAMP    │ Last update                   │
└─────────────────────────────────────────────────────────────────────┘
        │
        │ 1:N (subscriptions.card_id)
        ▼
    [SUBSCRIPTIONS]

┌─────────────────────────────────────────────────────────────────────┐
│                          CONVERSATIONS                               │
├─────────────────────────────────────────────────────────────────────┤
│ id (PK)              │ UUID         │ Primary key                   │
│ user_id              │ VARCHAR(255) │ User identifier (indexed)     │
│ session_id           │ VARCHAR(255) │ Session identifier (indexed)  │
│ role                 │ VARCHAR(20)  │ user/assistant                │
│ content              │ TEXT         │ Message content               │
│ entities             │ JSONB        │ Extracted entities            │
│ created_at           │ TIMESTAMP    │ Message timestamp             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          RAG_ANALYTICS                               │
├─────────────────────────────────────────────────────────────────────┤
│ id (PK)              │ UUID         │ Primary key                   │
│ user_id              │ VARCHAR(255) │ User identifier               │
│ query                │ TEXT         │ User query                    │
│ embedding_latency_ms │ INTEGER      │ Embedding generation time     │
│ search_latency_ms    │ INTEGER      │ Vector search time            │
│ total_latency_ms     │ INTEGER      │ Total processing time         │
│ cache_hit            │ BOOLEAN      │ Embedding cache hit           │
│ results_count        │ INTEGER      │ Number of results             │
│ top_score            │ FLOAT        │ Best relevance score          │
│ entities_resolved    │ INTEGER      │ References resolved           │
│ error                │ TEXT         │ Error message if failed       │
│ created_at           │ TIMESTAMP    │ Query timestamp               │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 Indexes

```sql
-- Subscriptions
CREATE INDEX ix_subscriptions_name ON subscriptions(name);
CREATE INDEX ix_subscriptions_payment_type ON subscriptions(payment_type);
CREATE INDEX ix_subscriptions_card_id ON subscriptions(card_id);

-- Payment History
CREATE INDEX ix_payment_history_subscription_id ON payment_history(subscription_id);
CREATE INDEX ix_payment_history_payment_date ON payment_history(payment_date);
CREATE INDEX ix_payment_history_status ON payment_history(status);

-- Conversations
CREATE INDEX ix_conversations_user_id ON conversations(user_id);
CREATE INDEX ix_conversations_session_id ON conversations(session_id);
```

### 8.3 Migration History

| Migration ID | Description | Date |
|--------------|-------------|------|
| `41ee05d4b675` | Add payment tracking fields | 2025-11-15 |
| `c7a8f3d2e591` | Add RAG tables | 2025-11-20 |
| `d8b9e4f5a123` | Add Money Flow payment types | 2025-12-01 |
| `e9c0f5g6b234` | Add ONE_TIME payment type | 2025-12-06 |
| `f1a2b3c4d567` | Add end_date field | 2025-12-07 |
| `g2b3c4d5e678` | Add payment_cards table | 2025-12-07 |
| `8288763654e3` | Add funding_card_id | 2025-12-08 |

---

## 9. API Reference

### 9.1 Subscriptions API

#### List Subscriptions
```http
GET /api/subscriptions
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `is_active` | boolean | Filter by active status |
| `payment_type` | string | Filter by payment type |
| `category` | string | Filter by category |

**Response:** `200 OK`
```json
[
  {
    "id": "uuid-string",
    "name": "Netflix",
    "amount": "15.99",
    "currency": "GBP",
    "frequency": "monthly",
    "payment_type": "subscription",
    "next_payment_date": "2025-01-15",
    "is_active": true,
    "days_until_payment": 5,
    "payment_status": "upcoming"
  }
]
```

#### Create Subscription
```http
POST /api/subscriptions
Content-Type: application/json

{
  "name": "Netflix",
  "amount": 15.99,
  "currency": "GBP",
  "frequency": "monthly",
  "payment_type": "subscription",
  "start_date": "2025-01-01",
  "category": "Entertainment"
}
```

**Response:** `201 Created`

#### Update Subscription
```http
PUT /api/subscriptions/{id}
Content-Type: application/json

{
  "amount": 17.99,
  "is_active": false
}
```

**Response:** `200 OK`

#### Delete Subscription
```http
DELETE /api/subscriptions/{id}
```

**Response:** `204 No Content`

#### Get Summary
```http
GET /api/subscriptions/summary
```

**Response:** `200 OK`
```json
{
  "total_monthly": 450.00,
  "total_yearly": 5400.00,
  "by_type": {
    "subscription": 150.00,
    "utility": 200.00,
    "housing": 100.00
  },
  "by_category": {
    "entertainment": 50.00,
    "utilities": 200.00
  },
  "active_count": 25,
  "inactive_count": 5
}
```

#### Import Subscriptions
```http
POST /api/subscriptions/import
Content-Type: multipart/form-data

file: subscriptions.json
```

**Response:** `200 OK`
```json
{
  "imported": 15,
  "skipped": 2,
  "errors": []
}
```

#### Export Subscriptions
```http
GET /api/subscriptions/export?format=json
```

**Response:** `200 OK` (JSON or CSV file download)

### 9.2 Calendar API

#### Get Events
```http
GET /api/calendar/events?start_date=2025-01-01&end_date=2025-01-31
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "subscription_id": "uuid",
    "name": "Netflix",
    "amount": "15.99",
    "currency": "GBP",
    "date": "2025-01-15",
    "payment_type": "subscription",
    "color": "#E50914"
  }
]
```

#### Get Monthly Summary
```http
GET /api/calendar/monthly-summary?year=2025&month=1
```

**Response:** `200 OK`
```json
{
  "total": 1250.00,
  "by_status": {
    "paid": 500.00,
    "pending": 750.00
  },
  "payment_count": 15
}
```

#### Record Payment
```http
POST /api/calendar/record-payment
Content-Type: application/json

{
  "subscription_id": "uuid",
  "payment_date": "2025-01-15",
  "amount": 15.99,
  "status": "completed"
}
```

**Response:** `201 Created`

### 9.3 Agent API

#### Execute Command
```http
POST /api/agent/execute
Content-Type: application/json

{
  "command": "Add Netflix for £15.99 monthly",
  "user_id": "user-123",
  "session_id": "session-456",
  "history": []
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Added Netflix - £15.99 monthly starting today.",
  "data": {
    "subscription": { ... }
  },
  "intent": "create_subscription"
}
```

#### Chat (Conversational)
```http
POST /api/agent/chat
Content-Type: application/json

{
  "message": "How much am I spending on streaming?",
  "user_id": "user-123",
  "session_id": "session-456",
  "history": [
    {"role": "user", "content": "Add Netflix"},
    {"role": "assistant", "content": "Added Netflix"}
  ]
}
```

**Response:** `200 OK`
```json
{
  "message": "You're spending £45.97 per month on streaming services:\n- Netflix: £15.99\n- Spotify: £10.99\n- Disney+: £8.99\n- YouTube Premium: £10.00",
  "data": null
}
```

### 9.4 Cards API

#### List Cards
```http
GET /api/cards
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "name": "Monzo",
    "card_type": "debit",
    "last_four": "1234",
    "currency": "GBP",
    "color": "#FF5757",
    "subscription_count": 12,
    "monthly_total": 250.00
  }
]
```

#### Get Balance Summary
```http
GET /api/cards/balance-summary
```

**Response:** `200 OK`
```json
{
  "total_monthly": 450.00,
  "by_card": [
    {"card_id": "uuid", "name": "Monzo", "monthly": 250.00},
    {"card_id": "uuid", "name": "Amex", "monthly": 200.00}
  ],
  "unassigned": 50.00
}
```

### 9.5 Search API

#### Semantic Search Notes
```http
POST /api/search/notes
Content-Type: application/json

{
  "query": "streaming services",
  "limit": 10,
  "user_id": "user-123"
}
```

**Response:** `200 OK`
```json
{
  "results": [
    {
      "subscription_id": "uuid",
      "name": "Netflix",
      "score": 0.92,
      "snippet": "Premium streaming subscription..."
    }
  ]
}
```

### 9.6 Insights API

#### Get All Insights
```http
GET /api/insights
```

**Response:** `200 OK`
```json
{
  "spending_trends": {
    "monthly_change": -5.2,
    "trend": "decreasing"
  },
  "category_breakdown": [
    {"category": "Entertainment", "amount": 150.00, "percentage": 33.3}
  ],
  "recommendations": [
    {
      "subscription_id": "uuid",
      "name": "Unused Service",
      "reason": "No activity in 3 months",
      "potential_savings": 9.99
    }
  ]
}
```

### 9.7 Analytics API

#### Get RAG Analytics
```http
GET /api/analytics
```

**Response:** `200 OK`
```json
{
  "total_queries": 150,
  "avg_latency_ms": 45,
  "cache_hit_rate": 0.72,
  "avg_results_count": 3.5
}
```

#### Get Cache Stats
```http
GET /api/analytics/cache
```

**Response:** `200 OK`
```json
{
  "redis_connected": true,
  "keys_count": 250,
  "memory_used_mb": 12.5,
  "hit_rate": 0.72
}
```

---

## 10. AI Agent System

### 10.1 Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                     USER NATURAL LANGUAGE                       │
│              "Add Netflix for £15.99 monthly"                   │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                    CONVERSATIONAL AGENT                         │
│              (Claude Haiku 4.5 with Tool Use)                   │
│                                                                 │
│  Tools Available:                                               │
│  - list_subscriptions    - create_subscription                  │
│  - update_subscription   - delete_subscription                  │
│  - get_summary           - get_upcoming                         │
│  - convert_currency      - record_payment                       │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                      COMMAND PARSER                             │
│               (NL → Intent + Entities)                          │
│                                                                 │
│  Input: "Add Netflix for £15.99 monthly"                        │
│  Output:                                                        │
│    intent: "create_subscription"                                │
│    entities:                                                    │
│      name: "Netflix"                                            │
│      amount: 15.99                                              │
│      currency: "GBP"                                            │
│      frequency: "monthly"                                       │
│      payment_type: "subscription"  (auto-detected)              │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                     AGENT EXECUTOR                              │
│            (Intent → Database Operations)                       │
│                                                                 │
│  Calls: SubscriptionService.create(parsed_data)                 │
│  Returns: Formatted response with result                        │
└────────────────────────────────────────────────────────────────┘
```

### 10.2 ConversationalAgent (`src/agent/conversational_agent.py`)

```python
class ConversationalAgent:
    """Claude Haiku 4.5 powered agent with tool use."""

    MODEL = "claude-haiku-4.5-20250929"

    TOOLS = [
        {
            "name": "list_subscriptions",
            "description": "List all subscriptions with optional filters",
            "input_schema": {
                "type": "object",
                "properties": {
                    "payment_type": {"type": "string"},
                    "is_active": {"type": "boolean"}
                }
            }
        },
        {
            "name": "create_subscription",
            "description": "Create a new subscription or payment",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "amount": {"type": "number"},
                    "currency": {"type": "string"},
                    "frequency": {"type": "string"},
                    "payment_type": {"type": "string"}
                },
                "required": ["name", "amount"]
            }
        },
        # ... more tools
    ]

    async def execute(
        self,
        command: str,
        history: list[dict],
        user_id: str,
        session_id: str,
    ) -> AgentResponse:
        """Execute natural language command."""

        # Get RAG context
        context = await self.rag_service.get_context(
            query=command,
            user_id=user_id,
            session_id=session_id,
        )

        # Build messages with context
        messages = self._build_messages(command, history, context)

        # Call Claude with tools
        response = await self.client.messages.create(
            model=self.MODEL,
            messages=messages,
            tools=self.TOOLS,
            max_tokens=1024,
        )

        # Handle tool calls
        if response.stop_reason == "tool_use":
            tool_result = await self._execute_tool(
                response.content[0].name,
                response.content[0].input,
            )
            return AgentResponse(
                success=True,
                message=self._format_response(tool_result),
                data=tool_result,
            )

        # Direct text response
        return AgentResponse(
            success=True,
            message=response.content[0].text,
        )
```

### 10.3 CommandParser (`src/agent/parser.py`)

Dual-mode parsing with AI + Regex fallback:

```python
class CommandParser:
    """Parse natural language commands into structured data."""

    # Payment type auto-detection hints
    PAYMENT_TYPE_HINTS = {
        PaymentType.SUBSCRIPTION: [
            "netflix", "spotify", "disney", "hulu", "youtube",
            "amazon prime", "streaming", "subscription", "premium"
        ],
        PaymentType.HOUSING: [
            "rent", "mortgage", "landlord", "property", "lease"
        ],
        PaymentType.UTILITY: [
            "electric", "gas", "water", "internet", "broadband",
            "council tax", "edf", "thames water", "energy"
        ],
        PaymentType.PROFESSIONAL_SERVICE: [
            "therapist", "therapy", "coach", "trainer", "tutor",
            "gym", "cleaner", "lesson", "barrister", "lawyer"
        ],
        PaymentType.INSURANCE: [
            "insurance", "bupa", "applecare", "health insurance"
        ],
        PaymentType.DEBT: [
            "debt", "credit card", "loan", "owe", "borrowed", "repay"
        ],
        PaymentType.SAVINGS: [
            "savings", "goal", "target", "save for", "accumulate"
        ],
        PaymentType.TRANSFER: [
            "transfer", "send", "gift", "family", "support"
        ],
    }

    async def parse(self, command: str) -> ParsedCommand:
        """Parse command using Claude, with regex fallback."""
        try:
            return await self._parse_with_claude(command)
        except Exception:
            return self._parse_with_regex(command)

    def _detect_payment_type(self, text: str) -> PaymentType:
        """Auto-detect payment type from keywords."""
        text_lower = text.lower()
        for ptype, keywords in self.PAYMENT_TYPE_HINTS.items():
            if any(kw in text_lower for kw in keywords):
                return ptype
        return PaymentType.SUBSCRIPTION  # Default
```

### 10.4 Supported Commands

| Intent | Example Commands |
|--------|------------------|
| **Create** | "Add Netflix for £15.99 monthly" |
| | "Create rent payment £1200 monthly" |
| | "Add debt to John £500, paying £50 monthly" |
| | "Set up savings goal £10000 for holiday" |
| **List** | "Show all my subscriptions" |
| | "List debts" |
| | "What streaming services do I have?" |
| **Update** | "Change Netflix to £17.99" |
| | "Mark Netflix as inactive" |
| | "Update my rent to £1250" |
| **Delete** | "Cancel Netflix" |
| | "Remove Spotify" |
| | "Delete the gym subscription" |
| **Summary** | "How much am I spending?" |
| | "What's my monthly total?" |
| | "Show spending by category" |
| **Upcoming** | "What's due this week?" |
| | "Show upcoming payments" |
| | "What bills are due soon?" |
| **Debt** | "I paid £200 off my credit card" |
| | "What's my total debt?" |
| | "How much do I owe?" |
| **Savings** | "Add £500 to holiday savings" |
| | "How much have I saved?" |
| | "What's my savings progress?" |

---

## 11. RAG Implementation

### 11.1 RAG Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER QUERY                                │
│                 "Cancel my streaming subscription"               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     EMBEDDING SERVICE                            │
│              (Sentence Transformers all-MiniLM-L6-v2)           │
│                                                                  │
│  Input: "Cancel my streaming subscription"                       │
│  Output: [0.123, -0.456, 0.789, ...] (384 dimensions)           │
│                                                                  │
│  Redis Cache Check:                                              │
│    Key: emb:all-MiniLM-L6-v2:{md5_hash}                         │
│    Hit: Return cached embedding                                  │
│    Miss: Generate and cache (TTL: 1 hour)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       VECTOR STORE                               │
│                    (Qdrant v1.7.4)                               │
│                                                                  │
│  Collection: conversation_embeddings                             │
│  Search: Hybrid (semantic + keyword boost)                       │
│  Filters: user_id = "user-123"                                  │
│                                                                  │
│  Results:                                                        │
│    1. "Added Netflix subscription" (score: 0.89)                │
│    2. "Added Disney+ for streaming" (score: 0.85)               │
│    3. "Cancelled Hulu" (score: 0.72)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       RAG SERVICE                                │
│                  (Context Orchestration)                         │
│                                                                  │
│  1. Get recent conversation turns (last 5)                      │
│  2. Get semantic search results (top 3)                         │
│  3. Resolve references ("my" → user's, "it" → Netflix)         │
│  4. Build context for Claude                                    │
│                                                                  │
│  Output Context:                                                 │
│    Recent: User mentioned Netflix, Disney+                      │
│    Relevant: Has Netflix (£15.99), Disney+ (£8.99)             │
│    Resolved: "streaming subscription" → Netflix, Disney+        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CLAUDE AGENT                                   │
│           (With context-enriched prompt)                         │
│                                                                  │
│  System: You are managing subscriptions for user-123.           │
│          They have: Netflix (£15.99), Disney+ (£8.99)           │
│          Recent conversation: Added Netflix yesterday           │
│                                                                  │
│  Response: "Which streaming subscription would you like to      │
│            cancel? You have Netflix (£15.99/month) and          │
│            Disney+ (£8.99/month)."                              │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 RAG Components

#### EmbeddingService

```python
class EmbeddingService:
    MODEL_NAME = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384

    async def embed(self, text: str) -> list[float]:
        # Check cache first
        cache_key = f"emb:{self.MODEL_NAME}:{hashlib.md5(text.encode()).hexdigest()}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # Generate embedding
        embedding = self.model.encode(text).tolist()

        # Cache for 1 hour
        await self.cache.set(cache_key, embedding, ttl=3600)
        return embedding
```

#### VectorStore

```python
class VectorStore:
    COLLECTIONS = {
        "conversations": "conversation_embeddings",
        "notes": "note_embeddings",
    }

    async def hybrid_search(
        self,
        collection: str,
        query_vector: list[float],
        keywords: list[str],
        limit: int = 5,
        user_id: str | None = None,
    ) -> list[ScoredPoint]:
        # Semantic search
        semantic_results = await self.client.search(
            collection_name=self.COLLECTIONS[collection],
            query_vector=query_vector,
            limit=limit * 2,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            ) if user_id else None,
        )

        # Keyword boost
        for result in semantic_results:
            text = result.payload.get("content", "").lower()
            keyword_matches = sum(1 for kw in keywords if kw.lower() in text)
            result.score += keyword_matches * 0.1  # Boost

        # Re-sort and limit
        semantic_results.sort(key=lambda x: x.score, reverse=True)
        return semantic_results[:limit]
```

#### RAGService

```python
class RAGService:
    async def get_context(
        self,
        query: str,
        user_id: str,
        session_id: str,
    ) -> ConversationContext:
        # Get recent turns
        recent = await self.conversation_service.get_recent(
            user_id=user_id,
            session_id=session_id,
            limit=5,
        )

        # Embed query
        query_embedding = await self.embedding_service.embed(query)

        # Search relevant context
        relevant = await self.vector_store.hybrid_search(
            collection="conversations",
            query_vector=query_embedding,
            keywords=self._extract_keywords(query),
            user_id=user_id,
        )

        # Extract entities from recent context
        entities = self._extract_entities(recent)

        return ConversationContext(
            recent_turns=recent,
            relevant_history=relevant,
            entities=entities,
        )

    async def resolve_references(
        self,
        query: str,
        context: ConversationContext,
    ) -> str:
        """Resolve pronouns like 'it', 'that', 'my subscription'."""
        resolved = query

        # "it" → most recent entity
        if " it " in query.lower() or query.lower().endswith(" it"):
            if context.entities:
                resolved = resolved.replace(" it", f" {context.entities[0]}")

        return resolved
```

### 11.3 RAG Analytics

```python
class RAGAnalyticsService:
    async def log_query(self, metrics: QueryMetrics):
        """Log query metrics to database."""
        record = RAGAnalytics(
            user_id=metrics.user_id,
            query=metrics.query,
            embedding_latency_ms=metrics.embedding_latency,
            search_latency_ms=metrics.search_latency,
            total_latency_ms=metrics.total_latency,
            cache_hit=metrics.cache_hit,
            results_count=metrics.results_count,
            top_score=metrics.top_score,
        )
        await self.db.add(record)
        await self.db.commit()

    async def get_daily_report(self, date: date) -> dict:
        """Get daily aggregated metrics."""
        return {
            "total_queries": await self._count_queries(date),
            "avg_latency_ms": await self._avg_latency(date),
            "cache_hit_rate": await self._cache_hit_rate(date),
            "error_rate": await self._error_rate(date),
        }
```

### 11.4 RAG Implementation Phases

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** | ✅ Complete | Database models, conversation storage |
| **Phase 2** | ✅ Complete | Embedding service, Sentence Transformers |
| **Phase 3** | ✅ Complete | Vector store, Qdrant integration |
| **Phase 4** | ✅ Complete | Redis caching, hybrid search, analytics |

---

## 12. Docker Infrastructure

### 12.1 Service Configuration

```yaml
# docker-compose.yml

services:
  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    container_name: subscription-db
    environment:
      POSTGRES_USER: subscriptions
      POSTGRES_PASSWORD: localdev
      POSTGRES_DB: subscriptions
    ports:
      - "5433:5432"  # Host:Container
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U subscriptions"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Backend
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: subscription-backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://subscriptions:localdev@db:5432/subscriptions
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "8001:8000"
    volumes:
      - ./src:/app/src  # Hot-reload
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  # Next.js Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: subscription-frontend
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8001
      - BACKEND_URL=http://backend:8000
    ports:
      - "3002:3000"
    volumes:
      - ./frontend/src:/app/src  # Hot-reload
    depends_on:
      - backend

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: subscription-redis
    ports:
      - "6380:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: subscription-qdrant
    ports:
      - "6333:6333"  # HTTP
      - "6334:6334"  # gRPC
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 10s

volumes:
  postgres_data:
  redis_data:
  qdrant_data:

networks:
  default:
    name: subscription-network
    driver: bridge
```

### 12.2 Backend Dockerfile

```dockerfile
# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application code
COPY src/ ./src/
COPY alembic.ini .

# Run migrations and start server
CMD alembic upgrade head && \
    uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 12.3 Frontend Dockerfile

```dockerfile
# frontend/Dockerfile

FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy application code
COPY . .

# Build for production
RUN npm run build

# Start server
CMD ["npm", "start"]
```

### 12.4 Container Communication

| From | To | Protocol | URL |
|------|-----|----------|-----|
| Frontend | Backend | HTTP | `http://backend:8000` |
| Backend | Database | PostgreSQL | `postgresql://db:5432` |
| Backend | Redis | Redis | `redis://redis:6379` |
| Backend | Qdrant | HTTP/gRPC | `http://qdrant:6333` |
| Browser | Frontend | HTTP | `http://localhost:3002` |
| Browser | Backend | HTTP | `http://localhost:8001` |

### 12.5 Common Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild specific service
docker-compose up -d --build backend

# Stop all services
docker-compose down

# Reset database (WARNING: deletes data)
docker-compose down -v
docker-compose up -d

# Enter container shell
docker exec -it subscription-backend bash
docker exec -it subscription-db psql -U subscriptions

# Check container health
docker-compose ps
```

---

## 13. Data Flow Diagrams

### 13.1 Create Subscription Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  User    │    │ Frontend │    │ Backend  │    │ Database │
└────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │               │
     │ Fill form     │               │               │
     │──────────────>│               │               │
     │               │               │               │
     │               │ POST /api/subscriptions       │
     │               │──────────────>│               │
     │               │               │               │
     │               │               │ Validate      │
     │               │               │──────┐        │
     │               │               │<─────┘        │
     │               │               │               │
     │               │               │ Calculate     │
     │               │               │ next_payment  │
     │               │               │──────┐        │
     │               │               │<─────┘        │
     │               │               │               │
     │               │               │ INSERT        │
     │               │               │──────────────>│
     │               │               │               │
     │               │               │<──────────────│
     │               │               │  Success      │
     │               │               │               │
     │               │<──────────────│               │
     │               │  SubscriptionResponse         │
     │               │               │               │
     │               │ Invalidate    │               │
     │               │ Query Cache   │               │
     │               │──────┐        │               │
     │               │<─────┘        │               │
     │               │               │               │
     │<──────────────│               │               │
     │ Show success  │               │               │
     │               │               │               │
```

### 13.2 Agent Command Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  User    │    │ Frontend │    │  Agent   │    │  Claude  │    │ Database │
└────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │               │               │
     │ "Add Netflix" │               │               │               │
     │──────────────>│               │               │               │
     │               │               │               │               │
     │               │ POST /agent/execute           │               │
     │               │──────────────>│               │               │
     │               │               │               │               │
     │               │               │ Get RAG       │               │
     │               │               │ Context       │               │
     │               │               │──────┐        │               │
     │               │               │<─────┘        │               │
     │               │               │               │               │
     │               │               │ messages.create               │
     │               │               │──────────────>│               │
     │               │               │               │               │
     │               │               │<──────────────│               │
     │               │               │ tool_use:     │               │
     │               │               │ create_sub    │               │
     │               │               │               │               │
     │               │               │ Execute tool  │               │
     │               │               │──────────────────────────────>│
     │               │               │               │               │
     │               │               │<──────────────────────────────│
     │               │               │    Subscription created       │
     │               │               │               │               │
     │               │               │ Store         │               │
     │               │               │ conversation  │               │
     │               │               │──────────────────────────────>│
     │               │               │               │               │
     │               │<──────────────│               │               │
     │               │ AgentResponse │               │               │
     │               │               │               │               │
     │<──────────────│               │               │               │
     │ "Added Netflix - £15.99/month"│               │               │
     │               │               │               │               │
```

### 13.3 Calendar Events Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  User    │    │ Frontend │    │ Backend  │    │ Database │
└────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │               │
     │ View calendar │               │               │
     │──────────────>│               │               │
     │               │               │               │
     │               │ GET /calendar/events          │
     │               │ ?start=2025-01-01             │
     │               │ &end=2025-01-31               │
     │               │──────────────>│               │
     │               │               │               │
     │               │               │ Query active  │
     │               │               │ subscriptions │
     │               │               │──────────────>│
     │               │               │               │
     │               │               │<──────────────│
     │               │               │               │
     │               │               │ Generate      │
     │               │               │ events for    │
     │               │               │ date range    │
     │               │               │──────┐        │
     │               │               │<─────┘        │
     │               │               │               │
     │               │<──────────────│               │
     │               │ CalendarEvent[]               │
     │               │               │               │
     │               │ Render grid   │               │
     │               │ with events   │               │
     │               │──────┐        │               │
     │               │<─────┘        │               │
     │               │               │               │
     │<──────────────│               │               │
     │ Display       │               │               │
     │ calendar      │               │               │
     │               │               │               │
```

---

## 14. Payment Types

### 14.1 Type Definitions

| Type | Description | Special Fields | Auto-Detection Keywords |
|------|-------------|----------------|------------------------|
| **SUBSCRIPTION** | Digital services, streaming | Standard | netflix, spotify, disney, streaming, premium |
| **HOUSING** | Rent, mortgage | Standard | rent, mortgage, landlord, property |
| **UTILITY** | Electric, gas, water, internet | Standard | electric, gas, water, council tax, broadband |
| **PROFESSIONAL_SERVICE** | Therapist, coach, trainer | Standard | therapist, coach, trainer, tutor, lesson |
| **INSURANCE** | Health, device, vehicle | Standard | insurance, bupa, applecare |
| **DEBT** | Credit cards, loans | total_owed, remaining_balance, creditor | debt, loan, owe, credit card |
| **SAVINGS** | Goals with targets | target_amount, current_saved, recipient | savings, goal, target, save for |
| **TRANSFER** | Family support, gifts | recipient | transfer, send, gift, family |
| **ONE_TIME** | One-off payments | end_date = start_date | one-time, one time, single |

### 14.2 Debt Tracking

```
┌────────────────────────────────────────────────────────┐
│                    DEBT: Credit Card                    │
├────────────────────────────────────────────────────────┤
│  Monthly Payment: £200                                  │
│  Creditor: Barclays                                     │
│  Total Owed: £5,000                                     │
│  Remaining: £3,500                                      │
│                                                         │
│  Progress: ████████░░░░░░░░░░░░ 30%                    │
│                                                         │
│  Paid Off: £1,500                                       │
│  Payments Remaining: ~18                                │
└────────────────────────────────────────────────────────┘
```

### 14.3 Savings Tracking

```
┌────────────────────────────────────────────────────────┐
│                 SAVINGS: Holiday Fund                   │
├────────────────────────────────────────────────────────┤
│  Monthly Contribution: £500                             │
│  Target: £10,000                                        │
│  Current Saved: £3,500                                  │
│                                                         │
│  Progress: ███████░░░░░░░░░░░░░ 35%                    │
│                                                         │
│  Remaining: £6,500                                      │
│  Est. Completion: ~13 months                            │
└────────────────────────────────────────────────────────┘
```

### 14.4 Installment Tracking

```
┌────────────────────────────────────────────────────────┐
│              INSTALLMENT: MacBook Air 15"               │
├────────────────────────────────────────────────────────┤
│  Monthly Payment: ₴7,140                                │
│  Total Installments: 10                                 │
│  Completed: 0                                           │
│                                                         │
│  Progress: ░░░░░░░░░░░░░░░░░░░░ 0%                     │
│                                                         │
│  Start Date: January 10, 2026                           │
│  End Date: October 10, 2026                             │
└────────────────────────────────────────────────────────┘
```

---

## 15. Currency System

### 15.1 Supported Currencies

| Currency | Symbol | Code | Status |
|----------|--------|------|--------|
| British Pound | £ | GBP | **Default** |
| US Dollar | $ | USD | Supported |
| Euro | € | EUR | Supported |
| Ukrainian Hryvnia | ₴ | UAH | Supported |

### 15.2 Exchange Rate Flow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Frontend   │    │   Backend    │    │  External    │
│              │    │ CurrencyService   │    API        │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │ Request rate      │                   │
       │──────────────────>│                   │
       │                   │                   │
       │                   │ Check Redis cache │
       │                   │──────┐            │
       │                   │<─────┘            │
       │                   │                   │
       │                   │ Cache miss?       │
       │                   │──────────────────>│
       │                   │                   │
       │                   │<──────────────────│
       │                   │    Live rates     │
       │                   │                   │
       │                   │ Cache for 1 hour  │
       │                   │──────┐            │
       │                   │<─────┘            │
       │                   │                   │
       │<──────────────────│                   │
       │      Rate         │                   │
       │                   │                   │
```

### 15.3 Fallback Rates

If external API is unavailable:

```python
FALLBACK_RATES = {
    "GBP": {"USD": 1.27, "EUR": 1.17, "UAH": 52.0},
    "USD": {"GBP": 0.79, "EUR": 0.92, "UAH": 41.0},
    "EUR": {"GBP": 0.85, "USD": 1.09, "UAH": 44.5},
    "UAH": {"GBP": 0.019, "USD": 0.024, "EUR": 0.022},
}
```

---

## 16. Testing Strategy

### 16.1 Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── unit/                       # Unit tests
│   ├── test_parser.py          # Command parsing
│   ├── test_executor.py        # Command execution
│   ├── test_models.py          # ORM models
│   ├── test_schemas.py         # Pydantic validation
│   ├── test_cache_service.py   # Redis caching
│   ├── test_currency_service.py # Currency conversion
│   ├── test_subscription_service.py # CRUD operations
│   ├── test_rag_services.py    # RAG functionality
│   └── test_vector_store_hybrid.py # Hybrid search
└── integration/                # Integration tests
    ├── test_api.py             # API endpoints
    ├── test_analytics_api.py   # Analytics endpoints
    ├── test_import_export_api.py # Import/export
    └── test_search_api.py      # Search endpoints
```

### 16.2 Test Configuration

```python
# pyproject.toml

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --tb=short"
```

### 16.3 Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_parser.py -v

# By marker
pytest -m "unit"
pytest -m "integration"

# Parallel execution
pytest -n auto
```

### 16.4 Test Fixtures

```python
# tests/conftest.py

@pytest.fixture
async def db_session():
    """Create test database session."""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
def sample_subscription():
    """Create sample subscription for tests."""
    return Subscription(
        name="Test Netflix",
        amount=Decimal("15.99"),
        currency="GBP",
        frequency=Frequency.MONTHLY,
        payment_type=PaymentType.SUBSCRIPTION,
        start_date=date.today(),
        next_payment_date=date.today(),
    )

@pytest.fixture
def mock_claude_response():
    """Mock Claude API response."""
    return {
        "content": [{"text": "Added Netflix - £15.99 monthly"}],
        "stop_reason": "end_turn",
    }
```

---

## 17. Development Workflow

### 17.1 Setup

```bash
# Clone repository
git clone <repo-url>
cd subscription-tracker

# Create .env file
cp .env.example .env
# Add ANTHROPIC_API_KEY

# Start Docker services
docker-compose up -d

# Access application
open http://localhost:3002
```

### 17.2 Development Commands

```bash
# View logs
docker-compose logs -f backend

# Restart service
docker-compose restart backend

# Rebuild after code changes
docker-compose up -d --build backend

# Run tests
docker exec -it subscription-backend pytest

# Code quality
docker exec -it subscription-backend ruff check src/
docker exec -it subscription-backend ruff format src/

# Database migration
docker exec -it subscription-backend alembic revision --autogenerate -m "description"
docker exec -it subscription-backend alembic upgrade head
```

### 17.3 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml

repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy

  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: detect-private-key
```

### 17.4 Code Standards

**Python:**
- PEP 8 compliance
- Type hints required
- Google-style docstrings
- 100 character line length
- Async/await for I/O

**TypeScript:**
- Strict mode enabled
- PascalCase for components
- camelCase for functions
- Explicit return types

---

## 18. Deployment Guide

### 18.1 Local Deployment

```bash
# Start all services
docker-compose up -d

# Verify health
curl http://localhost:8001/health
# {"status": "healthy"}

# Access frontend
open http://localhost:3002
```

### 18.2 GCP Cloud Run Deployment

```bash
# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Deploy backend
gcloud run deploy subscription-tracker-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=..." \
  --set-secrets "ANTHROPIC_API_KEY=anthropic-key:latest"

# Deploy frontend
cd frontend
gcloud run deploy subscription-tracker-frontend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "NEXT_PUBLIC_API_URL=https://backend-url"
```

### 18.3 Environment Variables (Production)

```env
# Database (Cloud SQL)
DATABASE_URL=postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/project:region:instance

# API
API_HOST=0.0.0.0
API_PORT=8080
DEBUG=false

# Claude API
ANTHROPIC_API_KEY=sk-ant-api03-...

# CORS
CORS_ORIGINS=["https://your-frontend.run.app"]

# Redis (optional, Cloud Memorystore)
REDIS_URL=redis://10.0.0.1:6379/0

# Qdrant (optional, managed or self-hosted)
QDRANT_HOST=qdrant.example.com
QDRANT_PORT=6333
```

---

## 19. Configuration Reference

### 19.1 Backend Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Required | PostgreSQL connection string |
| `API_HOST` | `0.0.0.0` | Server bind address |
| `API_PORT` | `8000` | Server port |
| `DEBUG` | `false` | Debug mode (enables hot-reload) |
| `ANTHROPIC_API_KEY` | Required | Claude API key |
| `CORS_ORIGINS` | `[]` | Allowed CORS origins |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `QDRANT_HOST` | `localhost` | Qdrant host |
| `QDRANT_PORT` | `6333` | Qdrant port |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence Transformer model |
| `RAG_ENABLED` | `true` | Enable RAG features |

### 19.2 Frontend Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8001` | Backend API URL (browser) |
| `BACKEND_URL` | `http://backend:8000` | Backend URL (server-side) |

---

## 20. Troubleshooting

### 20.1 Common Issues

#### Database Connection Failed

```
Error: Connection refused to db:5432
```

**Solution:**
```bash
# Check if database is running
docker-compose ps db

# Start database
docker-compose up -d db

# Wait for health check
docker-compose logs -f db

# Restart backend after DB is healthy
docker-compose restart backend
```

#### Backend Crashes on Startup

```
Error: Application startup failed
```

**Solution:**
```bash
# Check backend logs
docker-compose logs backend

# Common causes:
# 1. Database not ready - restart backend after DB is healthy
# 2. Missing environment variables - check .env file
# 3. Port already in use - change ports in docker-compose.yml
```

#### Frontend Cannot Connect to Backend

```
Error: Network Error
```

**Solution:**
1. Check backend is running: `curl http://localhost:8001/health`
2. Check CORS settings include frontend origin
3. Verify Next.js config has API rewrites

#### Redis Connection Failed

```
Error: Redis connection refused
```

**Solution:**
```bash
# Check Redis status
docker-compose ps redis

# Start Redis
docker-compose up -d redis

# Verify connection
docker exec -it subscription-redis redis-cli ping
# Should return: PONG
```

### 20.2 Reset Commands

```bash
# Full reset (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d

# Reset database only
docker-compose exec db psql -U subscriptions -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker-compose restart backend

# Clear Redis cache
docker exec -it subscription-redis redis-cli FLUSHALL

# Rebuild all containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 21. Future Roadmap

### 21.1 Planned Features

| Feature | Priority | Status |
|---------|----------|--------|
| **Subscription Templates** | High | Planned |
| **Payment Reminders** | High | Planned |
| **Mobile App** | Medium | Planned |
| **Budget Alerts** | Medium | Planned |
| **Multi-user Support** | Medium | Planned |
| **Recurring Transfer Automation** | Low | Planned |
| **Bank Integration** | Low | Research |

### 21.2 Technical Improvements

| Improvement | Priority | Status |
|-------------|----------|--------|
| **GraphQL API** | Medium | Planned |
| **WebSocket for Real-time** | Medium | Planned |
| **Kubernetes Deployment** | Low | Planned |
| **E2E Testing** | Medium | Planned |
| **Performance Monitoring** | High | Planned |

---

## Appendix A: Quick Reference

### Access URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3002 |
| Backend API | http://localhost:8001 |
| API Documentation | http://localhost:8001/docs |
| Health Check | http://localhost:8001/health |
| Database | localhost:5433 |
| Redis | localhost:6380 |
| Qdrant | localhost:6333 |

### Common Commands

```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# View logs
docker-compose logs -f

# Rebuild
docker-compose up -d --build

# Run tests
pytest tests/ -v

# Code quality
ruff check src/ --fix && ruff format src/
```

### Key Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Container orchestration |
| `src/main.py` | Backend entry point |
| `src/models/subscription.py` | Core data model |
| `src/agent/conversational_agent.py` | AI agent |
| `frontend/src/app/page.tsx` | Main dashboard |
| `frontend/src/lib/api.ts` | API client |

---

**Document Version**: 1.0.0
**Generated**: December 13, 2025
**Total Pages**: ~100 (equivalent)
**Word Count**: ~15,000 words

---

*This document was generated for the Money Flow (Subscription Tracker) project. For updates, please refer to the repository.*
