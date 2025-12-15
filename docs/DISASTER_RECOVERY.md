# Money Flow Disaster Recovery Guide

This document outlines procedures for backing up, restoring, and recovering the Money Flow application.

## Overview

Money Flow relies on the following data stores:
- **PostgreSQL**: Primary database (users, subscriptions, payment history)
- **Redis**: Cache and session data (non-critical, ephemeral)
- **Qdrant**: Vector embeddings for RAG (can be regenerated)

## Backup Strategy

### Database Backups

#### Automated Daily Backups (Recommended for Production)

Set up a cron job for daily backups:

```bash
# Add to crontab (crontab -e)
# Daily backup at 2 AM
0 2 * * * /path/to/subscription-tracker/scripts/backup_database.sh prod >> /var/log/moneyflow-backup.log 2>&1

# Weekly full backup on Sunday at 3 AM
0 3 * * 0 BACKUP_RETENTION_DAYS=90 /path/to/subscription-tracker/scripts/backup_database.sh prod >> /var/log/moneyflow-backup.log 2>&1
```

#### Manual Backup

```bash
# Development
./scripts/backup_database.sh dev

# Production
PGPASSWORD=your_password ./scripts/backup_database.sh prod
```

#### Backup Locations

| Environment | Location | Retention |
|-------------|----------|-----------|
| Development | `./backups/` | 7 days |
| Staging | `./backups/` | 14 days |
| Production | `./backups/` + Cloud Storage | 30 days + 1 year archive |

### What's Backed Up

| Data | Backed Up | Recovery Method |
|------|-----------|-----------------|
| Users | Yes | Database restore |
| Subscriptions | Yes | Database restore |
| Cards | Yes | Database restore |
| Payment History | Yes | Database restore |
| Conversations | Yes | Database restore |
| RAG Embeddings | No | Regenerated on restore |
| Redis Cache | No | Ephemeral, auto-rebuilds |
| User Sessions | No | Users re-login after restore |

## Restore Procedures

### Standard Restore

```bash
# Restore from latest backup
./scripts/restore_database.sh ./backups/moneyflow_dev_latest.sql.gz dev

# Restore from specific backup
./scripts/restore_database.sh ./backups/moneyflow_prod_20241215_020000.sql.gz prod
```

### Production Restore Checklist

1. **Before Restore**
   - [ ] Notify stakeholders of planned downtime
   - [ ] Scale down application replicas
   - [ ] Verify backup file integrity (checksum)
   - [ ] Test restore in staging first

2. **During Restore**
   - [ ] Run restore script with production credentials
   - [ ] Monitor restore progress
   - [ ] Run database migrations

3. **After Restore**
   - [ ] Verify data integrity
   - [ ] Clear Redis cache
   - [ ] Rebuild vector embeddings
   - [ ] Scale up application replicas
   - [ ] Verify application health
   - [ ] Notify stakeholders

### Rebuilding Vector Embeddings

After a database restore, RAG embeddings need regeneration:

```bash
# Connect to the backend container
docker-compose exec backend bash

# Run embedding rebuild script
python -c "
from src.services.rag_service import RAGService
from src.db.database import async_session_maker
import asyncio

async def rebuild():
    async with async_session_maker() as session:
        rag = RAGService()
        await rag.rebuild_all_embeddings(session)
        print('Embeddings rebuilt successfully')

asyncio.run(rebuild())
"
```

## Disaster Scenarios

### Scenario 1: Database Corruption

**Symptoms**: Application errors, data inconsistency, failed queries

**Recovery Steps**:
1. Stop the application
2. Identify last known good backup
3. Restore from backup
4. Run migrations
5. Rebuild embeddings
6. Restart application

```bash
# Stop services
docker-compose down

# Restore database
./scripts/restore_database.sh ./backups/moneyflow_prod_latest.sql.gz prod

# Start services
docker-compose up -d

# Verify health
curl http://localhost:8001/health/ready
```

### Scenario 2: Accidental Data Deletion

**Symptoms**: Missing records, user-reported data loss

**Recovery Steps**:
1. Identify the timeframe of deletion
2. Find backup before deletion occurred
3. Consider partial restore or point-in-time recovery
4. For recent deletions, check Redis cache first

```bash
# List available backups
ls -la ./backups/moneyflow_prod_*.sql.gz

# Restore to a temporary database for comparison
DB_NAME=moneyflow_recovery ./scripts/restore_database.sh ./backups/moneyflow_prod_20241214_020000.sql.gz dev

# Extract needed data and merge manually
```

