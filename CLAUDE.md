# Money Flow - Claude Code Guide

> **Note**: This project is being renamed from "Subscription Tracker" to "**Money Flow**" to reflect its expanded scope. See [Money Flow Refactor Plan](.claude/plans/MONEY_FLOW_REFACTOR_PLAN.md) for details.

---

## 🚀 MASTER DEVELOPMENT PLAN

> **NEW**: A comprehensive 16-week roadmap for production-ready enhancement.
> **Full Plan**: [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) (~400 hours, 250+ tasks)

### Current Phase & Sprint

| Phase | Sprint | Status | Focus |
|-------|--------|--------|-------|
| **Phase 1** | Sprint 1.1 | ✅ Complete | Authentication System |
| **Phase 1** | Sprint 1.2 | ✅ Complete | Security Hardening |
| **Phase 1** | Sprint 1.3 | ✅ Complete | CI/CD Pipeline |

### Sprint 1.3 Tasks (Week 3) - CI/CD Pipeline ✅

| Task | Status | Description |
|------|--------|-------------|
| 1.3.1 | ✅ DONE | GitHub Actions Setup (.github/workflows/) |
| 1.3.2 | ✅ DONE | Test Automation Pipeline (pytest, coverage) |
| 1.3.3 | ✅ DONE | Code Quality Gates (Ruff, ESLint, pre-commit, PR template) |
| 1.3.4 | ✅ DONE | Security Scanning (Bandit, Safety, npm audit) |
| 1.3.5 | ✅ DONE | Docker Build Pipeline (GHCR, multi-arch) |
| 1.3.6 | ✅ DONE | Deployment Automation (staging/prod, rollback, Telegram alerts) |

**CI/CD Features Implemented:**
- GitHub Actions CI: Python 3.11/3.12 matrix, PostgreSQL + Redis services
- Code quality: Ruff linting/formatting, ESLint, TypeScript type-check
- Pre-commit hooks: Ruff, Prettier, trailing whitespace, detect-secrets
- Security: Bandit scan, Safety dependency check, npm audit
- Docker: Build & push to GHCR, multi-arch (amd64/arm64), image tagging
- Deploy: Staging on main push, production on release, rollback support
- Notifications: Telegram alerts for deployments, rollbacks, and failures
- PR template: Standardized pull request format

### Sprint 1.2 Tasks (Week 2) - Security Hardening ✅

| Task | Status | Description |
|------|--------|-------------|
| 1.2.1 | ✅ DONE | Rate Limiting (slowapi + Redis) |
| 1.2.2 | ✅ DONE | Prompt Injection Protection |
| 1.2.3 | ✅ DONE | Input Validation Enhancement |
| 1.2.4 | ✅ DONE | Security Headers (CSP, HSTS, etc.) |
| 1.2.5 | ✅ DONE | CORS Hardening |
| 1.2.6 | ✅ DONE | Secrets Management |

**Security Features Implemented:**
- Rate limiting: 100/min GET, 20/min writes, 10/min agent, 5/min auth
- Prompt injection: 20+ detection patterns, blocked dangerous commands
- Input validation: Password strength, XSS/SQL detection, URL safety
- Security headers: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- CORS: No wildcards in production, specific methods/headers
- Secrets: Startup validation, blocks production with default secrets

### Sprint 1.1 Tasks (Week 1) - Authentication ✅

| Task | Status | Description |
|------|--------|-------------|
| 1.1.1 | ✅ DONE | Database Schema for Users |
| 1.1.2 | ✅ DONE | Password Security (bcrypt) |
| 1.1.3 | ✅ DONE | JWT Token System |
| 1.1.4 | ✅ DONE | Auth API Endpoints |
| 1.1.5 | ✅ DONE | Auth Middleware |

### Known Issues to Fix (Sprint 2.2)

