# Pre-Commit Hooks Configuration

## Overview

Pre-commit hooks automatically check code quality before allowing commits. This ensures consistent code style and catches issues early.

## Setup

### 1. Install Pre-Commit

Already in `pyproject.toml` dependencies:

```bash
# Activate virtual environment
source .venv/bin/activate.fish

# Install if not already installed
pip install pre-commit

# Install the git hook scripts
pre-commit install
```

### 2. Configuration File

Create `.pre-commit-config.yaml` in project root:

```yaml
# .pre-commit-config.yaml
repos:
  # Python: Ruff linting and formatting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.7.4
    hooks:
      # Run the linter
      - id: ruff
        args: [--fix]
      # Run the formatter
      - id: ruff-format

  # Python: Type checking with mypy
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.14.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict, --ignore-missing-imports]

  # General: File checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-toml
      - id: check-added-large-files
        args: [--maxkb=1000]
      - id: check-merge-conflict
      - id: detect-private-key

  # Frontend: ESLint and Prettier
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        files: \.(ts|tsx|js|jsx|json|css|md)$
        exclude: ^(frontend/node_modules/|.next/)

  # Frontend: TypeScript checking
  - repo: local
    hooks:
      - id: typescript-check
        name: TypeScript Check
        entry: bash -c 'cd frontend && npm run type-check'
        language: system
        files: \.(ts|tsx)$
        pass_filenames: false

  # Security: Check for secrets
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: [--baseline, .secrets.baseline]

  # Commit message format
  - repo: https://github.com/commitizen-tools/commitizen
    rev: v4.3.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
```

### 3. Frontend Package.json Scripts

Add to `frontend/package.json`:

```json
{
  "scripts": {
    "type-check": "tsc --noEmit",
    "lint": "next lint",
    "lint:fix": "next lint --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,js,jsx,json,css,md}\""
  }
}
```

### 4. Initialize Secrets Baseline

```bash
# Create baseline for secret detection
detect-secrets scan > .secrets.baseline
```

## Usage

### Automatic (Recommended)

Once installed, hooks run automatically on `git commit`:

```bash
git add src/services/currency_service.py
git commit -m "feat: add currency conversion service"

# Pre-commit hooks will run:
# ✓ Ruff linting
# ✓ Ruff formatting
# ✓ MyPy type checking
# ✓ File checks
# ✓ Prettier formatting
# ✓ TypeScript checking
# ✓ Secret detection
```

### Manual Run

```bash
# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run mypy --all-files

# Skip hooks (not recommended)
git commit --no-verify -m "Emergency fix"
```

### Update Hooks

```bash
# Update to latest versions
pre-commit autoupdate
```

## Hook Descriptions

### Ruff (Python)

**Purpose**: Lint and format Python code

**What it checks**:
- PEP 8 compliance
- Import sorting
- Code style issues
- Security issues
- Bug patterns

**Auto-fixes**:
- Import ordering
- Whitespace issues
- Quote consistency
- Line length

### MyPy (Python)

**Purpose**: Static type checking

**What it checks**:
- Type hint correctness
- Type compatibility
- Missing annotations
- Invalid operations

**Does not auto-fix** - requires manual correction

### Prettier (Frontend)

**Purpose**: Format TypeScript/JavaScript/CSS

**What it fixes**:
- Code formatting
- Indentation
- Quote style
- Trailing commas
- Line breaks

### TypeScript Check (Frontend)

**Purpose**: Type checking without emitting files

**What it checks**:
- TypeScript errors
- Type mismatches
- Missing types

### Secret Detection

**Purpose**: Prevent committing sensitive data

**What it detects**:
- API keys
- Passwords
- Private keys
- Tokens
- AWS keys

## Customization

### Skip Specific Files

Add to `.pre-commit-config.yaml`:

```yaml
- id: ruff
  exclude: ^(tests/|migrations/)
```

### Skip Specific Hooks for a Commit

```bash
# Skip only prettier
SKIP=prettier git commit -m "docs: update README"

# Skip multiple hooks
SKIP=ruff,mypy git commit -m "WIP: refactoring"
```

### Add Custom Hook

```yaml
- repo: local
  hooks:
    - id: check-subscription-schema
      name: Validate Subscription Schema
      entry: python scripts/validate_schema.py
      language: system
      files: src/schemas/subscription.py
```

## Continuous Integration

### GitHub Actions

Create `.github/workflows/pre-commit.yml`:

```yaml
name: Pre-commit Checks

on: [push, pull_request]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: pre-commit/action@v3.0.0
```

## Common Issues

### Hook Fails on Every Commit

```bash
# Clear pre-commit cache
pre-commit clean

# Reinstall hooks
pre-commit install --install-hooks
```

### MyPy Fails with Import Errors

Add to `pyproject.toml`:

```toml
[tool.mypy]
ignore_missing_imports = true
```

### Prettier Conflicts with ESLint

Install prettier-eslint:

```bash
cd frontend
npm install --save-dev prettier-eslint eslint-config-prettier
```

## Performance

### Slow Hooks

```bash
# Run hooks in parallel (default)
pre-commit run --all-files

# Skip slow hooks locally
SKIP=mypy git commit -m "Quick fix"

# But run in CI (always)
```

### Cache Management

```bash
# Clear all caches
pre-commit clean

# Remove unused hook repos
pre-commit gc
```

## Recommended Workflow

1. **Make changes** to code
2. **Run linters manually** (optional):
   ```bash
   ruff check src/
   cd frontend && npm run lint
   ```
3. **Stage changes**: `git add .`
4. **Commit**: `git commit -m "feat: add feature"`
5. **Hooks run automatically**
6. **Fix any issues** if hooks fail
7. **Commit again** if changes were made

## Benefits

✅ **Consistent Code Style**: All code follows same standards
✅ **Early Bug Detection**: Catch issues before they reach production
✅ **No Manual Linting**: Automatic on every commit
✅ **Team Alignment**: Everyone uses same tools
✅ **CI/CD Ready**: Same checks in pre-commit and CI

---

**Last Updated**: 2025-11-28
**Next**: Run `pre-commit install` to enable hooks
