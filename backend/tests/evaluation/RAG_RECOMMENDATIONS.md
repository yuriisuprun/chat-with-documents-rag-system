# RAG Pipeline Improvement Recommendations

**Report Date:** 2026-01-06  
**Current Status:** Evaluation framework deployed, ready for integration  
**Recommendation Type:** Framework-based continuous improvement roadmap

## Executive Recommendations

Based on the comprehensive RAG evaluation framework, we recommend a phased approach to optimize the Chat With Documents system:

### Phase 1: Foundation (Weeks 1-2)
- Connect framework to real RAG service
- Establish performance baselines
- Identify top 5 failure patterns

### Phase 2: Quick Wins (Weeks 3-4)
- Implement high-impact fixes
- Improve retrieval quality
- Reduce hallucinations

### Phase 3: Advanced (Weeks 5-8)
- Implement RAGAS metrics
- Domain-specific tuning
- Production hardening

## Priority Framework: Impact vs. Effort

```
┌─────────────────────────────────────────┐
│ High Impact                             │
│ • Retrieval optimization                │
│ • Hallucination reduction               │
│ • Error recovery                        │
├─────────────────────────────────────────┤
│ Medium Impact                           │
│ • Citation improvements                 │
│ • Relevance enhancement                 │
│ • Performance optimization              │
├─────────────────────────────────────────┤
│ Low Impact                              │
│ • Formatting improvements               │
│ • UX enhancements                       │
│ • Logging improvements                  │
└─────────────────────────────────────────┘
     Low       Medium      High
         Effort/Complexity
```

## Detailed Recommendations

### PRIORITY 1: Retrieval Quality Improvements

**Current State:** Framework can measure Recall@K, Precision@K, MRR metrics

**Recommendations:**

#### 1.1 Embedding Model Optimization
**Impact:** HIGH | **Effort:** MEDIUM | **Timeline:** 2-3 weeks

**Current Setup:**
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Dimension: 384
- Speed: Fast
- Quality: Baseline

**Options to Evaluate:**

| Model | Dimension | Quality | Speed | Use Case |
|-------|-----------|---------|-------|----------|
| all-MiniLM-L6-v2 | 384 | Baseline | Fast | Current |
| all-mpnet-base-v2 | 768 | Better | Medium | Accuracy focus |
| all-MiniLM-L12-v2 | 384 | Good | Medium | Balanced |
| bge-large-en-v1.5 | 1024 | Excellent | Slow | Premium |

**Testing Process:**
1. Download candidate models
2. Re-embed existing chunks
3. Run evaluation framework on all 100 questions
4. Compare Recall@K, Precision@K metrics
5. Measure latency impact
6. Calculate cost/benefit

**Expected Impact:** +15-25% improvement in retrieval recall/precision

**Implementation:**
```python
# In infrastructure/embeddings/huggingface_provider.py
# Change model_name based on test results
model_name = "all-mpnet-base-v2"  # Test this
```

#### 1.2 Chunk Size and Overlap Tuning
**Impact:** HIGH | **Effort:** LOW | **Timeline:** 1 week

**Current Configuration:**
- Chunk size: 1000 characters
- Overlap: 100 characters

**Testing Matrix:**
```
Chunk Sizes: 500, 750, 1000, 1250, 1500 chars
Overlap:     0, 50, 100, 150, 200 chars

Test: Run framework on subset (25 questions)
Measure: Recall@K, precision, context quality
```

**Optimization Goals:**
- Maximize context coherence
- Maintain semantic boundaries
- Minimize redundancy

**Implementation:**
```python
# In infrastructure/pdf/chunker.py
chunk_size = 1000  # Tune this
chunk_overlap = 100  # Tune this
```

**Expected Impact:** +10-15% improvement in retrieval quality

#### 1.3 Query Expansion Implementation
**Impact:** MEDIUM | **Effort:** MEDIUM | **Timeline:** 2 weeks

**Problem:** Queries may use different terminology than documents

**Solution:** Expand queries before embedding

**Implementation Approach:**
```python
def expand_query(query: str) -> list[str]:
    """Generate query variations."""
    variations = []
    
    # Original
    variations.append(query)
    
    # Paraphrased (using LLM if available)
    # paraphrased = llm.generate(f"Rephrase: {query}")
    # variations.append(paraphrased)
    
    # Generic expansion
    # Add synonyms, related terms
    
    return variations

# Then search with all variations
```

**Expected Impact:** +10-20% recall improvement for ambiguous queries

#### 1.4 Hybrid Retrieval (Dense + Sparse)
**Impact:** MEDIUM | **Effort:** HIGH | **Timeline:** 3-4 weeks

**Current:** Dense vector search only

**Proposed:** Combine dense + BM25 sparse search