| Issue | Priority | Status |
|-------|----------|--------|
| Subscription summary calculation bugs | 🔴 Critical | ⬜ TODO |
| Upcoming payments date filtering | 🔴 Critical | ⬜ TODO |
| Currency conversion edge cases | 🟠 High | ⬜ TODO |
| Debt balance calculation | 🔴 Critical | ⬜ TODO |
| Savings progress calculation | 🔴 Critical | ⬜ TODO |
| Card balance aggregation | 🟠 High | ⬜ TODO |
| Export format inconsistencies | 🟠 High | ⬜ TODO |

### Security Gaps (Sprint 1.2) ✅ ALL RESOLVED

| Gap | Priority | Status |
|-----|----------|--------|
| No authentication | 🔴 Critical | ✅ DONE (Sprint 1.1) |
| No rate limiting | 🔴 Critical | ✅ DONE |
| Prompt injection vulnerable | 🔴 Critical | ✅ DONE |
| CORS not hardened | 🟠 High | ✅ DONE |
| No audit logging | 🟡 Medium | ⬜ TODO (Sprint 1.4) |

### Phase Overview

```
Phase 1: Foundation & Security  [Weeks 1-4]   ████████░░ 75% (Sprint 1.1, 1.2, 1.3 complete)
Phase 2: Quality & Testing      [Weeks 5-8]   ░░░░░░░░░░ 0%
Phase 3: Architecture           [Weeks 9-12]  ░░░░░░░░░░ 0%
Phase 4: Features & Polish      [Weeks 13-16] ░░░░░░░░░░ 0%
```

---

## 🎯 Project Overview

A comprehensive **recurring payment management application** with an **agentic interface** that allows natural language commands to manage all types of recurring payments. Features a modern, responsive UI built with Next.js and Tailwind CSS.

### Current Status
- ✅ Multi-container Docker setup (PostgreSQL + FastAPI + Next.js + Redis + Qdrant)
- ✅ Agentic interface with Claude Haiku 4.5 and XML prompting
- ✅ CRUD operations for all payment types
- ✅ Natural language command parsing (dual-mode: AI + regex fallback)
- ✅ Currency conversion (GBP default, USD, EUR, UAH support)
- ✅ Import/Export functionality (JSON & CSV v2.0)
- ✅ RAG implementation complete (all 4 phases - see [RAG Plan](.claude/plans/RAG_PLAN.md))
- ✅ **Money Flow Refactor Complete** - All 8 payment types supported (see [Money Flow Plan](.claude/plans/MONEY_FLOW_REFACTOR_PLAN.md))
- 🟡 **Master Plan Active** - Production-ready enhancement in progress

### Tech Stack
- **Frontend**: Next.js 16, TypeScript, Tailwind CSS v4, React Query, Framer Motion
- **Backend**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL 15 (Docker local dev) → Cloud SQL (GCP production)
- **ORM**: SQLAlchemy 2.0 with async support
- **Validation**: Pydantic v2
- **AI**: Claude Haiku 4.5 (`claude-haiku-4.5-20250929`)
- **Prompting**: XML-based prompts with PromptLoader
- **Caching**: Redis (embedding cache, performance)
- **Vector DB**: Qdrant (RAG, semantic search)
- **Deployment**: Multi-container Docker → GCP Cloud Run

### Key Features
- 🤖 **Natural language interface** - "Add Netflix for £15.99 monthly"
- 💱 **Currency conversion** - GBP, USD, EUR, UAH with exchange rates
- 📊 **Spending analytics** - Summaries by frequency and category
- 🔄 **Dual-mode parsing** - AI with regex fallback for reliability
- 🐳 **Docker containerized** - Easy local development and deployment
- 🎨 **Modern UI** - Tailwind CSS with responsive design
- 📥 **Import/Export** - Backup and restore data (JSON/CSV)
- 🧠 **RAG-powered** - Conversational context, semantic search, intelligent insights

### Supported Payment Types ✅

