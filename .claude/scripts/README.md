# Utility Scripts

This directory contains utility scripts for common development tasks.

## Available Scripts

### `setup_dev.sh`
Complete development environment setup script.

**Usage:**
```bash
bash .claude/scripts/setup_dev.sh
```

**What it does:**
1. Checks Python version (3.11+ recommended)
2. Creates Python virtual environment
3. Installs backend dependencies
4. Installs frontend dependencies
5. Sets up pre-commit hooks
6. Creates .env from .env.example if needed
7. Initializes secrets baseline
8. Checks Docker installation

**When to use:**
- First time setting up the project
- After cloning the repository
- Resetting development environment

---

### `run_tests.sh`
Comprehensive test runner with coverage reporting.

**Usage:**
```bash
# Run all tests with coverage
bash .claude/scripts/run_tests.sh

# Run only backend tests
bash .claude/scripts/run_tests.sh backend

# Run frontend tests without coverage
bash .claude/scripts/run_tests.sh frontend no

# Run only linters
bash .claude/scripts/run_tests.sh lint

# Run only type checks
bash .claude/scripts/run_tests.sh types
```

**Options:**
- `all` (default) - Run all tests and checks
- `backend` or `be` - Backend Python tests only
- `frontend` or `fe` - Frontend React tests only
- `types` or `type` - Type checking only
- `lint` - Linting only

**Coverage argument:**
- `yes` (default) - Generate coverage reports
- `no` - Skip coverage reporting

**Output:**
- Backend coverage: `htmlcov/index.html`
- Frontend coverage: `frontend/coverage/index.html`

---

### `check_code_quality.sh`
Runs all code quality tools without fixing issues.

**Usage:**
```bash
bash .claude/scripts/check_code_quality.sh
```

**Checks performed:**
1. Ruff linting (Python)
2. Ruff formatting check (Python)
3. MyPy type checking (Python)
4. Bandit security scan (Python)
5. ESLint (TypeScript/React)
6. Prettier formatting check (Frontend)
7. TypeScript compiler
8. Secret detection
9. Large file detection
10. TODO/FIXME comment count

**Exit codes:**
- `0` - All checks passed
- `1` - One or more checks failed

**When to use:**
- Before committing code
- In CI/CD pipeline
- Code review preparation

---

### `db_reset.sh`
Database reset and migration script.

**⚠️ WARNING:** This script will delete all data!

**Usage:**
```bash
bash .claude/scripts/db_reset.sh
```

**What it does:**
1. Confirms action (requires typing "yes")
2. Detects Docker or local environment
3. Drops all database tables
4. Runs migrations from scratch
5. Optionally loads sample data

**When to use:**
- Development database corruption
- Testing migrations
- Starting fresh with schema changes
- NOT for production!

---

## Making Scripts Executable

To make scripts executable without `bash` prefix:

```bash
chmod +x .claude/scripts/*.sh

# Then run directly:
./.claude/scripts/setup_dev.sh
./.claude/scripts/run_tests.sh
```

## Script Conventions

### Exit Codes
- `0` - Success
- `1` - General error
- Other - Specific error codes

### Colors
Scripts use ANSI color codes for better readability:
- 🔵 Blue - Informational messages
- 🟢 Green - Success messages
- 🟡 Yellow - Warnings
- 🔴 Red - Errors

### Error Handling
All scripts use `set -e` to exit on first error, ensuring reliability.

## Integration with Pre-commit

These scripts complement pre-commit hooks:
- Pre-commit: Automatic checks before commit
- These scripts: Manual comprehensive checks

Run `check_code_quality.sh` for the same checks as pre-commit but with detailed output.

## CI/CD Integration

These scripts are designed to work in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Setup environment
  run: bash .claude/scripts/setup_dev.sh

- name: Run tests
  run: bash .claude/scripts/run_tests.sh all

- name: Check code quality
  run: bash .claude/scripts/check_code_quality.sh
```

## Troubleshooting

### Virtual environment not found
```bash
# Recreate virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Permission denied
```bash
chmod +x .claude/scripts/*.sh
```

### Docker issues
```bash
# Check Docker is running
docker ps

# Restart Docker daemon
# (varies by OS)
```

## Related Documentation

- [Python Standards](../docs/PYTHON_STANDARDS.md)
- [TypeScript Standards](../docs/TYPESCRIPT_STANDARDS.md)
- [Pre-commit Hooks](../docs/PRE_COMMIT_HOOKS.md)
- [Architecture](../docs/ARCHITECTURE.md)
