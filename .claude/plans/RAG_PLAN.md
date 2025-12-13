# RAG Implementation Plan

**Status**: Phase 4 Complete - RAG Implementation Done ✅
**Duration**: 4 Weeks
**Priority**: Medium
**Last Updated**: 2025-12-01

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Decisions](#architecture-decisions)
3. [Sprint Plan](#sprint-plan)
4. [Milestone Tracker](#milestone-tracker)
5. [Risk Assessment](#risk-assessment)
6. [Success Metrics](#success-metrics)

---

## Executive Summary

### What is RAG?

RAG (Retrieval-Augmented Generation) enhances our AI agent by giving it memory and context awareness. Instead of treating each message in isolation, the agent can:

- **Remember conversations**: "Cancel it" → knows you mean Netflix from earlier
- **Search semantically**: "Find subscriptions I mentioned for renewal"
- **Provide insights**: "Why is my spending higher?" → analyzes patterns

### Why We Need It

| Current Problem | RAG Solution |
|-----------------|--------------|
| Agent forgets context between messages | Conversation history stored and retrieved |
| Can't search notes naturally | Semantic search over all notes |
| No personalized insights | Pattern analysis from historical data |
| Ambiguous commands fail | Reference resolution ("it" → "Netflix") |

### Business Value

- **40% reduction** in failed/ambiguous commands
- **Better UX** with multi-turn conversations
- **Intelligent insights** that add real value
- **Foundation** for future AI features

---

## Architecture Decisions

### Decision 1: Vector Database - Qdrant

**Choice**: Qdrant v1.7+

**Alternatives Considered**:

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Qdrant** | Docker-native, excellent Python SDK, production-ready, built-in filtering | Newer, smaller community | ✅ Selected |
| Pinecone | Managed service, scalable | Paid, vendor lock-in, external dependency | ❌ Rejected |
| Weaviate | Full-featured, GraphQL | Complex setup, heavier resource usage | ❌ Rejected |
| ChromaDB | Simple, lightweight | Not production-ready, limited filtering | ❌ Rejected |
| pgvector | No new service, PostgreSQL native | Limited features, slower for large datasets | ❌ Rejected |

**Rationale**:
- Already have Docker infrastructure - Qdrant fits perfectly
- Excellent filtering by user_id (critical for data isolation)
- gRPC support for low latency
- Built-in persistence with volume mounts
- Free and self-hosted (no API costs)

---

### Decision 2: Embedding Model - Sentence Transformers

**Choice**: `all-MiniLM-L6-v2` (local)

**Alternatives Considered**:

| Option | Dimensions | Speed | Quality | Cost | Verdict |
|--------|------------|-------|---------|------|---------|
| **all-MiniLM-L6-v2** | 384 | ~50ms | Good | Free | ✅ Selected |
| all-mpnet-base-v2 | 768 | ~100ms | Better | Free | Future upgrade |
| OpenAI Ada-002 | 1536 | ~200ms | Best | $0.0001/1K tokens | ❌ Cost concern |
| Cohere Embed | 1024 | ~150ms | Very Good | Paid | ❌ Cost concern |

**Rationale**:
- Runs locally (no API calls, no costs, no latency)
- 384 dimensions is sufficient for our use case
- 50ms inference is fast enough for real-time
- Can upgrade to mpnet later if quality insufficient
- Model is only 80MB (small footprint)

---

### Decision 3: Caching Strategy - Redis

**Choice**: Use existing Redis for embedding cache

**What We Cache**:

| Data | TTL | Why |
|------|-----|-----|
| Query embeddings | 1 hour | Same queries are common |
| Conversation context | 30 min | Session-based, expires naturally |
| Search results | 5 min | Short-lived, data changes |

**Rationale**:
- Redis already in our stack (Qdrant is in docker-compose)
- Reduces embedding computation by ~60%
- Simple key-value pattern fits our needs
- TTL prevents stale data

---

### Decision 4: Context Window Strategy

**Choice**: Hybrid approach (Recent + Semantic)

**How It Works**:
1. **Recent turns** (last 5): Always include from current session
2. **Semantic search** (top 3): Find similar past conversations
3. **Combine**: Merge without duplicates, ordered by relevance

**Why Hybrid**:
- Recent turns capture immediate context ("Add Netflix" → "Change price")
- Semantic search finds relevant history ("Netflix" matches past Netflix discussions)
- Fallback if one method fails

---

### Decision 5: Reference Resolution Approach

**Choice**: Rule-based with context lookup

**How It Works**:
1. Detect pronouns: "it", "that", "them", "this"
2. Search recent conversation for mentioned entities
3. Replace pronoun with entity name
4. Pass resolved query to parser

**Example**:
```
Turn 1: "Add Netflix for £15.99" → stores {name: "Netflix"}
Turn 2: "Cancel it" → resolves to "Cancel Netflix"
```

**Why Not ML-Based**:
- Simpler to implement and debug
- Sufficient for our use case (subscription names)
- No additional model overhead
- Can upgrade later if needed

---

### Decision 6: Data Isolation Strategy

**Choice**: User-level filtering at query time

**Implementation**:
- All vectors tagged with `user_id` in payload
- Every search query includes `user_id` filter
- Database queries also filter by user
- No cross-user data leakage possible

**Why Not Separate Collections**:
- Would need dynamic collection creation per user
- Harder to manage and scale
- Qdrant filtering is efficient enough
- Simpler architecture

---

## Sprint Plan

### Sprint 1: Foundation (Week 1)

**Goal**: Infrastructure and core services running

| Day | Task | Owner | Deliverable |
|-----|------|-------|-------------|
| 1 | Add Qdrant to docker-compose | Dev | Qdrant running on port 6333 |
| 1 | Add dependencies to pyproject.toml | Dev | sentence-transformers, qdrant-client installed |
| 1 | Update config.py with RAG settings | Dev | Settings class extended |
| 2 | Implement EmbeddingService | Dev | Singleton service with embed/embed_batch |
| 2 | Write EmbeddingService tests | Dev | 80%+ coverage |
| 3 | Implement VectorStore | Dev | Qdrant wrapper with CRUD + search |
| 3 | Write VectorStore tests | Dev | 80%+ coverage |
| 4 | Implement RAGService core | Dev | Context retrieval working |
| 4 | Write RAGService tests | Dev | 80%+ coverage |
| 5 | Create Alembic migration | Dev | conversations, notes, analytics tables |
| 5 | Run migration, verify schema | Dev | Tables created in PostgreSQL |
| 6-7 | Integration testing | Dev | End-to-end flow working |
| 6-7 | Documentation | Dev | README updated |

**Exit Criteria**:
- [x] Qdrant healthy in Docker
- [x] Can generate embeddings
- [x] Can store and retrieve vectors
- [x] Database tables created (conversations, rag_analytics)
- [x] All unit tests passing (237 tests)

---

### Sprint 2: Core Features (Week 2)

**Goal**: Conversation tracking and semantic search working

| Day | Task | Owner | Deliverable |
|-----|------|-------|-------------|
| 1 | Implement ConversationService | Dev | Session management |
| 1 | Add session storage in Redis | Dev | TTL-based sessions |
| 2 | Implement reference resolution | Dev | Pronoun → entity mapping |
| 2 | Write resolution tests | Dev | Edge cases covered |
| 3 | Implement NoteSearchService | Dev | Semantic search over notes |
| 3 | Add note indexing on CRUD | Dev | Auto-index on create/update |
| 4 | Integrate RAG into agent executor | Dev | Agent uses context |
| 4 | Update agent prompts for context | Dev | Prompts include history |
| 5 | Create search API endpoints | Dev | /api/search/notes, /conversations |
| 5 | Write API tests | Dev | Endpoint tests passing |
| 6-7 | Integration testing | Dev | Multi-turn conversations work |
| 6-7 | Bug fixes | Dev | Issues resolved |

**Exit Criteria**:
- [ ] "Cancel it" resolves correctly
- [ ] Note search returns relevant results
- [ ] Agent uses conversation context
- [ ] API endpoints documented in Swagger

---

### Sprint 3: Advanced Features (Week 3)

**Goal**: Insights and historical queries

| Day | Task | Owner | Deliverable |
|-----|------|-------|-------------|
| 1 | Implement InsightsService | Dev | Spending pattern analysis |
| 2 | Add renewal predictions | Dev | Upcoming renewal alerts |
| 3 | Add cancellation recommendations | Dev | Suggest unused subscriptions |
| 4 | Implement HistoricalQueryService | Dev | Time-based queries work |
| 4 | Add temporal parsing | Dev | "last month", "in January" parsed |
| 5 | Create insights API endpoints | Dev | /api/insights/* endpoints |
| 6 | Frontend: insights component | Dev | Display insights in UI |
| 7 | Testing and polish | Dev | All features working |

**Exit Criteria**:
- [ ] "Why is spending higher?" works
- [ ] "What did I add in January?" works
- [ ] Insights displayed in UI
- [ ] All tests passing

---

### Sprint 4: Optimization (Week 4)

**Goal**: Production-ready performance and monitoring

| Day | Task | Owner | Deliverable |
|-----|------|-------|-------------|
| 1 | Implement embedding cache | Dev | Redis caching for embeddings |
| 2 | Add batch processing | Dev | Batch queries for efficiency |
| 3 | Implement hybrid search | Dev | Semantic + keyword combined |
| 4 | Add performance monitoring | Dev | Latency tracking |
| 5 | Implement RAG analytics | Dev | Query logging and metrics |
| 6 | Load testing | Dev | Performance benchmarks |
| 7 | Documentation and cleanup | Dev | Final documentation |

**Exit Criteria**:
- [ ] Query latency < 300ms (p95)
- [ ] Cache hit rate > 60%
- [ ] Monitoring dashboard available
- [ ] Load test passed (100 concurrent users)

---

## Milestone Tracker

### Phase 1: Foundation

| # | Milestone | Target Date | Status | Notes |
|---|-----------|-------------|--------|-------|
| 1.1 | Qdrant running in Docker | Week 1, Day 1 | ✅ Completed | Already in docker-compose.yml |
| 1.2 | EmbeddingService complete | Week 1, Day 2 | ✅ Completed | Singleton with lazy loading |
| 1.3 | VectorStore complete | Week 1, Day 3 | ✅ Completed | CRUD + search with user filtering |
| 1.4 | RAGService core complete | Week 1, Day 4 | ✅ Completed | Context retrieval, reference resolution |
| 1.5 | Database migration applied | Week 1, Day 5 | ✅ Completed | conversations, rag_analytics tables created |
| 1.6 | Phase 1 tests passing | Week 1, Day 7 | ✅ Completed | 47 RAG tests + 237 total tests passing |

### Phase 2: Core Features

| # | Milestone | Target Date | Status | Notes |
|---|-----------|-------------|--------|-------|
| 2.1 | ConversationService complete | Week 2, Day 1 | ✅ Completed | DB persistence + RAG integration |
| 2.2 | Reference resolution working | Week 2, Day 2 | ✅ Completed | Integrated into AgentExecutor |
| 2.3 | Note search working | Week 2, Day 3 | ✅ Completed | Auto-index on create/update |
| 2.4 | Agent integrated with RAG | Week 2, Day 4 | ✅ Completed | Context retrieval in execute() |
| 2.5 | Search API endpoints live | Week 2, Day 5 | ✅ Completed | /api/search/notes, /conversations, /history |
| 2.6 | Phase 2 tests passing | Week 2, Day 7 | ✅ Completed | 255 total tests (18 new) |

### Phase 3: Advanced Features

| # | Milestone | Target Date | Status | Notes |
|---|-----------|-------------|--------|-------|
| 3.1 | InsightsService complete | Week 3, Day 2 | ✅ Completed | Trends, categories, renewals, recommendations |
| 3.2 | Historical queries working | Week 3, Day 4 | ✅ Completed | Temporal parsing, date ranges |
| 3.3 | Insights API endpoints | Week 3, Day 6 | ✅ Completed | /api/insights/*, /historical |
| 3.4 | Phase 3 tests passing | Week 3, Day 7 | ✅ Completed | 319 total tests (64 new) |

### Phase 4: Optimization

| # | Milestone | Target Date | Status | Notes |
|---|-----------|-------------|--------|-------|
| 4.1 | Embedding cache implemented | Week 4, Day 1 | ✅ Completed | Redis CacheService with TTL |
| 4.2 | Hybrid search working | Week 4, Day 3 | ✅ Completed | Semantic + keyword boosting |
| 4.3 | Monitoring dashboard | Week 4, Day 5 | ✅ Completed | RAGAnalyticsService + /api/analytics |
| 4.4 | Load test passed | Week 4, Day 6 | ⏭️ Skipped | Deferred to production readiness |
| 4.5 | Documentation complete | Week 4, Day 7 | ✅ Completed | 373 tests passing |

---

## Risk Assessment

### Risk 1: Performance Degradation

**Risk Level**: Medium

**Description**: RAG adds latency to every agent request (embedding + vector search + context building)

**Mitigation**:
- Aggressive caching (target 60% hit rate)
- Async processing where possible
- Fallback to non-RAG if timeout (500ms)
- Use gRPC for Qdrant (faster than HTTP)

**Monitoring**: Track p95 latency, alert if > 300ms

---

### Risk 2: Poor Search Quality

**Risk Level**: Medium

**Description**: Semantic search might return irrelevant results

**Mitigation**:
- Hybrid search (semantic + keyword)
- Minimum score threshold (0.5)
- User feedback collection
- A/B testing different models

**Monitoring**: Track relevance scores, user feedback

---

### Risk 3: Memory/Resource Usage

**Risk Level**: Low

**Description**: Embedding model uses ~500MB RAM, Qdrant uses disk

**Mitigation**:
- Use smaller model (MiniLM is 80MB)
- Limit vector count per user
- Implement TTL for old data
- Monitor resource usage

**Monitoring**: Docker stats, memory alerts

---

### Risk 4: Data Privacy

**Risk Level**: Low

**Description**: RAG stores conversation data, potential privacy concern

**Mitigation**:
- User-level data isolation (filter by user_id)
- No cross-user data access possible
- Encryption at rest (Qdrant supports it)
- Clear data retention policy

**Monitoring**: Audit logs, access patterns

---

## Success Metrics

### Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| RAG query latency (p95) | < 300ms | Prometheus/logging |
| Embedding generation | < 100ms | Logging |
| Vector search | < 50ms | Qdrant metrics |
| Cache hit rate | > 60% | Redis stats |
| End-to-end response | < 500ms | Frontend timing |

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Reference resolution accuracy | > 90% | Manual testing |
| Search relevance score (avg) | > 0.7 | Qdrant scores |
| User feedback "helpful" | > 75% | UI feedback button |
| Ambiguous query reduction | 40% | Error rate comparison |

### Usage Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Queries using RAG | > 30% | Analytics |
| Multi-turn conversations | > 5/user/week | Session tracking |
| Note searches per day | > 10 | API logs |
| Insights viewed | > 50% of users | Frontend analytics |

---

## File Structure (To Be Created)

```
src/services/
├── embedding_service.py    # Sentence Transformers wrapper
├── vector_store.py         # Qdrant client wrapper
├── rag_service.py          # Main RAG orchestration
├── conversation_service.py # Session & context management
├── note_search_service.py  # Semantic note search
├── insights_service.py     # Pattern analysis
└── rag_analytics.py        # Monitoring & metrics

src/api/
├── search.py               # Search endpoints
└── insights.py             # Insights endpoints

src/db/migrations/versions/
└── xxx_add_rag_tables.py   # conversations, notes, analytics

tests/unit/
├── test_embedding_service.py
├── test_vector_store.py
├── test_rag_service.py
└── test_conversation_service.py

tests/integration/
└── test_rag_flow.py        # End-to-end RAG tests
```

---

## Dependencies to Add

```toml
# pyproject.toml additions
qdrant-client = ">=1.7.0"
sentence-transformers = ">=2.2.0"
torch = ">=2.0.0"
numpy = ">=1.24.0"
```

---

## Configuration to Add

```python
# Settings additions (no code, just reference)
rag_enabled: bool = True
qdrant_host: str = "qdrant"
qdrant_port: int = 6333
embedding_model: str = "all-MiniLM-L6-v2"
embedding_dimension: int = 384
rag_top_k: int = 5
rag_min_score: float = 0.5
rag_context_window: int = 5
```

---

## Appendix: Glossary

| Term | Definition |
|------|------------|
| **RAG** | Retrieval-Augmented Generation - enhancing LLM with retrieved context |
| **Embedding** | Vector representation of text (384 floats for MiniLM) |
| **Vector Database** | Database optimized for similarity search on vectors |
| **Semantic Search** | Finding similar meaning, not just keywords |
| **Context Window** | Number of past conversation turns to include |
| **Reference Resolution** | Converting "it" to the actual entity name |

---

**Document Owner**: Development Team
**Review Cycle**: Weekly during implementation
**Next Review**: After Sprint 1 completion
