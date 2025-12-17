# Claude Code Configuration

This directory contains all configuration, documentation, templates, and scripts for Claude Code development of the Subscription Tracker project.

## 📂 Directory Structure

```
.claude/
├── README.md                    # This file
├── CHANGELOG.md                 # Development history & decisions
├── settings.local.json          # Claude Code local settings
├── docs/                        # Comprehensive documentation
│   ├── PYTHON_STANDARDS.md     # Python coding standards
│   ├── TYPESCRIPT_STANDARDS.md # TypeScript/React standards
│   ├── ARCHITECTURE.md         # System architecture
│   ├── MCP_SETUP.md           # Model Context Protocol setup
│   ├── RAG_CONSIDERATIONS.md  # RAG analysis and examples
│   └── PRE_COMMIT_HOOKS.md    # Pre-commit hooks guide
├── plans/                       # Implementation plans
│   ├── RAG_PLAN.md            # 4-week RAG implementation plan
│   └── PAYMENT_TRACKING_PLAN.md # 3-week payment features plan
├── skills/                      # Custom Claude Skills
│   ├── README.md               # Skills overview
│   ├── financial-analysis/     # Spending analysis skill
│   ├── payment-reminder/       # Smart reminders skill
│   ├── debt-management/        # Debt payoff strategies skill
│   └── savings-goal/           # Goal tracking skill
├── templates/                   # Code templates
│   ├── README.md               # Template usage guide
│   ├── python_service.py       # Service class template
│   ├── fastapi_router.py       # API router template
│   ├── react_component.tsx     # React component template
│   └── react_hook.ts           # Custom hook template
└── scripts/                     # Utility scripts
    ├── README.md               # Script documentation
    ├── setup_dev.sh            # Dev environment setup
    ├── run_tests.sh            # Test runner
    ├── db_reset.sh             # Database reset
    └── check_code_quality.sh   # Code quality checker
```

## 📚 Documentation

### [Python Coding Standards](docs/PYTHON_STANDARDS.md)
Complete Python development guide including:
- PEP 8 compliance (100 char line length)
- Type hints requirements
- Comprehensive docstring standards (Google style)
- **Agentic code standards** for AI/LLM integration
- Testing best practices (80%+ coverage)
- Error handling patterns
- Async/await patterns
- Database operations with SQLAlchemy 2.0
- **Redis caching patterns and best practices**
- Ruff and MyPy configuration

### [TypeScript/React Standards](docs/TYPESCRIPT_STANDARDS.md)
Frontend development guide covering:
- TypeScript strict mode
- React component patterns
- Naming conventions
- State management with React Query
- Error handling
- Testing with React Testing Library
- ESLint and Prettier setup

### [System Architecture](docs/ARCHITECTURE.md)
Comprehensive architecture documentation:
- 6-layer architecture breakdown
- Data flow examples
- Microservices migration path
- Security considerations
- Performance optimization
- Monitoring and observability

### [MCP Setup Guide](docs/MCP_SETUP.md)
Model Context Protocol configuration:
- Recommended MCPs (Database, Git, Brave Search)
- Configuration examples
- Custom MCP ideas
- Security best practices

### [Pre-commit Hooks](docs/PRE_COMMIT_HOOKS.md)
Automated code quality setup:
- Ruff linting and formatting
- MyPy type checking
- Prettier for frontend
- Secret detection
- Installation and usage

## 🤖 Claude Skills

Custom Claude Skills for Money Flow financial management are in the `skills/` directory. See [skills/README.md](skills/README.md) for full documentation.

### Available Skills

| Skill | Description |
|-------|-------------|
| **Financial Analysis** | Spending analysis, budget comparison, trend detection, anomaly alerts |
| **Payment Reminder** | Smart reminders with urgency classification, multi-channel support |
| **Debt Management** | Debt payoff strategies (avalanche/snowball), interest calculations |
| **Savings Goal** | Goal tracking, contribution recommendations, milestone celebrations |

### Using Skills

Skills contain:
- **SKILL.md** - Skill definition with XML patterns and response templates
- **Supporting files** - Examples, templates, and Python calculator modules

```python
# Example: Using debt management calculator
from .claude.skills.debt_management.calculators import calculate_payoff, Debt
from decimal import Decimal

debts = [Debt("1", "Credit Card", Decimal("3500"), Decimal("22.9"), Decimal("87"))]
result = calculate_payoff(debts, extra_payment=Decimal("100"))
print(f"Debt-free in {result.months_to_payoff} months")
```

## 🎨 Code Templates

All templates are located in the `templates/` directory with a comprehensive [README](templates/README.md).

### Python Templates
- **python_service.py**: Service class following repository pattern
- **fastapi_router.py**: REST API endpoints with FastAPI