Money Flow supports **all recurring payment types**:

| Payment Type | Examples | Special Features |
|--------------|----------|------------------|
| **Subscriptions** | Netflix, Claude AI, Spotify | Standard tracking |
| **Housing** | Rent, mortgage | Auto-classified |
| **Utilities** | Electric, water, council tax, internet | Auto-classified |
| **Professional Services** | Therapist, coach, trainer | Auto-classified |
| **Insurance** | Health, device (AppleCare), vehicle | Auto-classified |
| **Debts** | Credit cards, loans, friends/family | Track total_owed, remaining_balance, creditor |
| **Savings** | Regular transfers, goals with targets | Track target_amount, current_saved, recipient |
| **Transfers** | Family support, recurring gifts | Track recipient |

See [Money Flow Refactor Plan](.claude/plans/MONEY_FLOW_REFACTOR_PLAN.md) for implementation details.

---

## 📁 Project Structure

```
subscription-tracker/
├── CLAUDE.md              # YOU ARE HERE - Claude Code instructions
├── docker-compose.yml     # Multi-container orchestration
├── .env                   # Environment variables (not in git)
├── .env.example          # Example env vars
├── docs/                  # 📋 NEW: Project documentation
│   └── MASTER_PLAN.md    # 🆕 16-week production roadmap
│
├── frontend/             # Next.js Frontend Application
│   ├── Dockerfile        # Frontend container
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.mjs
│   ├── src/
│   │   ├── app/          # Next.js app router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx  # Main dashboard
│   │   │   ├── globals.css
│   │   │   └── providers.tsx
│   │   ├── components/   # React components
│   │   │   ├── Header.tsx
│   │   │   ├── StatsPanel.tsx
│   │   │   ├── SubscriptionList.tsx
│   │   │   ├── AddSubscriptionModal.tsx
│   │   │   └── AgentChat.tsx
│   │   ├── lib/          # Utilities
│   │   │   ├── api.ts    # Backend API client
│   │   │   └── utils.ts  # Helper functions
│   │   └── hooks/        # Custom React hooks
│   └── public/           # Static assets
│
├── src/                  # Backend Python Application
│   ├── main.py           # FastAPI application entry point
│   ├── api/              # API route handlers
│   │   ├── __init__.py
│   │   ├── subscriptions.py  # CRUD endpoints
│   │   └── agent.py          # Agentic/prompt endpoint
│   ├── core/             # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py     # Settings and env vars
│   │   └── dependencies.py
│   ├── db/               # Database setup
│   │   ├── __init__.py
│   │   ├── database.py   # Engine and session
│   │   └── migrations/   # Alembic migrations
│   ├── models/           # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   └── subscription.py
│   ├── schemas/          # Pydantic schemas
│   │   ├── __init__.py
│   │   └── subscription.py
│   ├── services/         # Business logic
│   │   ├── __init__.py
│   │   └── subscription_service.py
│   ├── auth/             # 🆕 Authentication (Sprint 1.1)
│   │   ├── __init__.py
│   │   ├── jwt.py        # JWT token handling
│   │   ├── security.py   # Password hashing
│   │   └── dependencies.py # Auth middleware
│   └── agent/            # Agentic interface
│       ├── __init__.py
│       ├── parser.py     # NL command parser
│       ├── executor.py   # Command executor
│       └── prompts.py    # System prompts for Claude
│
├── tests/                # Pytest tests
├── scripts/              # Utility scripts
├── docs/                 # Documentation
├── deploy/               # Deployment configs
│   └── gcp/              # GCP-specific configs
├── Dockerfile            # Backend container
└── pyproject.toml        # Python dependencies
```

---

## 🔧 Common Commands

### Docker Multi-Container Setup (Recommended)

```bash
# Start all services (DB + Backend + Frontend)
docker-compose up --build

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild specific service
docker-compose up --build backend
docker-compose up --build frontend
```

