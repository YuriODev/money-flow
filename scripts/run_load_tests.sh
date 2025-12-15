#!/bin/bash
# Run Load Tests for Money Flow API
# Sprint 2.4: Performance & Load Testing
#
# Usage:
#   ./scripts/run_load_tests.sh [mode]
#
# Modes:
#   quick   - Quick test (10 users, 30s)
#   medium  - Medium test (50 users, 5m)
#   full    - Full test (100 users, 10m)
#   web     - Start Locust web UI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOCUST_FILE="$PROJECT_DIR/tests/load/locustfile.py"
REPORTS_DIR="$PROJECT_DIR/reports"
HOST="${HOST:-http://localhost:8001}"

# Create reports directory
mkdir -p "$REPORTS_DIR"

# Get timestamp for report naming
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Ensure locust is available
if ! command -v locust &> /dev/null; then
    echo "Installing locust..."
    pip install locust
fi

run_quick() {
    echo "🚀 Running quick load test (10 users, 30 seconds)..."
    locust -f "$LOCUST_FILE" \
        --host="$HOST" \
        --headless \
        -u 10 \
        -r 2 \
        -t 30s \
        --html="$REPORTS_DIR/load_test_quick_${TIMESTAMP}.html" \
        --csv="$REPORTS_DIR/load_test_quick_${TIMESTAMP}"
    echo "✅ Quick test complete. Report: $REPORTS_DIR/load_test_quick_${TIMESTAMP}.html"
}

run_medium() {
    echo "🚀 Running medium load test (50 users, 5 minutes)..."
    locust -f "$LOCUST_FILE" \
        --host="$HOST" \
        --headless \
        -u 50 \
        -r 5 \
        -t 5m \
        --html="$REPORTS_DIR/load_test_medium_${TIMESTAMP}.html" \
        --csv="$REPORTS_DIR/load_test_medium_${TIMESTAMP}"
    echo "✅ Medium test complete. Report: $REPORTS_DIR/load_test_medium_${TIMESTAMP}.html"
}

run_full() {
    echo "🚀 Running full load test (100 users, 10 minutes)..."
    locust -f "$LOCUST_FILE" \
        --host="$HOST" \
        --headless \
        -u 100 \
        -r 10 \
        -t 10m \
        --html="$REPORTS_DIR/load_test_full_${TIMESTAMP}.html" \
        --csv="$REPORTS_DIR/load_test_full_${TIMESTAMP}"
    echo "✅ Full test complete. Report: $REPORTS_DIR/load_test_full_${TIMESTAMP}.html"
}

run_web() {
    echo "🌐 Starting Locust web UI at http://localhost:8089..."
    echo "   Target host: $HOST"
    echo "   Press Ctrl+C to stop"
    locust -f "$LOCUST_FILE" --host="$HOST"
}

print_usage() {
    echo "Usage: $0 [mode]"
    echo ""
    echo "Modes:"
    echo "  quick   - Quick test (10 users, 30s)"
    echo "  medium  - Medium test (50 users, 5m)"
    echo "  full    - Full test (100 users, 10m)"
    echo "  web     - Start Locust web UI"
    echo ""
    echo "Environment variables:"
    echo "  HOST    - Target host (default: http://localhost:8001)"
    echo ""
    echo "Examples:"
    echo "  $0 quick"
    echo "  HOST=https://api.example.com $0 medium"
}

# Main
case "${1:-web}" in
    quick)
        run_quick
        ;;
    medium)
        run_medium
        ;;
    full)
        run_full
        ;;
    web)
        run_web
        ;;
    -h|--help|help)
        print_usage
        ;;
    *)
        echo "Unknown mode: $1"
        print_usage
        exit 1
        ;;
esac