**Benefits:**
- Dense: Semantic similarity
- Sparse: Exact term matching
- Combined: Complementary strengths

**Implementation Path:**
1. Index documents with BM25 (Elasticsearch, Solr, or Python `rank_bm25`)
2. Score chunks with both methods
3. Combine scores (e.g., 70% dense + 30% sparse)
4. Rerank results

**Expected Impact:** +20-30% improvement in hard queries

### PRIORITY 2: Hallucination Reduction

**Current State:** Framework detects hallucinations via multiple methods

**Recommendations:**

#### 2.1 Enhanced Sufficiency Checking
**Impact:** HIGH | **Effort:** LOW | **Timeline:** 1 week

**Current Implementation:**
- Basic check using LLM response parsing
- Limited instruction set

**Improvements:**
```python
# In services/rag_service.py - improve _check_sufficiency()

def _check_sufficiency(self, question: str, context: str) -> bool:
    """Enhanced sufficiency check."""
    
    if not context or len(context) < 100:
        return False  # Too little context
    
    if len(context) > 50000:
        return False  # Too much context, likely noise
    
    # Check coverage
    key_terms = extract_key_terms(question)
    coverage = sum(1 for term in key_terms if term in context.lower())
    
    if coverage < len(key_terms) * 0.5:
        return False  # Only 50% coverage
    
    # Use LLM for final check with clearer prompt
    prompt = f"""Is the provided context sufficient to answer this question?
    
Question: {question}

Context: {context[:1000]}...

Respond with exactly: SUFFICIENT or INSUFFICIENT"""
    
    response = self.llm_provider.generate(prompt, temperature=0.0)
    return "SUFFICIENT" in response.upper()
```

**Expected Impact:** -30-50% hallucination rate

#### 2.2 Prompt Engineering for Faithfulness
**Impact:** HIGH | **Effort:** LOW | **Timeline:** 1 week

**Current Prompt:** Basic template

**Enhanced Prompt:**
```python
# In prompts/rag_prompt.py

ENHANCED_RAG_PROMPT = """You are a helpful assistant answering questions based ONLY on the provided context.

CRITICAL RULES:
1. ONLY use information from the context below
2. Do NOT use any external knowledge or assumptions
3. If the context doesn't contain the answer, say "The provided documents don't contain information about this."
4. For every fact stated, cite the source: [Document Name, Page X]
5. Explain your reasoning step by step
6. Be precise and avoid generalizations

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
```

**Expected Impact:** -20-40% hallucinations through better instruction

#### 2.3 Post-Generation Validation
**Impact:** MEDIUM | **Effort:** MEDIUM | **Timeline:** 2 weeks

**Approach:** Validate generated answers against context

```python
def validate_answer(answer: str, context: str, question: str) -> dict:
    """Validate answer against context."""
    
    validation = {
        "has_unsupported_claims": False,
        "claims": [],
        "uncited_claims": [],
        "confidence": 0.0
    }
    
    # Extract claims from answer
    claims = extract_claims(answer)
    
    for claim in claims:
        # Check if claim appears in context
        if claim not in context:
            validation["has_unsupported_claims"] = True
            validation["uncited_claims"].append(claim)
    
    # Check factual consistency
    # Use NLI (Natural Language Inference) model if available
    
    return validation

# Usage
validation_result = validate_answer(generated_answer, context, question)
if validation_result["has_unsupported_claims"]:
    # Regenerate or mark as uncertain
    pass
```

**Expected Impact:** -50-70% hallucinations via validation

### PRIORITY 3: Citation and Attribution

**Current State:** Framework measures citation presence and accuracy

**Recommendations:**

#### 3.1 Chunk-to-Answer Mapping
**Impact:** MEDIUM | **Effort:** MEDIUM | **Timeline:** 2 weeks

**Goal:** Track which chunk contributed to each sentence

**Implementation:**
```python
def generate_with_attribution(question: str, chunks: list[RetrievedChunk]) -> dict:
    """Generate answer with full attribution."""
    
    answer_parts = []
    
    for i, chunk in enumerate(chunks):
        # Generate for each chunk separately
        prompt = f"""Based on this passage:
{chunk.text}

Answer: {question}

Keep answer concise (1-2 sentences)."""
        
        part_answer = llm.generate(prompt)
        answer_parts.append({
            "text": part_answer,
            "chunk_id": chunk.chunk_id,
            "document": chunk.metadata.get("filename"),
            "page": chunk.metadata.get("page_number")
        })
    
    # Combine parts
    full_answer = " ".join(p["text"] for p in answer_parts)
    
    return {
        "answer": full_answer,
        "attribution": answer_parts,
        "sources": extract_unique_sources(answer_parts)
    }
```

**Expected Impact:** +40-50% citation accuracy

