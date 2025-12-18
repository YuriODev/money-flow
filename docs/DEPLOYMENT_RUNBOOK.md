# Money Flow - Deployment Runbook

> Step-by-step procedures for deploying, updating, and maintaining the Money Flow application

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Overview](#environment-overview)
3. [Initial Deployment](#initial-deployment)
4. [Standard Deployment](#standard-deployment)
5. [Rollback Procedures](#rollback-procedures)
6. [Database Migrations](#database-migrations)
7. [Configuration Management](#configuration-management)
8. [Health Checks](#health-checks)
9. [Monitoring Setup](#monitoring-setup)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Multi-container orchestration |
| Git | 2.40+ | Version control |
| gcloud CLI | Latest | GCP deployment (production) |
| gh CLI | Latest | GitHub operations |

### Access Requirements

- [ ] GitHub repository access (read/write)
- [ ] Docker registry access (GHCR)
- [ ] GCP project access (for production)
- [ ] Database credentials
- [ ] API keys (Anthropic, Telegram)

### Environment Variables Checklist

```bash
# Required for all environments
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
SECRET_KEY=<32+ character secret>
ANTHROPIC_API_KEY=sk-ant-...

# Required for Telegram notifications
TELEGRAM_BOT_TOKEN=<bot token from BotFather>

# Required for production
GCP_PROJECT_ID=your-project
GCP_REGION=us-central1
SENTRY_DSN=https://...@sentry.io/...

# Optional
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333
```

---

## Environment Overview

### Development (Local)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│  PostgreSQL │
│   :3001     │     │    :8001    │     │    :5433    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              ┌─────────┐   ┌─────────┐
              │  Redis  │   │ Qdrant  │
              │  :6379  │   │  :6333  │
              └─────────┘   └─────────┘
```

### Staging

- URL: https://staging.moneyflow.app
- Branch: `main` (auto-deploy)
- Database: Cloud SQL (staging instance)

### Production

- URL: https://moneyflow.app
- Branch: Release tags (`v*`)
- Database: Cloud SQL (production instance)

---

## Initial Deployment

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/subscription-tracker.git
cd subscription-tracker
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your values
vim .env
```

**Required variables:**

```bash
# Database
DATABASE_URL=postgresql+asyncpg://subscriptions:localdev@localhost:5433/subscriptions

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# AI
ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional: Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
```

### Step 3: Start Services

```bash
# Build and start all services
docker-compose up --build -d

# Verify all containers are running
docker-compose ps
```

Expected output:
```
NAME                    STATUS              PORTS
subscription-backend    Up                  0.0.0.0:8001->8000/tcp
subscription-frontend   Up                  0.0.0.0:3001->3000/tcp
subscription-db         Up (healthy)        0.0.0.0:5433->5432/tcp
subscription-redis      Up (healthy)        0.0.0.0:6379->6379/tcp
subscription-qdrant     Up                  0.0.0.0:6333->6333/tcp
```

### Step 4: Run Database Migrations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Verify migrations
docker-compose exec backend alembic current
```

### Step 5: Verify Deployment

```bash
# Health check
curl http://localhost:8001/health/ready

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "qdrant": "connected"
}
```

### Step 6: Access Application

- Frontend: http://localhost:3001
- API Docs: http://localhost:8001/docs
- Health: http://localhost:8001/health

---

## Standard Deployment

### Automated (CI/CD)

Deployments are triggered automatically:

| Trigger | Environment | Action |
|---------|-------------|--------|
| Push to `main` | Staging | Auto-deploy |
| Create release tag | Production | Auto-deploy |
| Manual dispatch | Any | Manual trigger |

### Manual Deployment

#### Backend Deployment

```bash
# 1. Pull latest code
git pull origin main

# 2. Build new image
docker-compose build backend

# 3. Stop old container
docker-compose stop backend

# 4. Run migrations (if any)
docker-compose run --rm backend alembic upgrade head

# 5. Start new container
docker-compose up -d backend

# 6. Verify health
curl http://localhost:8001/health/ready
```

#### Frontend Deployment

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild and restart
docker-compose up --build -d frontend

# 3. Verify
curl http://localhost:3001
```

#### Full Stack Deployment

```bash
# 1. Pull latest code
git pull origin main

# 2. Stop all services
docker-compose down

# 3. Rebuild all
docker-compose build

# 4. Start services
docker-compose up -d

# 5. Run migrations
docker-compose exec backend alembic upgrade head

# 6. Verify all services
docker-compose ps
curl http://localhost:8001/health/ready
```

---

## Rollback Procedures

### Quick Rollback (Same Image)

```bash
# 1. Restart with previous running state
docker-compose down
docker-compose up -d

# 2. Skip migrations if they caused issues
```

### Image Rollback

```bash
# 1. List available images
docker images | grep subscription

# 2. Update docker-compose.yml to use specific tag
# image: ghcr.io/your-org/subscription-backend:v1.2.3

# 3. Restart with old image
docker-compose up -d backend
```

### Git Rollback

```bash
# 1. Identify last good commit
git log --oneline -10

# 2. Revert to that commit
git checkout <commit-hash>

# 3. Rebuild and deploy
docker-compose up --build -d
```

### Database Rollback

```bash
# 1. Check current migration
docker-compose exec backend alembic current

# 2. Downgrade to specific revision
docker-compose exec backend alembic downgrade <revision>

# 3. Or downgrade one step
docker-compose exec backend alembic downgrade -1
```

**Warning**: Database rollbacks may cause data loss. Always backup first!

---

## Database Migrations

### Creating a Migration

```bash
# Auto-generate from model changes
docker-compose exec backend alembic revision --autogenerate -m "description"

# Manual empty migration
docker-compose exec backend alembic revision -m "description"
```

### Running Migrations

```bash
# Upgrade to latest
docker-compose exec backend alembic upgrade head

# Upgrade to specific revision
docker-compose exec backend alembic upgrade <revision>

# Check current state
docker-compose exec backend alembic current

# View history
docker-compose exec backend alembic history --verbose
```

### Migration Best Practices

1. **Always backup before migrating production**
2. **Test migrations in staging first**
3. **Keep migrations small and focused**
4. **Include rollback logic in downgrade()**
5. **Never edit deployed migrations**

---

## Configuration Management

### Environment-Specific Configs

| Config | Development | Staging | Production |
|--------|-------------|---------|------------|
| DEBUG | true | true | false |
| LOG_LEVEL | DEBUG | INFO | WARNING |
| CORS_ORIGINS | * | staging domain | prod domain |
| RATE_LIMITS | relaxed | normal | strict |

### Secrets Rotation

```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -hex 32)

# 2. Update in .env
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env

# 3. Restart services
docker-compose up -d backend
```

### Configuration Validation

```bash
# Backend validates config on startup
docker-compose logs backend | grep -i "config"

# Common config errors:
# - Missing required env vars
# - Invalid DATABASE_URL format
# - Invalid API keys
```

---

## Health Checks

### Endpoint Overview

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/health` | Basic liveness | `{"status": "healthy"}` |
| `/health/live` | Kubernetes liveness | `{"status": "alive"}` |
| `/health/ready` | Full readiness | All services connected |

### Manual Health Verification

```bash
# Basic health
curl -s http://localhost:8001/health | jq .

# Detailed readiness
curl -s http://localhost:8001/health/ready | jq .

# Expected ready response:
{
  "status": "healthy",
  "timestamp": "2025-12-18T10:00:00Z",
  "version": "1.1.0",
  "database": {
    "status": "connected",
    "latency_ms": 2
  },
  "redis": {
    "status": "connected",
    "latency_ms": 1
  },
  "qdrant": {
    "status": "connected"
  }
}
```

### Container Health

```bash
# View container health status
docker-compose ps

# Check specific container
docker inspect subscription-backend --format='{{.State.Health.Status}}'

# View health check logs
docker inspect subscription-backend --format='{{json .State.Health}}' | jq .
```

---

## Monitoring Setup

### Prometheus + Grafana Stack

```bash
# Start monitoring services
docker-compose --profile monitoring up -d

# Access:
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3003 (admin/admin)
# - Alertmanager: http://localhost:9093
```

### Key Metrics to Monitor

| Metric | Threshold | Action |
|--------|-----------|--------|
| HTTP error rate | > 1% | Investigate logs |
| Response time P95 | > 500ms | Check database |
| Database connections | > 80% pool | Scale or optimize |
| Memory usage | > 80% | Scale or restart |
| Disk usage | > 70% | Clean logs/backups |

### Setting Up Alerts

```yaml
# Configured in monitoring/prometheus/rules/alerts.yml

# Example critical alerts:
- API down > 5 minutes
- Database connection failed
- Error rate > 5%
- Disk > 90%
```

---

## Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Common causes:
# 1. Missing env vars
# 2. Port already in use
# 3. Database not ready

# Fix: Check .env and port availability
lsof -i :8001
```

#### Database Connection Failed

```bash
# Verify database is running
docker-compose ps db

# Test connection
docker-compose exec db psql -U subscriptions -d subscriptions -c "SELECT 1"

# Check connection string
echo $DATABASE_URL
```

#### Migrations Failed

```bash
# View migration error
docker-compose exec backend alembic upgrade head --sql

# Common fixes:
# 1. Check for conflicting migrations
# 2. Verify database schema state
# 3. Rollback and re-run
```

#### High Memory Usage

```bash
# Check container stats
docker stats

# Restart high-memory container
docker-compose restart backend

# Scale if needed
docker-compose up -d --scale backend=2
```

#### Slow API Response

```bash
# Check database query times
docker-compose exec db psql -U subscriptions -c "
  SELECT query, calls, mean_time
  FROM pg_stat_statements
  ORDER BY mean_time DESC
  LIMIT 10;
"

# Check Redis cache
docker-compose exec redis redis-cli INFO stats
```

### Emergency Procedures

#### Service Down

1. Check container status: `docker-compose ps`
2. View logs: `docker-compose logs --tail=100 <service>`
3. Restart service: `docker-compose restart <service>`
4. If persists, rebuild: `docker-compose up --build -d <service>`

#### Database Corrupted

1. Stop all services: `docker-compose stop`
2. Restore from backup (see DISASTER_RECOVERY.md)
3. Run migrations: `alembic upgrade head`
4. Start services: `docker-compose up -d`

#### Security Incident

1. Rotate all secrets immediately
2. Review access logs
3. Scale down if under attack
4. Contact security team

---

## Appendix

### Useful Commands

```bash
# View all logs
docker-compose logs -f

# Enter container shell
docker-compose exec backend bash

# Database shell
docker-compose exec db psql -U subscriptions -d subscriptions

# Redis CLI
docker-compose exec redis redis-cli

# Clean up unused resources
docker system prune -a
```

### Contact Information

| Role | Contact |
|------|---------|
| DevOps Lead | devops@example.com |
| Backend Lead | backend@example.com |
| On-Call | pagerduty.com/moneyflow |

---

*Last Updated: December 2025*
*Version: 1.0.0*