### Scenario 3: Complete Infrastructure Failure

**Symptoms**: All services down, data center outage

**Recovery Steps**:
1. Provision new infrastructure (GCP Cloud Run)
2. Pull latest Docker images
3. Configure environment variables
4. Restore database from off-site backup
5. Deploy and verify

```bash
# Deploy to new region
gcloud config set run/region us-west1

# Deploy services
gcloud run deploy money-flow-backend --source .
gcloud run deploy money-flow-frontend --source ./frontend

# Restore database to Cloud SQL
gcloud sql import sql INSTANCE_NAME gs://bucket/backup.sql.gz --database=subscriptions
```

### Scenario 4: Redis Cache Failure

**Symptoms**: Slow responses, missing sessions, users logged out

**Recovery Steps**:
1. Application continues to work (cache is optional)
2. Fix or replace Redis instance
3. Cache rebuilds automatically on access

```bash
# Check Redis health
docker-compose logs redis

# Restart Redis if needed
docker-compose restart redis

# Flush corrupted cache
docker-compose exec redis redis-cli FLUSHALL
```

### Scenario 5: Qdrant Vector Database Failure

**Symptoms**: RAG features unavailable, semantic search errors

**Recovery Steps**:
1. Application continues to work (RAG is optional)
2. Fix or replace Qdrant instance
3. Rebuild embeddings from PostgreSQL data

```bash
# Check Qdrant health
curl http://localhost:6333/collections

# Restart Qdrant
docker-compose restart qdrant

# Rebuild embeddings
docker-compose exec backend python -c "..."  # See rebuilding section
```

## Recovery Time Objectives (RTO)

| Scenario | Target RTO | Actual RTO |
|----------|------------|------------|
| Single service restart | 1 minute | < 30 seconds |
| Database restore (small) | 15 minutes | ~5 minutes |
| Database restore (large) | 1 hour | ~30 minutes |
| Full infrastructure | 4 hours | ~2 hours |

## Recovery Point Objectives (RPO)

| Data Type | RPO | Backup Frequency |
|-----------|-----|------------------|
| User data | 24 hours | Daily |
| Subscriptions | 24 hours | Daily |
| Transactions | 24 hours | Daily |
| Cache | N/A | Not backed up |
| Embeddings | N/A | Regenerated |

## Testing Disaster Recovery

### Monthly DR Drill

1. Take a fresh backup
2. Provision a staging environment
3. Restore from backup
4. Verify all functionality
5. Document any issues
6. Update runbooks as needed

### Quarterly Full DR Test

1. Simulate complete failure
2. Execute full recovery procedure
3. Measure actual RTO/RPO
4. Review and improve procedures

## Monitoring and Alerts

### Backup Monitoring

```bash
# Check backup success
ls -la ./backups/moneyflow_prod_*.sql.gz | tail -1

# Check backup age (alert if > 25 hours)
find ./backups -name "moneyflow_prod_*.sql.gz" -mtime +1 | wc -l
```

### Health Check Alerts

Configure monitoring to alert on:
- `/health/ready` returning non-200
- Database connection failures
- Backup job failures
- Disk space running low

## Contact Information

| Role | Contact | Escalation |
|------|---------|------------|
| On-Call Engineer | Slack #on-call | PagerDuty |
| Database Admin | Slack #dba | Phone tree |
| Infrastructure | Slack #infra | PagerDuty |

## Appendix

### Environment Variables for Scripts

```bash
export DB_HOST=localhost
export DB_PORT=5433
export DB_NAME=subscriptions
export DB_USER=subscriptions
export PGPASSWORD=localdev
export BACKUP_DIR=./backups
export BACKUP_RETENTION_DAYS=30
```

### Cloud Storage Backup (GCP)

```bash
# Upload backup to Cloud Storage
gsutil cp ./backups/moneyflow_prod_latest.sql.gz gs://moneyflow-backups/

# Download backup from Cloud Storage
gsutil cp gs://moneyflow-backups/moneyflow_prod_20241215.sql.gz ./backups/
```

### Backup Encryption

For sensitive production data:

```bash
# Encrypt backup
gpg --symmetric --cipher-algo AES256 backup.sql.gz

# Decrypt backup
gpg --decrypt backup.sql.gz.gpg > backup.sql.gz
```
