# Money Flow - Incident Response Playbook

> Procedures for detecting, responding to, and recovering from incidents

---

## Table of Contents

1. [Incident Severity Levels](#incident-severity-levels)
2. [Detection & Alerting](#detection--alerting)
3. [Incident Response Process](#incident-response-process)
4. [Specific Incident Playbooks](#specific-incident-playbooks)
5. [Communication Templates](#communication-templates)
6. [Post-Incident Review](#post-incident-review)

---

## Incident Severity Levels

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| **SEV-1** (Critical) | Service completely down, data breach | 15 minutes | API unreachable, database corruption |
| **SEV-2** (High) | Major feature broken, security risk | 1 hour | Auth failing, payments not saving |
| **SEV-3** (Medium) | Feature degraded, workaround exists | 4 hours | Slow performance, partial failures |
| **SEV-4** (Low) | Minor issue, cosmetic | 24 hours | UI glitch, log noise |

### Escalation Path

```
SEV-4: On-call engineer
  ↓
SEV-3: Team lead + on-call
  ↓
SEV-2: Engineering manager + team
  ↓
SEV-1: All hands + executive notification
```

---

## Detection & Alerting

### Monitoring Sources

| Source | What It Detects | Alert Channel |
|--------|-----------------|---------------|
| Prometheus | Metrics anomalies | Alertmanager → Telegram |
| Grafana | Dashboard thresholds | Email, Slack |
| Sentry | Application errors | Email, Slack |
| Health checks | Service availability | PagerDuty |
| Log aggregation | Error patterns | Loki → Grafana |

### Key Alerts

| Alert | Severity | Condition |
|-------|----------|-----------|
| API Down | SEV-1 | Health check fails 3x |
| Database Unreachable | SEV-1 | Connection timeout |
| Error Rate Spike | SEV-2 | >5% errors in 5 min |
| High Latency | SEV-3 | P95 >2s for 10 min |
| Disk Space Low | SEV-3 | >80% usage |
| Rate Limit Exceeded | SEV-4 | Many 429 responses |

---

## Incident Response Process

### Phase 1: Detection (0-5 minutes)

1. **Alert received** - Note time and source
2. **Acknowledge** - Claim incident in on-call system
3. **Initial assessment** - Check dashboards, logs
4. **Classify severity** - Assign SEV level

```bash
# Quick health check
curl -s http://localhost:8001/health/ready | jq .

# Check container status
docker-compose ps

# Recent errors
docker-compose logs --tail=100 backend | grep -i error
```

### Phase 2: Triage (5-15 minutes)

1. **Identify scope** - How many users affected?
2. **Isolate cause** - Which component is failing?
3. **Communicate** - Notify stakeholders per severity

```bash
# Check error rate
curl -s http://localhost:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m])

# Check database connections
docker-compose exec db psql -U subscriptions -c "SELECT count(*) FROM pg_stat_activity;"

# Check Redis
docker-compose exec redis redis-cli PING
```

### Phase 3: Mitigation (15-60 minutes)

1. **Apply quick fix** - Restart, scale, rollback
2. **Monitor improvement** - Watch metrics
3. **Document actions** - Log everything tried

```bash
# Restart problematic service
docker-compose restart backend

# Scale up if needed
docker-compose up -d --scale backend=2

# Rollback if recent deploy
git checkout HEAD~1
docker-compose up --build -d backend
```

### Phase 4: Resolution (1-24 hours)

1. **Root cause analysis** - Identify underlying issue
2. **Permanent fix** - Deploy proper solution
3. **Verify resolution** - Confirm metrics normal
4. **Close incident** - Mark resolved

### Phase 5: Post-Incident (24-72 hours)

1. **Write post-mortem** - Document incident
2. **Identify action items** - Prevent recurrence
3. **Share learnings** - Team discussion

---

## Specific Incident Playbooks

### Playbook 1: API Completely Down (SEV-1)

**Symptoms:**
- Health check returns error
- All API requests failing
- Frontend shows connection errors

**Investigation:**

```bash
# 1. Check container status
docker-compose ps

# 2. View backend logs
docker-compose logs --tail=200 backend

# 3. Check if port is listening
lsof -i :8001

# 4. Verify database connection
docker-compose exec backend python -c "
from src.db.database import get_engine
engine = get_engine()
with engine.connect() as conn:
    print(conn.execute('SELECT 1').fetchone())
"
```

**Resolution Steps:**

1. **Container crashed**: `docker-compose up -d backend`
2. **Port conflict**: Kill conflicting process
3. **DB connection failed**: Check DATABASE_URL, restart DB
4. **Out of memory**: Increase limits, restart
5. **Bad deploy**: Rollback to previous version

**Recovery Verification:**

```bash
# Health check
curl http://localhost:8001/health/ready

# Test API call
curl http://localhost:8001/api/v1/auth/login -X POST -H "Content-Type: application/json" -d '{"email":"test@test.com","password":"Test123!@#"}'
```

---

### Playbook 2: Database Connection Failure (SEV-1)

**Symptoms:**
- "Connection refused" errors
- 500 errors on all data operations
- Health check shows database unhealthy

**Investigation:**

```bash
# 1. Check DB container
docker-compose ps db
docker-compose logs --tail=50 db

# 2. Test direct connection
docker-compose exec db psql -U subscriptions -c "SELECT 1;"

# 3. Check connection pool
docker-compose exec backend python -c "
from src.db.database import get_pool_status
print(get_pool_status())
"

# 4. Check for locks
docker-compose exec db psql -U subscriptions -c "
SELECT pid, query, state FROM pg_stat_activity WHERE state != 'idle';
"
```

**Resolution Steps:**

1. **DB container down**: `docker-compose up -d db`
2. **Connection pool exhausted**: Restart backend
3. **Deadlock**: Kill blocking queries
4. **Disk full**: Clean up, expand storage
5. **Corrupted**: Restore from backup

**Kill blocking queries:**

```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active'
  AND query_start < NOW() - INTERVAL '5 minutes';
```

---

### Playbook 3: High Error Rate (SEV-2)

**Symptoms:**
- Error rate >5%
- Sentry flooding with errors
- User complaints

**Investigation:**

```bash
# 1. Check error distribution
curl -s "http://localhost:9090/api/v1/query?query=sum(rate(http_requests_total{status=~'5..'}[5m]))by(endpoint)"

# 2. View recent errors in Sentry
# (Check Sentry dashboard)

# 3. Check specific endpoint
docker-compose logs backend | grep "500" | tail -20

# 4. Check for patterns
docker-compose logs backend | grep -E "ERROR|Exception" | tail -50
```

**Resolution Steps:**

1. **Single endpoint failing**: Check that specific handler
2. **Database timeout**: Check slow queries, add indexes
3. **External API failing**: Check Anthropic/Telegram status
4. **Rate limiting**: Adjust limits or scale
5. **Bug in recent deploy**: Rollback

---

### Playbook 4: Performance Degradation (SEV-3)

**Symptoms:**
- Response time P95 >2 seconds
- Timeouts occurring
- Users reporting slowness

**Investigation:**

```bash
# 1. Check response times
curl -s "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(http_request_duration_seconds_bucket[5m]))"

# 2. Check database queries
docker-compose exec db psql -U subscriptions -c "
SELECT query, calls, mean_time, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"

# 3. Check Redis cache hit rate
docker-compose exec redis redis-cli INFO stats | grep keyspace

# 4. Check container resources
docker stats
```

**Resolution Steps:**

1. **Slow DB queries**: Add indexes, optimize queries
2. **No caching**: Verify Redis connection, TTLs
3. **Memory pressure**: Increase container limits
4. **CPU bound**: Scale horizontally
5. **Network latency**: Check container networking

---

### Playbook 5: Security Incident (SEV-1/2)

**Symptoms:**
- Unusual access patterns
- Failed login spikes
- Unauthorized data access

**Immediate Actions:**

```bash
# 1. Check for brute force
docker-compose logs backend | grep "401" | wc -l

# 2. Check recent logins
docker-compose exec db psql -U subscriptions -c "
SELECT email, last_login, failed_login_attempts
FROM users
ORDER BY last_login DESC
LIMIT 20;
"

# 3. Check for suspicious IPs
docker-compose logs backend | grep "POST /api/v1/auth" | awk '{print $1}' | sort | uniq -c | sort -rn | head -10
```

**Containment Steps:**

1. **Rotate secrets immediately**
   ```bash
   # Generate new secrets
   export NEW_SECRET=$(openssl rand -hex 32)
   export NEW_JWT=$(openssl rand -hex 32)

   # Update and restart
   sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env
   docker-compose up -d backend
   ```

2. **Block suspicious IPs** (if applicable)

3. **Force logout all users**
   ```bash
   docker-compose exec redis redis-cli FLUSHDB
   ```

4. **Review access logs**

5. **Notify affected users** (if data breach)

---

### Playbook 6: Telegram Notifications Failing (SEV-3)

**Symptoms:**
- Users not receiving reminders
- Test notifications failing
- Telegram webhook errors

**Investigation:**

```bash
# 1. Check Telegram service status
curl -s http://localhost:8001/health/ready | jq '.telegram'

# 2. Check for webhook errors
docker-compose logs backend | grep -i telegram | tail -20

# 3. Verify bot token
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"

# 4. Check notification preferences table
docker-compose exec db psql -U subscriptions -c "
SELECT COUNT(*) as linked_users
FROM notification_preferences
WHERE telegram_verified = true;
"
```

**Resolution Steps:**

1. **Bot token invalid**: Regenerate with @BotFather
2. **Webhook not receiving**: Check URL configuration
3. **Rate limited by Telegram**: Implement exponential backoff
4. **Database issue**: Check notification_preferences table

---

## Communication Templates

### Internal Status Update

```
INCIDENT UPDATE - [SEV-X] [Brief Description]

Time: [Current time]
Status: [Investigating/Mitigating/Resolved]
Impact: [User impact description]

What we know:
- [Finding 1]
- [Finding 2]

Actions taken:
- [Action 1]
- [Action 2]

Next steps:
- [Plan]

ETA to resolution: [Estimate or "Unknown"]
```

### User Communication (Outage)

```
We're aware of issues with [Feature/Service] and are actively working on a fix.

Current status: [Brief description]
Expected resolution: [Time estimate]

We apologize for any inconvenience and will provide updates as we have them.
```

### User Communication (Resolved)

```
The issue with [Feature/Service] has been resolved.

What happened: [Brief non-technical explanation]
Duration: [Start time] to [End time]
Impact: [What users experienced]

We've identified the root cause and are taking steps to prevent this in the future.

We apologize for any inconvenience caused.
```

---

## Post-Incident Review

### Post-Mortem Template

```markdown
# Post-Mortem: [Incident Title]

**Date**: [Date]
**Duration**: [X hours Y minutes]
**Severity**: SEV-[X]
**Author**: [Name]

## Summary
[1-2 sentence description of what happened]

## Timeline (all times in UTC)
- HH:MM - [Event 1]
- HH:MM - [Event 2]
- HH:MM - [Resolution]

## Root Cause
[Detailed explanation of why this happened]

## Impact
- Users affected: [Number]
- Revenue impact: [If applicable]
- Data impact: [Any data loss/corruption]

## What Went Well
- [Positive 1]
- [Positive 2]

## What Went Poorly
- [Issue 1]
- [Issue 2]

## Action Items
| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| [Action 1] | [Name] | [Date] | Open |
| [Action 2] | [Name] | [Date] | Open |

## Lessons Learned
- [Learning 1]
- [Learning 2]
```

### Review Process

1. **Schedule review** - Within 48 hours of resolution
2. **Gather data** - Logs, metrics, communication
3. **Write draft** - Fill out template
4. **Team review** - Discuss blameless
5. **Assign actions** - Prevent recurrence
6. **Archive** - Store in incidents folder

---

## Appendix

### Quick Reference Commands

```bash
# Service status
docker-compose ps

# All logs
docker-compose logs -f

# Specific service logs
docker-compose logs -f backend

# Restart service
docker-compose restart <service>

# Rebuild and restart
docker-compose up --build -d <service>

# Database shell
docker-compose exec db psql -U subscriptions -d subscriptions

# Redis CLI
docker-compose exec redis redis-cli

# Check metrics
curl -s http://localhost:8001/metrics | grep http_request

# Health check
curl -s http://localhost:8001/health/ready | jq .
```

### Contact List

| Role | Name | Contact |
|------|------|---------|
| On-Call Primary | [Name] | [Phone/Slack] |
| On-Call Secondary | [Name] | [Phone/Slack] |
| Engineering Manager | [Name] | [Phone/Slack] |
| DevOps Lead | [Name] | [Phone/Slack] |

### External Dependencies

| Service | Status Page | Support |
|---------|-------------|---------|
| Anthropic | status.anthropic.com | support@anthropic.com |
| Telegram | telegram.org/faq | @BotFather |
| GCP | status.cloud.google.com | GCP Console |

---

*Last Updated: December 2025*
*Version: 1.0.0*