#### 3.2 Source Citation Formatting
**Impact:** LOW | **Effort:** LOW | **Timeline:** 1 week

**Goal:** Consistent, user-friendly citation format

```python
# Format citations consistently
citation_template = "[{document} - Page {page}]"

# Example output:
answer = """The RAG architecture uses ChromaDB for vector storage [technical_spec.pdf - Page 3] 
and FastAPI for the web interface [architecture.pdf - Page 1]."""
```

**Expected Impact:** Better user trust through clear attribution

### PRIORITY 4: Error Handling and Recovery

**Current State:** Framework tracks errors and execution time

**Recommendations:**

#### 4.1 Retry Logic with Backoff
**Impact:** MEDIUM | **Effort:** LOW | **Timeline:** 1 week

**Implementation:**
```python
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(multiplier=1, min=2, max=10),
       stop=stop_after_attempt(3))
async def retrieve_with_retry(query: str, top_k: int = 4):
    """Retrieve with automatic retry."""
    try:
        return await retrieval_service.retrieve(query, top_k)
    except Exception as e:
        logger.warning(f"Retrieval attempt failed: {e}")
        raise
```

**Expected Impact:** 99%+ system availability

#### 4.2 Service Fallbacks
**Impact:** MEDIUM | **Effort:** MEDIUM | **Timeline:** 2 weeks

**Fallback Strategy:**
```
LLM Provider Hierarchy:
1. Primary: Groq (fast, cloud)
2. Secondary: Ollama (local, reliable)
3. Fallback: Return context directly

Embedding Provider Hierarchy:
1. Primary: sentence-transformers (GPU)
2. Fallback: CPU-based model (slower)
```

**Expected Impact:** Reduced service unavailability

#### 4.3 Graceful Degradation
**Impact:** MEDIUM | **Effort:** MEDIUM | **Timeline:** 2 weeks

**Levels of Response:**
- **Ideal:** Full RAG (retrieval + generation + citations)
- **Degraded:** Retrieval only (return top chunks)
- **Minimal:** Error message + retry option

**Expected Impact:** User experience maintained during outages

### PRIORITY 5: Performance Optimization

**Current State:** Framework measures execution time

**Recommendations:**

#### 5.1 Result Caching
**Impact:** MEDIUM | **Effort:** LOW | **Timeline:** 1 week

**Approach:**
```python
from functools import lru_cache
from diskcache import Cache

# Query cache
@lru_cache(maxsize=1000)
def cached_embedding(text: str) -> list[float]:
    """Cache query embeddings."""
    return embedding_provider.embed_text(text)

# Response cache
response_cache = Cache("./cache/rag_responses")

def get_or_generate(question: str):
    # Check cache first
    cached = response_cache.get(question)
    if cached:
        return cached
    
    # Generate and cache
    result = rag_service.answer_question(question)
    response_cache[question] = result
    return result
```

**Expected Impact:** 30-50% faster responses for repeated queries

#### 5.2 Batch Processing
**Impact:** MEDIUM | **Effort:** MEDIUM | **Timeline:** 2 weeks

**Approach:**
```python
async def process_batch(queries: list[str]):
    """Process multiple queries efficiently."""
    
    # Batch embeddings
    embeddings = embedding_provider.embed_texts(queries)
    
    # Batch retrieval
    all_results = vector_store.search_batch(embeddings)
    
    # Parallel generation
    tasks = [
        llm_provider.generate_async(build_prompt(q, r))
        for q, r in zip(queries, all_results)
    ]
    
    answers = await asyncio.gather(*tasks)
    return answers
```

**Expected Impact:** 3-5x throughput improvement for batch operations

#### 5.3 Index Optimization
**Impact:** LOW | **Effort:** MEDIUM | **Timeline:** 2 weeks

**Approaches:**
- Use approximate nearest neighbor (ANN) search
- Implement vector quantization
- Add indexing strategies (hierarchical, product quantization)

**Expected Impact:** 50-70% faster retrieval, less memory

## Implementation Roadmap

### Month 1: Retrieval & Hallucination Focus

**Week 1-2:**
- [ ] Connect evaluation framework to real service
- [ ] Establish baseline metrics
- [ ] Test embedding models (1.2)
- [ ] Tune chunk parameters (1.3)

**Week 3-4:**
- [ ] Implement enhanced sufficiency checking (2.1)
- [ ] Improve prompt engineering (2.2)
- [ ] Add citation tracking (3.1)
- [ ] Measure improvement

**Deliverables:**
- Baseline performance document
- Model comparison report
- Improved configuration
- Initial metric improvements

### Month 2: Quality & Performance

**Week 5-6:**
- [ ] Implement post-generation validation (2.3)
- [ ] Add retry logic (4.1)
- [ ] Implement caching (5.1)