### Local Development (Without Docker)

#### Backend
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate.fish  # For Fish shell
source .venv/bin/activate       # For Bash/Zsh

# Install dependencies
pip install -e ".[dev]"

# Run development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8001

# Run tests
pytest tests/ -v

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run production server
npm start
```

### Code Quality (Run Before Commits)

```bash
# Python linting and formatting
ruff check src/ --fix && ruff format src/

# Run all tests
pytest tests/ -v --cov=src --cov-report=term-missing

# Pre-commit hooks
pre-commit run --all-files
```

### GCP Deployment

```bash
# Deploy backend
gcloud run deploy subscription-tracker-backend --source .

# Deploy frontend
cd frontend && gcloud run deploy subscription-tracker-frontend --source .
```

---

## 🐳 Docker Architecture

The application uses a multi-container setup with five main services:

### Services

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| Database | subscription-db | 5433:5432 | PostgreSQL data storage |
| Backend | subscription-backend | 8001:8000 | FastAPI application |
| Frontend | subscription-frontend | 3001:3000 | Next.js web app |
| Cache | subscription-redis | 6379:6379 | Redis caching |
| Vectors | subscription-qdrant | 6333:6333 | Qdrant vector DB |

### Network

All services communicate via `subscription-network` Docker bridge network.

---

## 📚 Development Documentation

**IMPORTANT**: Start here for complete project context: [.claude/README.md](.claude/README.md)

### Project Context & History
- **[CHANGELOG](.claude/CHANGELOG.md)** - 📋 Complete development history, milestones, issues resolved, and major decisions
  - All features implemented with file links
  - Issues fixed with solutions
  - Technical decisions with rationale
  - **Always check here first to understand what has been done and why**

### Master Plan & Roadmap
- **[MASTER_PLAN](docs/MASTER_PLAN.md)** - 🆕 16-week production roadmap (400+ tasks)
  - Phase 1: Foundation & Security (Auth, CI/CD)
  - Phase 2: Quality & Testing (E2E, Bug fixes)
  - Phase 3: Architecture (API versioning, Monitoring)
  - Phase 4: Features & Polish (Custom Skills, Mobile)

### Coding Standards
- [Python Coding Standards](.claude/docs/PYTHON_STANDARDS.md) - PEP 8 compliance, type hints, **comprehensive docstrings**, **agentic naming**, **Redis caching patterns**
- [TypeScript/React Standards](.claude/docs/TYPESCRIPT_STANDARDS.md) - Strict TypeScript, React best practices, ESLint & Prettier configuration
- [Pre-commit Hooks](.claude/docs/PRE_COMMIT_HOOKS.md) - Automated code quality checks, linting, formatting, secret detection

### Architecture & Setup
- [System Architecture](.claude/docs/ARCHITECTURE.md) - Complete system design, 6-layer architecture, data flow, microservices path
- [MCP (Model Context Protocol) Setup](.claude/docs/MCP_SETUP.md) - Enhancing Claude Code with database, git, and custom MCPs
- [RAG Considerations](.claude/docs/RAG_CONSIDERATIONS.md) - When to use RAG, cost-benefit analysis, implementation examples

### Implementation Plans
- [Money Flow Refactor Plan](.claude/plans/MONEY_FLOW_REFACTOR_PLAN.md) - ✅ **COMPLETE** - All 8 payment types supported
- [RAG Plan](.claude/plans/RAG_PLAN.md) - ✅ **COMPLETE** - Conversational context, semantic search, intelligent insights
- [Payment Tracking Plan](.claude/plans/PAYMENT_TRACKING_PLAN.md) - Calendar view, installment payments, beautiful UI

### Development Tools
- [Code Templates](.claude/templates/README.md) - Python services, FastAPI routers, React components, custom hooks
- [Utility Scripts](.claude/scripts/README.md) - Setup, testing, code quality checks, database reset

### Quick Reference

**Python Code Style:**
- 100 character line length
- Google-style docstrings
- Type hints required for all functions
- Async/await for I/O operations
- 80%+ test coverage target
- **⚠️ IMPORTANT: Run `ruff check src/ --fix && ruff format src/` after modifying Python files**

**TypeScript Code Style:**
- Strict mode enabled
- PascalCase for components, camelCase for functions
- React Query for server state
- Tailwind CSS for styling
- ESLint + Prettier enforced

**Before Committing:**
```bash
# Install pre-commit hooks (one-time)
pip install pre-commit
pre-commit install

