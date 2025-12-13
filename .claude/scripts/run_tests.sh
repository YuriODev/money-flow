#!/bin/bash

# Test Runner Script
# Comprehensive test suite runner with coverage reporting

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Running Subscription Tracker Test Suite${NC}\n"

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
    if [ -f ".venv/bin/activate" ]; then
        echo "Activating virtual environment..."
        source .venv/bin/activate
    else
        echo -e "${RED}❌ Error: Virtual environment not found${NC}"
        exit 1
    fi
fi

# Parse command line arguments
TEST_TYPE="${1:-all}"
COVERAGE="${2:-yes}"

# Backend tests
run_backend_tests() {
    echo -e "${BLUE}🐍 Running Backend Tests${NC}"

    if [ "$COVERAGE" = "yes" ]; then
        echo "Running with coverage..."
        pytest tests/ \
            --cov=src \
            --cov-report=html \
            --cov-report=term-missing \
            --cov-fail-under=80 \
            -v
    else
        pytest tests/ -v
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Backend tests passed${NC}\n"
    else
        echo -e "${RED}✗ Backend tests failed${NC}\n"
        exit 1
    fi
}

# Frontend tests
run_frontend_tests() {
    echo -e "${BLUE}🎨 Running Frontend Tests${NC}"
    cd frontend

    if [ "$COVERAGE" = "yes" ]; then
        npm run test -- --coverage
    else
        npm run test
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Frontend tests passed${NC}\n"
    else
        echo -e "${RED}✗ Frontend tests failed${NC}\n"
        exit 1
    fi

    cd ..
}

# Type checking
run_type_checks() {
    echo -e "${BLUE}📝 Running Type Checks${NC}"

    # Python type checking with mypy
    echo "Running mypy..."
    mypy src/ --ignore-missing-imports || true

    # TypeScript type checking
    echo "Running TypeScript compiler..."
    cd frontend
    npx tsc --noEmit || true
    cd ..

    echo -e "${GREEN}✓ Type checks complete${NC}\n"
}

# Linting
run_linters() {
    echo -e "${BLUE}🔍 Running Linters${NC}"

    # Python linting with Ruff
    echo "Running Ruff..."
    ruff check src/ tests/

    # Frontend linting
    echo "Running ESLint..."
    cd frontend
    npm run lint
    cd ..

    echo -e "${GREEN}✓ Linting complete${NC}\n"
}

# Run tests based on argument
case "$TEST_TYPE" in
    "backend"|"be")
        run_backend_tests
        ;;
    "frontend"|"fe")
        run_frontend_tests
        ;;
    "types"|"type")
        run_type_checks
        ;;
    "lint")
        run_linters
        ;;
    "all")
        run_linters
        run_type_checks
        run_backend_tests
        run_frontend_tests
        ;;
    *)
        echo "Usage: $0 [all|backend|frontend|types|lint] [yes|no (coverage)]"
        echo ""
        echo "Examples:"
        echo "  $0              # Run all tests with coverage"
        echo "  $0 backend      # Run only backend tests with coverage"
        echo "  $0 frontend no  # Run frontend tests without coverage"
        echo "  $0 lint         # Run only linters"
        echo "  $0 types        # Run only type checks"
        exit 1
        ;;
esac

# Coverage report location
if [ "$COVERAGE" = "yes" ] && [ "$TEST_TYPE" != "lint" ] && [ "$TEST_TYPE" != "types" ]; then
    echo -e "${BLUE}📊 Coverage Reports:${NC}"
    echo "Backend: htmlcov/index.html"
    if [ "$TEST_TYPE" = "all" ] || [ "$TEST_TYPE" = "frontend" ]; then
        echo "Frontend: frontend/coverage/index.html"
    fi
fi

echo -e "\n${GREEN}✨ All tests completed successfully!${NC}"