### TypeScript/React Templates
- **react_component.tsx**: React functional component with TypeScript
- **react_hook.ts**: Custom React hook with proper typing

### Using Templates
1. Copy template to appropriate directory
2. Replace placeholders (e.g., `[ComponentName]`, `[ServiceName]`)
3. Update imports and dependencies
4. Customize implementation
5. Add tests

## 🛠️ Utility Scripts

All scripts are located in the `scripts/` directory. See [scripts/README.md](scripts/README.md) for details.

### Available Scripts

#### setup_dev.sh
Complete development environment setup.
```bash
bash .claude/scripts/setup_dev.sh
```

#### run_tests.sh
Run tests with coverage reporting.
```bash
# All tests with coverage
bash .claude/scripts/run_tests.sh

# Backend only
bash .claude/scripts/run_tests.sh backend

# Frontend without coverage
bash .claude/scripts/run_tests.sh frontend no
```

#### check_code_quality.sh
Comprehensive code quality checks.
```bash
bash .claude/scripts/check_code_quality.sh
```

#### db_reset.sh
Reset database (⚠️ WARNING: Deletes all data).
```bash
bash .claude/scripts/db_reset.sh
```

## 🚀 Quick Start

### First Time Setup
```bash
# 1. Run setup script
bash .claude/scripts/setup_dev.sh

# 2. Update .env with your configuration
# 3. Start Docker containers
docker-compose up --build

# 4. Access the application
# Frontend: http://localhost:3002
# Backend: http://localhost:8001
# API Docs: http://localhost:8001/docs
```

### Daily Development Workflow

```bash
# 1. Pull latest changes
git pull

# 2. Install/update dependencies if needed
pip install -e ".[dev]"
cd frontend && npm install

# 3. Start development servers (choose one)
# Option A: Docker
docker-compose up

# Option B: Local
uvicorn src.main:app --reload --port 8001
cd frontend && npm run dev

# 4. Before committing
bash .claude/scripts/check_code_quality.sh
bash .claude/scripts/run_tests.sh

# 5. Commit (pre-commit hooks will run automatically)
git add .
git commit -m "Your commit message"
```

## 📋 Code Quality Standards

### Python
- ✅ 100 character line length
- ✅ Google-style docstrings with Args, Returns, Raises, Example
- ✅ Type hints for all functions
- ✅ Async/await for I/O operations
- ✅ Ruff linting and formatting
- ✅ MyPy type checking
- ✅ 80%+ test coverage
- ✅ Agentic naming for AI/LLM code
- ✅ Redis caching with structured keys

### TypeScript/React
- ✅ Strict mode enabled
- ✅ PascalCase for components
- ✅ camelCase for functions/variables
- ✅ ESLint and Prettier enforced
- ✅ React Query for server state
- ✅ Comprehensive JSDoc comments

## 🔍 Finding Help

### Documentation
- General project info: [CLAUDE.md](../CLAUDE.md)
- Architecture details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Python standards: [docs/PYTHON_STANDARDS.md](docs/PYTHON_STANDARDS.md)
- TypeScript standards: [docs/TYPESCRIPT_STANDARDS.md](docs/TYPESCRIPT_STANDARDS.md)

### Common Tasks
- Create new service: Use `templates/python_service.py`
- Create new API endpoint: Use `templates/fastapi_router.py`
- Create React component: Use `templates/react_component.tsx`
- Create custom hook: Use `templates/react_hook.ts`
- Setup development: Run `scripts/setup_dev.sh`
- Run all tests: Run `scripts/run_tests.sh`
- Check code quality: Run `scripts/check_code_quality.sh`

### Troubleshooting
- Pre-commit hooks failing: Run `bash .claude/scripts/check_code_quality.sh` for details
- Tests failing: Run `bash .claude/scripts/run_tests.sh backend` or `frontend`
- Docker issues: Check Docker is running, try `docker-compose down && docker-compose up --build`
- Database issues: Run `bash .claude/scripts/db_reset.sh` (⚠️ deletes data)

## 🤖 MCP (Model Context Protocol)

Consider setting up these MCPs to enhance Claude Code:
- **PostgreSQL MCP**: Direct database access
- **Git MCP**: Repository operations
- **Brave Search MCP**: Web search capabilities

See [docs/MCP_SETUP.md](docs/MCP_SETUP.md) for setup instructions.

## 📝 Notes

- All scripts are made executable automatically
- Pre-commit hooks run automatically before commits
- Redis is optional but recommended for caching
- Refer to coding standards for agentic/AI code patterns
- Follow comprehensive docstring format for all functions

---

**Last Updated**: 2025-11-30
**Maintained By**: Development Team