# Manually run all hooks
pre-commit run --all-files
```

---

## 💡 Claude Code Tips

When working on this project:

1. **Check Master Plan first**: See [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) for current sprint tasks
2. **Adding new features**: Start with the schema, then model, then service, then API
3. **Modifying models**: Always create an Alembic migration
4. **Agent commands**: Add new intents in parser.py, handlers in executor.py
5. **Testing**: Write tests alongside new features
6. **Code quality**: Pre-commit hooks will automatically lint and format your code

### Sprint Workflow

```bash
# 1. Check current sprint in this file (top section)
# 2. Pick a task from the current sprint
# 3. Implement the task
# 4. Update task status in this file
# 5. Commit with conventional commit message

git commit -m "feat(auth): add User model with SQLAlchemy"
```

### Code Style
- Use type hints everywhere
- Async/await for all database operations
- Pydantic for all external data validation
- Keep services thin, business logic in dedicated modules
- Refer to coding standards docs in [.claude/docs/](.claude/docs/)

---

## 📋 Important Context & History

### Always Check First
**[.claude/CHANGELOG.md](.claude/CHANGELOG.md)** - Complete development history including:
- ✅ All milestones achieved with dates
- 🐛 Issues resolved with solutions
- 📝 Major technical decisions with rationale
- 📊 Current project metrics
- 🎯 Next steps and timeline

**Why this matters**: The CHANGELOG preserves all context about what has been built, what problems were solved, and why specific decisions were made. Always check it before making changes to understand the full context.

### Key Technical Decisions Made

1. **Default Currency: GBP (£)**
   - Changed from USD to GBP per user requirement
   - Exchange rates configured for GBP/USD/EUR conversion
   - See [.claude/CHANGELOG.md](.claude/CHANGELOG.md#decision-1-default-currency---gbp-)

2. **XML-Based Prompting**
   - Structured prompts in `src/agent/prompts.xml`
   - Better maintainability and organization
   - See [.claude/CHANGELOG.md](.claude/CHANGELOG.md#decision-2-xml-based-prompting)

3. **Claude Haiku 4.5 Model**
   - Model: `claude-haiku-4.5-20250929`
   - Fast and cost-effective for intent classification
   - See [.claude/CHANGELOG.md](.claude/CHANGELOG.md#decision-3-claude-haiku-45-model)

4. **Dual-Mode Parsing (AI + Regex)**
   - Primary: Claude AI for intelligent parsing
   - Fallback: Regex patterns for reliability
   - Ensures system works even without API
   - See [.claude/CHANGELOG.md](.claude/CHANGELOG.md#decision-4-dual-mode-parsing-ai--regex)

5. **Redis Caching Strategy**
   - Cache parsed commands, queries, embeddings
   - Structured key pattern: `{resource}:{identifier}:{operation}`
   - See [Python Standards - Redis Caching](.claude/docs/PYTHON_STANDARDS.md#redis-caching)

### Issues Fixed

**Network Error (Fixed)**: Frontend couldn't communicate with backend in Docker.
- **Solution**: Added API rewrites in Next.js config, updated API client to use relative paths
- **See**: [.claude/CHANGELOG.md](.claude/CHANGELOG.md#issue-1-network-error-between-frontend-and-backend)

**Port Conflicts (Fixed)**: Ports 8000 and 3001 already in use.
- **Solution**: Changed to ports 8001 (backend) and 3002 (frontend)
- **See**: [.claude/CHANGELOG.md](.claude/CHANGELOG.md#issue-2-port-conflicts)

### Current Access URLs
- Frontend: http://localhost:3001
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs
- Database: localhost:5433
- Qdrant Dashboard: http://localhost:6333/dashboard

---

## 🚧 Development Workflow

### Before Starting New Work
1. Check current sprint in this file (top section)
2. Check [.claude/CHANGELOG.md](.claude/CHANGELOG.md) for context
3. Check [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) for task details
4. Review relevant implementation plan
5. Check coding standards

### During Development
1. Follow coding standards ([Python](.claude/docs/PYTHON_STANDARDS.md) | [TypeScript](.claude/docs/TYPESCRIPT_STANDARDS.md))
2. Write comprehensive docstrings with all sections
3. Add type hints everywhere
4. Write tests alongside code
5. Use templates from [.claude/templates/](.claude/templates/)

### Before Committing
```bash
# Run code quality checks
bash .claude/scripts/check_code_quality.sh

