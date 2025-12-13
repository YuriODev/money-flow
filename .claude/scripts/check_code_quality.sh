#!/bin/bash

# Code Quality Checker
# Runs all code quality tools: linting, formatting, type checking, security checks

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Running Code Quality Checks${NC}\n"

ERRORS=0

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Activating virtual environment...${NC}"
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        echo -e "${RED}❌ Error: Virtual environment not found${NC}"
        exit 1
    fi
fi

# 1. Python - Ruff linting
echo -e "${BLUE}1️⃣  Running Ruff (Python linter)...${NC}"
if ruff check src/ tests/; then
    echo -e "${GREEN}✓ Ruff check passed${NC}\n"
else
    echo -e "${RED}✗ Ruff found issues${NC}\n"
    ((ERRORS++))
fi

# 2. Python - Ruff formatting check
echo -e "${BLUE}2️⃣  Checking Python formatting (Ruff)...${NC}"
if ruff format --check src/ tests/; then
    echo -e "${GREEN}✓ Python formatting correct${NC}\n"
else
    echo -e "${RED}✗ Python formatting issues found${NC}"
    echo -e "${YELLOW}Run: ruff format src/ tests/${NC}\n"
    ((ERRORS++))
fi

# 3. Python - Type checking with mypy
echo -e "${BLUE}3️⃣  Running mypy (Python type checker)...${NC}"
if mypy src/ --ignore-missing-imports; then
    echo -e "${GREEN}✓ Type checking passed${NC}\n"
else
    echo -e "${RED}✗ Type errors found${NC}\n"
    ((ERRORS++))
fi

# 4. Python - Security check with bandit
echo -e "${BLUE}4️⃣  Running bandit (Security linter)...${NC}"
if command -v bandit &> /dev/null; then
    if bandit -r src/ -ll; then
        echo -e "${GREEN}✓ No security issues found${NC}\n"
    else
        echo -e "${YELLOW}⚠️  Security issues detected${NC}\n"
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠️  bandit not installed (pip install bandit)${NC}\n"
fi

# 5. Frontend - ESLint
echo -e "${BLUE}5️⃣  Running ESLint (TypeScript/React)...${NC}"
cd frontend
if npm run lint; then
    echo -e "${GREEN}✓ ESLint check passed${NC}\n"
else
    echo -e "${RED}✗ ESLint found issues${NC}\n"
    ((ERRORS++))
fi

# 6. Frontend - Prettier check
echo -e "${BLUE}6️⃣  Checking frontend formatting (Prettier)...${NC}"
if npx prettier --check "src/**/*.{ts,tsx,js,jsx,json,css,md}"; then
    echo -e "${GREEN}✓ Frontend formatting correct${NC}\n"
else
    echo -e "${RED}✗ Frontend formatting issues found${NC}"
    echo -e "${YELLOW}Run: npm run format${NC}\n"
    ((ERRORS++))
fi

# 7. Frontend - TypeScript compiler
echo -e "${BLUE}7️⃣  Running TypeScript compiler...${NC}"
if npx tsc --noEmit; then
    echo -e "${GREEN}✓ TypeScript compilation successful${NC}\n"
else
    echo -e "${RED}✗ TypeScript errors found${NC}\n"
    ((ERRORS++))
fi

cd ..

# 8. Check for secrets
echo -e "${BLUE}8️⃣  Checking for secrets...${NC}"
if command -v detect-secrets &> /dev/null; then
    if detect-secrets scan --baseline .secrets.baseline; then
        echo -e "${GREEN}✓ No new secrets detected${NC}\n"
    else
        echo -e "${RED}✗ Potential secrets found${NC}\n"
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠️  detect-secrets not installed${NC}\n"
fi

# 9. Check for large files
echo -e "${BLUE}9️⃣  Checking for large files...${NC}"
LARGE_FILES=$(find . -type f -size +1M -not -path "./node_modules/*" -not -path "./.venv/*" -not -path "./.git/*" -not -path "./frontend/node_modules/*" 2>/dev/null || true)
if [ -z "$LARGE_FILES" ]; then
    echo -e "${GREEN}✓ No large files found${NC}\n"
else
    echo -e "${YELLOW}⚠️  Large files detected:${NC}"
    echo "$LARGE_FILES"
    echo ""
fi

# 10. Check for TODO/FIXME comments
echo -e "${BLUE}🔟 Checking for TODO/FIXME comments...${NC}"
TODO_COUNT=$(grep -r "TODO\|FIXME" src/ frontend/src/ 2>/dev/null | wc -l || echo "0")
if [ "$TODO_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✓ No TODO/FIXME comments${NC}\n"
else
    echo -e "${YELLOW}⚠️  Found $TODO_COUNT TODO/FIXME comments${NC}\n"
fi

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✨ All code quality checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Found $ERRORS issues${NC}"
    echo -e "${YELLOW}Please fix the issues above before committing${NC}"
    exit 1
fi
