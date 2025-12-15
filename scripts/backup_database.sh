#!/bin/bash
# Database Backup Script for Money Flow
#
# Usage:
#   ./scripts/backup_database.sh [environment]
#
# Arguments:
#   environment: dev|staging|prod (default: dev)
#
# Environment Variables:
#   DB_HOST: Database host (default: localhost)
#   DB_PORT: Database port (default: 5433)
#   DB_NAME: Database name (default: subscriptions)
#   DB_USER: Database user (default: subscriptions)
#   PGPASSWORD: Database password
#   BACKUP_DIR: Backup directory (default: ./backups)
#   BACKUP_RETENTION_DAYS: Days to keep backups (default: 30)
#
# Examples:
#   ./scripts/backup_database.sh dev
#   BACKUP_DIR=/mnt/backups ./scripts/backup_database.sh prod

set -euo pipefail

# Configuration
ENV="${1:-dev}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_NAME="${DB_NAME:-subscriptions}"
DB_USER="${DB_USER:-subscriptions}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

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

# Generate timestamp
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILENAME="moneyflow_${ENV}_${TIMESTAMP}.sql.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

log_info "Starting database backup..."
log_info "Environment: ${ENV}"
log_info "Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
log_info "Backup file: ${BACKUP_PATH}"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Check if pg_dump is available
if ! command -v pg_dump &> /dev/null; then
    log_error "pg_dump not found. Please install PostgreSQL client tools."
    exit 1
fi

# Check database connectivity
log_info "Checking database connectivity..."
if ! pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" &> /dev/null; then
    log_error "Cannot connect to database. Check your credentials and network."
    exit 1
fi

# Perform backup with compression
log_info "Creating backup (this may take a while for large databases)..."

pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --format=custom \
    --compress=9 \
    --verbose \
    --no-owner \
    --no-privileges \
    --exclude-table-data='alembic_version' \
    2>&1 | gzip > "${BACKUP_PATH}"

# Verify backup was created
if [ -f "${BACKUP_PATH}" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_PATH}" | cut -f1)
    log_info "Backup created successfully!"
    log_info "Backup size: ${BACKUP_SIZE}"
else
    log_error "Backup file was not created!"
    exit 1
fi

# Create a checksum for integrity verification
log_info "Creating checksum..."
shasum -a 256 "${BACKUP_PATH}" > "${BACKUP_PATH}.sha256"

# Create latest symlink
LATEST_LINK="${BACKUP_DIR}/moneyflow_${ENV}_latest.sql.gz"
ln -sf "${BACKUP_FILENAME}" "${LATEST_LINK}"
log_info "Updated latest symlink: ${LATEST_LINK}"

# Clean up old backups
log_info "Cleaning up backups older than ${BACKUP_RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "moneyflow_${ENV}_*.sql.gz" -mtime "+${BACKUP_RETENTION_DAYS}" -delete 2>/dev/null || true
find "${BACKUP_DIR}" -name "moneyflow_${ENV}_*.sql.gz.sha256" -mtime "+${BACKUP_RETENTION_DAYS}" -delete 2>/dev/null || true

# List recent backups
log_info "Recent backups:"
ls -lh "${BACKUP_DIR}"/moneyflow_${ENV}_*.sql.gz 2>/dev/null | tail -5 || log_warn "No backups found"

# Summary
log_info "=== Backup Summary ==="
log_info "Environment: ${ENV}"
log_info "Backup file: ${BACKUP_PATH}"
log_info "Backup size: ${BACKUP_SIZE}"
log_info "Checksum: ${BACKUP_PATH}.sha256"
log_info "Backup completed successfully!"