# Run tests
bash .claude/scripts/run_tests.sh

# Or use pre-commit hooks (auto-runs on git commit)
pre-commit run --all-files
```

### After Completing Work
1. **Update task status** in this file (top section)
2. **Update [.claude/CHANGELOG.md](.claude/CHANGELOG.md)** with:
   - Milestone achieved
   - Files modified
   - Issues resolved
   - Technical decisions made

This ensures context is preserved for future development.

---

## 🎓 Learning Resources

### For New Features
1. Review similar existing code
2. Use code templates from [.claude/templates/](.claude/templates/)
3. Follow implementation plans for complex features
4. Check architecture docs for design patterns

### For Understanding Agentic Code
- [Python Standards - Agentic Code](.claude/docs/PYTHON_STANDARDS.md#agentic-code-standards)
- [RAG Considerations](.claude/docs/RAG_CONSIDERATIONS.md)
- [RAG Plan](.claude/plans/RAG_PLAN.md)

### For Payment Tracking Features
- [Payment Tracking Plan](.claude/plans/PAYMENT_TRACKING_PLAN.md)
- Database schema changes
- Calendar component design
- Installment tracking implementation

---

## 🔗 Quick Links

### Documentation
- [.claude/README.md](.claude/README.md) - Complete .claude directory overview
- [.claude/CHANGELOG.md](.claude/CHANGELOG.md) - **Development history and context**
- [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) - 🆕 **16-week production roadmap**
- [ARCHITECTURE.md](.claude/docs/ARCHITECTURE.md) - System architecture
- [PYTHON_STANDARDS.md](.claude/docs/PYTHON_STANDARDS.md) - Python coding standards
- [TYPESCRIPT_STANDARDS.md](.claude/docs/TYPESCRIPT_STANDARDS.md) - TypeScript/React standards

### Plans
- [Master Plan](docs/MASTER_PLAN.md) - 🆕 **ACTIVE** - Production-ready enhancement
- [Money Flow Refactor](.claude/plans/MONEY_FLOW_REFACTOR_PLAN.md) - ✅ **COMPLETE** - All 8 payment types
- [RAG Plan](.claude/plans/RAG_PLAN.md) - ✅ **COMPLETE** - RAG implementation
- [Payment Tracking](.claude/plans/PAYMENT_TRACKING_PLAN.md) - Calendar view and installment payments

### Tools
- [Templates](.claude/templates/README.md) - Code templates
- [Scripts](.claude/scripts/README.md) - Utility scripts

---

**Last Updated**: 2025-12-13
**Version**: 2.1 (Master Plan Integration)
**Current Sprint**: 1.1 - Authentication System
**For Questions**: Check [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) or [.claude/CHANGELOG.md](.claude/CHANGELOG.md)