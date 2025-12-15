#!/bin/bash
# Database Restore Script for Money Flow
#
# Usage:
#   ./scripts/restore_database.sh <backup_file> [environment]
#
# Arguments:
#   backup_file: Path to the backup file (.sql.gz)
#   environment: dev|staging|prod (default: dev)
#
# Environment Variables:
#   DB_HOST: Database host (default: localhost)
#   DB_PORT: Database port (default: 5433)
#   DB_NAME: Database name (default: subscriptions)
#   DB_USER: Database user (default: subscriptions)
#   PGPASSWORD: Database password
#
# Examples:
#   ./scripts/restore_database.sh ./backups/moneyflow_dev_20241215_120000.sql.gz
#   ./scripts/restore_database.sh ./backups/moneyflow_prod_latest.sql.gz prod
#
# WARNING: This will DROP and RECREATE the database!

set -euo pipefail

# Configuration
BACKUP_FILE="${1:-}"
ENV="${2:-dev}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_NAME="${DB_NAME:-subscriptions}"
DB_USER="${DB_USER:-subscriptions}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Check arguments
if [ -z "${BACKUP_FILE}" ]; then
    log_error "Usage: $0 <backup_file> [environment]"
    log_error "Example: $0 ./backups/moneyflow_dev_latest.sql.gz dev"
    exit 1
fi

# Resolve symlinks
if [ -L "${BACKUP_FILE}" ]; then
    BACKUP_FILE=$(readlink -f "${BACKUP_FILE}")
    log_info "Resolved symlink to: ${BACKUP_FILE}"
fi

# Check if backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    log_error "Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# Verify checksum if available
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
if [ -f "${CHECKSUM_FILE}" ]; then
    log_info "Verifying backup integrity..."
    if shasum -a 256 -c "${CHECKSUM_FILE}" &> /dev/null; then
        log_info "Checksum verification passed"
    else
        log_error "Checksum verification FAILED! Backup may be corrupted."
        exit 1
    fi
else
    log_warn "No checksum file found, skipping integrity check"
fi

# Check if pg_restore is available
if ! command -v pg_restore &> /dev/null; then
    log_error "pg_restore not found. Please install PostgreSQL client tools."
    exit 1
fi

# Safety confirmation for production
if [ "${ENV}" = "prod" ] || [ "${ENV}" = "production" ]; then
    log_warn "=========================================="
    log_warn "  WARNING: PRODUCTION RESTORE REQUESTED  "
    log_warn "=========================================="
    log_warn "This will DROP and RECREATE the ${DB_NAME} database!"
    log_warn "All existing data will be LOST!"
    echo ""
    read -p "Type 'YES-DESTROY-PROD-DATA' to confirm: " CONFIRM
    if [ "${CONFIRM}" != "YES-DESTROY-PROD-DATA" ]; then
        log_info "Restore cancelled"
        exit 0
    fi
else
    log_warn "This will DROP and RECREATE the ${DB_NAME} database!"
    read -p "Continue? (y/N): " CONFIRM
    if [ "${CONFIRM}" != "y" ] && [ "${CONFIRM}" != "Y" ]; then
        log_info "Restore cancelled"
        exit 0
    fi
fi

log_info "Starting database restore..."
log_info "Environment: ${ENV}"
log_info "Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
log_info "Backup file: ${BACKUP_FILE}"

# Check database connectivity (using postgres database)
log_info "Checking database connectivity..."
if ! pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres &> /dev/null; then
    log_error "Cannot connect to database server. Check your credentials and network."
    exit 1
fi

# Terminate existing connections
log_info "Terminating existing connections to ${DB_NAME}..."
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" \
    2>/dev/null || true

# Drop and recreate database
log_info "Dropping existing database..."
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c \
    "DROP DATABASE IF EXISTS ${DB_NAME};" 2>/dev/null

log_info "Creating new database..."
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c \
    "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" 2>/dev/null

# Restore from backup
log_info "Restoring from backup (this may take a while for large databases)..."
gunzip -c "${BACKUP_FILE}" | pg_restore \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --no-owner \
    --no-privileges \
    --verbose \
    2>&1 | grep -v "^pg_restore: " || true

# Verify restore
log_info "Verifying restore..."
TABLE_COUNT=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -t -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
TABLE_COUNT=$(echo "${TABLE_COUNT}" | tr -d ' ')

if [ "${TABLE_COUNT}" -gt 0 ]; then
    log_info "Found ${TABLE_COUNT} tables in restored database"
else
    log_warn "No tables found after restore - database may be empty"
fi

# Run migrations to ensure schema is up to date
log_info "Running database migrations..."
if [ -f "alembic.ini" ]; then
    DATABASE_URL="postgresql+asyncpg://${DB_USER}:${PGPASSWORD:-localdev}@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
        alembic upgrade head 2>&1 || log_warn "Migration failed or not needed"
else
    log_warn "alembic.ini not found, skipping migrations"
fi

# Summary
log_info "=== Restore Summary ==="
log_info "Environment: ${ENV}"
log_info "Backup file: ${BACKUP_FILE}"
log_info "Database: ${DB_NAME}"
log_info "Tables: ${TABLE_COUNT}"
log_info "Restore completed successfully!"