**Week 7-8:**
- [ ] Test service fallbacks (4.2)
- [ ] Add batch processing (5.2)
- [ ] Domain-specific tuning (future)

**Deliverables:**
- Production-hardened system
- Performance benchmarks
- Reduced hallucination rates

### Month 3: Advanced Features

**Week 9-10:**
- [ ] Implement RAGAS metrics
- [ ] Add continuous evaluation
- [ ] Create domain-specific datasets

**Week 11-12:**
- [ ] Fine-tune embeddings on domain data
- [ ] Implement vector quantization
- [ ] Production deployment

**Deliverables:**
- Advanced metrics dashboard
- Fine-tuned models
- Production deployment

## Success Metrics

### Month 1 Targets

| Metric | Current | Target | Success |
|--------|---------|--------|---------|
| Retrieval Recall@K | 0.0 (baseline) | 0.75 | Detect 75% of relevant docs |
| Hallucination Rate | 0.0 (baseline) | <0.20 | <20% of answers hallucinate |
| System Availability | 0.0 (baseline) | 0.95 | 95%+ uptime |
| Response Latency | 0.0 (baseline) | <3s | Answer in <3 seconds |

### Month 2 Targets

| Metric | Month 1 | Target | Improvement |
|--------|---------|--------|-------------|
| Retrieval Recall@K | 0.75 | 0.85 | +13% |
| Precision@K | 0.70 | 0.82 | +17% |
| Hallucination Rate | 0.20 | 0.08 | -60% |
| Citation Rate | 0.50 | 0.90 | +80% |
| Response Latency | 2.5s | 1.2s | -52% |

### Month 3 Targets

| Metric | Month 2 | Target | Status |
|--------|---------|--------|--------|
| Overall Quality (RAGAS) | N/A | >0.85 | Domain-specific |
| Production Availability | 0.95 | 0.99 | 99% uptime |
| User Satisfaction | N/A | >4.0/5 | Community feedback |

## Risk Mitigation

### Potential Risks

**Risk 1: Embedding Model Changes Break Existing Embeddings**
- *Mitigation:* Parallel run both models, test thoroughly before switching
- *Timeline:* 2 weeks testing before cutover
- *Rollback:* Keep old model indexed as backup

**Risk 2: Prompt Changes Alter Behavior Unexpectedly**
- *Mitigation:* A/B test new prompts on subset, measure impact
- *Timeline:* Run on 25 questions first
- *Rollback:* Easy - revert prompt text

**Risk 3: Service Fallbacks Add Latency**
- *Mitigation:* Design fallback logic to skip if primary available
- *Timeline:* Measure fallback path latency independently
- *Rollback:* Disable fallbacks, use primary only

**Risk 4: Performance Tuning Causes Regressions**
- *Mitigation:* Full evaluation suite before/after each change
- *Timeline:* Run all 100 questions before deployment
- *Rollback:* Version control all changes, revert if needed

## Budget & Resource Allocation

### Development Effort

| Phase | Dev Hours | Tester Hours | Total | Team |
|-------|-----------|--------------|-------|------|
| Month 1 | 80 | 20 | 100 | 1-2 engineers |
| Month 2 | 60 | 15 | 75 | 1-2 engineers |
| Month 3 | 40 | 10 | 50 | 1 engineer |

### Infrastructure Costs

| Component | Current | Estimated | Notes |
|-----------|---------|-----------|-------|
| Vector Store | ChromaDB (local) | Scales with data | +$0 (local) |
| LLM Service | Ollama (local) | GPU cost | +$0 (local GPU) |
| Caching | None | Redis | +$50-100/mo |
| Monitoring | Logs only | APM tool | +$100-200/mo |

## Conclusion & Action Items

### Immediate Actions (This Week)

1. ✅ **Integration:** Connect evaluation framework to live RAG service
2. ✅ **Baseline:** Run 100-question evaluation, document results
3. ✅ **Analysis:** Review failed examples, identify patterns
4. ✅ **Planning:** Prioritize fixes based on impact/effort

### Next Steps (Next 2 Weeks)

1. **Testing:** Evaluate embedding models, chunk parameters
2. **Implementation:** Quick-win fixes (prompt engineering, caching)
3. **Validation:** Re-run evaluation, measure improvement
4. **Deployment:** Roll out improvements to production

### Long-term Vision

- Continuous evaluation pipeline
- Automated metrics tracking
- Domain-specific optimization
- Multi-language support (future)
- Advanced RAG techniques (Graph-RAG, etc.)

---

**RAG Pipeline Improvement Recommendations | Version: 1.0 | 2026-01-06**

*This roadmap is based on the comprehensive RAG evaluation framework and provides a data-driven approach to systematic improvement. Priorities should be adjusted based on actual evaluation results.*
