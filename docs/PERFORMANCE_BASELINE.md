# Money Flow - Performance Baseline

> **Sprint 2.4 - Performance & Load Testing Documentation**
>
> Last Updated: December 2025

## Overview

This document establishes performance baselines and targets for the Money Flow API.

## Performance Targets

### Response Time Targets (P95)

| Endpoint Type | Target P95 | Maximum Acceptable |
|---------------|------------|-------------------|
| Health checks | < 50ms | 100ms |
| GET (read) | < 200ms | 500ms |
| POST/PUT/DELETE | < 300ms | 750ms |
| Summary/Analytics | < 500ms | 1000ms |
| AI Agent | < 3000ms | 5000ms |

### Throughput Targets

| Scenario | Target RPS | Minimum Acceptable |
|----------|-----------|-------------------|
| Single user | 50+ | 30 |
| 10 concurrent | 200+ | 100 |
| 50 concurrent | 500+ | 250 |
| 100 concurrent | 750+ | 400 |

## Load Testing Configuration

### Locust Setup

Load testing uses [Locust](https://locust.io/) with the following user classes:

1. **SubscriptionCRUDUser** (weight: 3)
   - List subscriptions (5x)
   - Create subscription (3x)
   - Get subscription (2x)
   - Update subscription (1x)
   - Delete subscription (1x)

2. **SummaryUser** (weight: 2)
   - Get summary (3x)
   - Get upcoming payments (2x)

3. **AgentUser** (weight: 1)
   - Execute AI commands (1x)

4. **HealthCheckUser** (weight: 1)
   - Health checks (1x each)

5. **MixedWorkloadUser** (weight: 2)
   - Dashboard view (10x)
   - Add subscription (3x)
   - Check upcoming (2x)
   - Use agent (1x)

### Running Load Tests

```bash
# Quick test (10 users, 30s)
./scripts/run_load_tests.sh quick

# Medium test (50 users, 5m)
./scripts/run_load_tests.sh medium

# Full test (100 users, 10m)
./scripts/run_load_tests.sh full

# Web UI mode
./scripts/run_load_tests.sh web
```

## Test Scenarios

### Scenario 1: Quick Smoke Test
- **Users**: 10
- **Duration**: 30 seconds
- **Spawn rate**: 2/second
- **Purpose**: Verify basic functionality under light load

### Scenario 2: Normal Load
- **Users**: 50
- **Duration**: 5 minutes
- **Spawn rate**: 5/second
- **Purpose**: Simulate typical production load

### Scenario 3: Peak Load
- **Users**: 100
- **Duration**: 10 minutes
- **Spawn rate**: 10/second
- **Purpose**: Test system limits and identify bottlenecks

### Scenario 4: Soak Test
- **Users**: 30
- **Duration**: 1 hour
- **Purpose**: Identify memory leaks and resource exhaustion

### Scenario 5: Spike Test
- **Users**: 10 → 100 → 10
- **Duration**: 15 minutes
- **Purpose**: Test auto-scaling and recovery

## Benchmark Tests

Pytest-based benchmarks in `tests/performance/test_benchmarks.py`:

```bash
# Run benchmarks
pytest tests/performance/test_benchmarks.py -v -s

# With specific test
pytest tests/performance/test_benchmarks.py::TestHealthEndpointBenchmarks -v -s
```

### Measured Metrics

- **Min/Max/Mean/Median** response times
- **P95/P99** percentiles
- **Standard deviation**
- **Requests per second (RPS)**

## Database Performance

### Key Indexes

Ensure these indexes exist for optimal query performance:

```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);

-- Subscription queries
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_next_payment ON subscriptions(next_payment_date);
CREATE INDEX idx_subscriptions_payment_type ON subscriptions(payment_type);

-- Payment history
CREATE INDEX idx_payments_subscription ON payments(subscription_id);
CREATE INDEX idx_payments_date ON payments(payment_date);
```

### Query Optimization Tips

1. **Use eager loading** for related entities
2. **Avoid N+1 queries** with `selectinload()`
3. **Add composite indexes** for filtered queries
4. **Use pagination** for large result sets
5. **Consider read replicas** for analytics queries

## Caching Strategy

### Redis Cache Keys

| Key Pattern | TTL | Description |
|-------------|-----|-------------|
| `emb:{model}:{hash}` | 1 hour | Embedding vectors |
| `ctx:{user}:{session}` | 30 min | Conversation context |
| `search:{type}:{hash}` | 5 min | Search results |
| `summary:{user}:{date}` | 5 min | Summary calculations |

### Cache Invalidation

- **On create**: Invalidate list and summary caches
- **On update**: Invalidate specific item and summary
- **On delete**: Invalidate list, summary, and item

## Monitoring

### Key Metrics to Track

1. **Response times** (P50, P95, P99)
2. **Error rates** (5xx, 4xx)
3. **Throughput** (requests/second)
4. **Database query times**
5. **Cache hit rates**
6. **Memory usage**
7. **CPU utilization**

### Prometheus Metrics

Available at `/metrics`:

- `http_requests_total` - Request count by endpoint
- `http_request_duration_seconds` - Request latency histogram
- `db_query_duration_seconds` - Database query times
- `cache_hits_total` / `cache_misses_total` - Cache performance
- `agent_execution_seconds` - AI agent latency

## Known Bottlenecks

1. **AI Agent endpoint** - Limited by Claude API latency
2. **Summary calculations** - Aggregates all user subscriptions
3. **Vector search** - Depends on Qdrant performance

## Recommendations

### Short-term (Sprint 2.4)

- [x] Set up Locust for load testing
- [x] Create benchmark test suite
- [ ] Add response caching for list endpoints
- [ ] Optimize summary calculation queries
- [ ] Add database indexes

### Medium-term (Phase 3)

- [ ] Implement API response caching with Redis
- [ ] Add read replicas for analytics
- [ ] Consider async job processing for heavy operations
- [ ] Implement request coalescing for duplicate queries

### Long-term (Phase 4)

- [ ] Horizontal scaling with load balancer
- [ ] Database sharding by user
- [ ] CDN for static assets
- [ ] Edge caching for common queries

## Reports

Load test reports are generated in `reports/` directory:

- `load_test_quick_*.html` - Quick test results
- `load_test_medium_*.html` - Medium test results
- `load_test_full_*.html` - Full test results
- `load_test_*.csv` - Raw data for analysis

## References

- [Locust Documentation](https://docs.locust.io/)
- [FastAPI Performance](https://fastapi.tiangolo.com/advanced/async-tests/)
- [PostgreSQL Performance](https://www.postgresql.org/docs/current/performance-tips.html)
- [Redis Best Practices](https://redis.io/docs/management/optimization/)
