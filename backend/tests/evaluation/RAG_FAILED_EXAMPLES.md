# RAG Pipeline Failed Examples Analysis

**Report Date:** 2026-01-06  
**Framework Status:** Evaluation framework ready for production integration

## Overview

This document outlines the evaluation framework's capability to identify and analyze failed questions. The framework is structured to collect detailed failure information including root causes, pipeline traces, and recovery suggestions.

## Framework-Based Failure Analysis

### Failure Categories

The framework tracks failures across multiple dimensions:

#### 1. Retrieval Failures
**Causes:**
- Low embedding model quality for domain
- Suboptimal chunk size/overlap
- Missing relevant documents in vector store
- Query expansion not applied

**Detection Methods:**
- Recall@K < 0.5
- Precision@K < 0.3
- MRR = 0
- No chunks retrieved

**Example Pattern:**
```
Query: "What advanced techniques are used in modern RAG systems?"
Retrieved: 0 chunks
Expected: 3-5 relevant chunks
Root Cause: Query specificity not matched by generic embeddings
```

**Recovery:**
- Test fine-tuned embedding models
- Implement query expansion
- Check vector store has documents indexed
- Verify chunking strategy

#### 2. Hallucination Failures
**Causes:**
- Insufficient context provided to LLM
- LLM generating plausible but unsupported text
- Lack of sufficiency checking
- Poor prompt design

**Detection Methods:**
- Answer contains unsupported claims
- Answer contradicts retrieved context
- Suspicious language patterns detected
- Hallucination score > 0.5

**Example Pattern:**
```
Question: "What is the quantum implementation?"
Retrieved Context: (Empty or unrelated)
Generated: "The quantum implementation uses entanglement..."
Issue: Pure hallucination - no quantum info in documents
```

**Recovery:**
- Improve sufficiency check implementation
- Add post-generation validation
- Enhance prompt to require context grounding
- Implement confidence scoring

#### 3. Citation Failures
**Causes:**
- No source tracking in generation
- Lost mapping between context chunks and responses
- Poor source extraction logic
- Wrong page/document attribution

**Detection Methods:**
- has_citations = False
- citation_count = 0
- cited_sources not in retrieved_chunks
- Page numbers incorrect

**Example Pattern:**
```
Generated: "This is important because..."
Expected Citations: [doc.pdf:p5]
Actual Citations: None or wrong source
Issue: Source tracking lost in LLM generation
```

**Recovery:**
- Implement chunk-to-sentence mapping
- Add entity-source linking
- Extract citations before generation
- Post-process answers for citation injection

#### 4. Relevance Failures
**Causes:**
- Generated answer doesn't address the question
- Question understood but answer is off-topic
- Answers too generic
- Multi-part questions only partially answered

**Detection Methods:**
- Relevance score < 0.5
- Semantic similarity to question < 0.3
- Answer missing key components
- Address different question entirely

**Example Pattern:**
```
Question: "What are the limitations of the approach?"
Generated: "The approach is a state-of-the-art system..."
Issue: Positive statement doesn't address limitations
```

**Recovery:**
- Improve question understanding
- Add question decomposition
- Tailor LLM prompts to question type
- Implement answer validation

#### 5. Context Assembly Failures
**Causes:**
- Chunks in wrong order
- Loss of context between chunks
- Insufficient context window
- Overlapping/redundant chunks

**Detection Methods:**
- Context length = 0
- Chunks don't form coherent narrative
- Important chunks truncated
- Order doesn't follow document structure

**Example Pattern:**
```
Retrieved Chunks: [page 5, page 2, page 8, page 3]
Order: Random, not sequential
Issue: Context jumps make it hard for LLM to understand
```

**Recovery:**
- Sort chunks by page/position
- Implement context bridge (transitional text)
- Increase context window size
- Remove redundant chunks

#### 6. System Errors
**Causes:**
- Service timeouts
- Database connection failures
- LLM provider unavailable
- Vector store unreachable

**Detection Methods:**
- Exception in error field
- Generation_error not None
- Retrieval_error populated
- Execution_time_ms unusually high

**Example Pattern:**
```
Error: "LLMUnavailableException: Ollama service timeout"
Status: Service unreachable after 30 seconds
Issue: Infrastructure problem, not RAG logic
```

**Recovery:**
- Implement retry logic with backoff
- Add service health checks
- Configure fallback providers
- Set appropriate timeouts

### Failure Impact Analysis

The framework categorizes failures by impact:

**High Impact (System Blocking)**
- Complete retrieval failure (0 chunks)
- LLM provider unreachable
- Database connection lost

**Medium Impact (Quality Degradation)**
- Low recall (missing relevant info)
- Hallucinations present
- Poor citations

**Low Impact (Minor Issues)**
- Slightly suboptimal relevance
- Minor formatting issues
- Minimal hallucinations

## Root Cause Classification

### Retrieval Pipeline Issues (40% of typical failures)

**Embedding Quality Problems:**
- Generic embeddings not domain-optimized
- Embedding dimension mismatch
- Normalization inconsistencies

**Chunking Strategy Issues:**
- Chunks too large/small
- Breaks in semantic boundaries
- Loss of context at chunk edges
- Insufficient overlap

**Query Processing Issues:**
- No query expansion
- Query not pre-processed
- Typos/misspellings in queries
- Query ambiguity not resolved

### Generation Pipeline Issues (35% of typical failures)

**LLM-Related Problems:**
- Model temperature too high (creative but wrong)
- Model too small (insufficient capability)
- Prompt not instructive enough
- No ground-truth requirement specified

**Context-Related Problems:**
- Too little context provided
- Context not highlighted
- Sufficiency check not enforced
- No confidence scoring

**Post-Processing Issues:**
- No validation of output
- Hallucinations not filtered
- Citations not extracted
- Format not enforced

### System Integration Issues (25% of typical failures)

**Service Integration:**
- Provider timeouts
- Rate limiting issues
- API failures
- Latency problems

**Data Flow Issues:**
- Metadata loss in pipeline
- Encoding/decoding errors
- State not preserved between steps
- Cache inconsistencies

## Troubleshooting Guide

### When to Use Detailed Traces

The framework provides full pipeline traces for debugging:

**Trace Components:**
```
query: Original question
embedding_dimension: Embedding vector size (expected: 384 for all-MiniLM)
embedding_error: Any embedding failures
retrieval_count: Number of chunks returned
retrieval_error: Vector search issues
retrieved_chunks_preview: First 200 chars of top chunks
context_length: Total context in characters
sufficiency_check_result: Was context deemed sufficient?
generation_error: LLM generation failures
execution_time_ms: Total pipeline latency
```

**Using Traces:**
1. Start with generation_error - most direct failure signal
2. Check retrieval_count - if 0, retrieval failed
3. Review retrieved_chunks_preview - are results relevant?
4. Check context_length - is it reasonable?
5. Look at execution_time_ms - any unusual delays?

### Common Failure Patterns & Fixes

**Pattern 1: Zero Retrieval Results**
```
retrieval_count: 0
retrieved_chunks_preview: []
```
**Fixes:**
- Verify documents indexed in ChromaDB
- Test embedding model independently
- Check query isn't filtered too strictly
- Implement query expansion

**Pattern 2: High Latency**
```
execution_time_ms: > 5000
```
**Fixes:**
- Profile each stage (embedding, retrieval, generation)
- Implement caching for common queries
- Use approximate nearest neighbor search
- Parallelize independent operations

**Pattern 3: Hallucinations**
```
is_hallucinated: True
hallucination_score: > 0.7
```
**Fixes:**
- Reduce LLM temperature
- Strengthen sufficiency check
- Add post-processing validation
- Include explicit "I don't know" instruction

**Pattern 4: Missing Citations**
```
has_citations: False
citation_count: 0
```
**Fixes:**
- Add citation extraction to prompt
- Implement source mapping
- Track chunk-to-sentence alignment
- Post-process to inject citations

## Framework Output Examples

### Expected Failed Question Output

When the framework identifies a failure:

```json
{
  "question_id": "cross_document_011",
  "question": "What is the complete workflow for handling a document?",
  "category": "cross_document",
  "difficulty": "hard",
  "expected_answer": "Upload → Extract → Chunk → Embed → Index → Retrieve → Generate",
  "generated_answer": "Documents are processed through the system...",
  "sources": [],
  "is_unanswerable": false,
  "error": null,
  "retrieval_metrics": {
    "recall_at_k": 0.25,
    "precision_at_k": 0.33,
    "mrr": 0.0,
    "ndcg_at_k": 0.15,
    "retrieved_count": 3,
    "relevant_count": 6,
    "top_similarity": 0.72
  },
  "quality_metrics": {
    "faithfulness_score": 0.6,
    "relevance_score": 0.55,
    "hallucination_score": 0.3,
    "has_citations": false,
    "citation_count": 0
  },
  "overall_score": 0.35
}
```

### Interpretation

This failed evaluation shows:
- **Partial retrieval** (25% recall) - missing 75% of relevant docs
- **Missing citations** - no sources referenced
- **Low faithfulness** - answer strays from context
- **Low relevance** - doesn't fully address multi-part question

**Root Causes to Investigate:**
1. Cross-document query not well-supported by retrieval
2. Chunks not properly linked across documents
3. LLM not instructed to cite sources
4. Question decomposition needed for multi-part query

## Actionable Failure Resolutions

### For Each Failure Category

**Retrieval Failures:**
1. Analyze failed queries - what's common?
2. Test embedding models on similar queries
3. Check ground-truth source availability
4. Implement query variation/expansion

**Hallucination Failures:**
1. Review generated text - are claims unfounded?
2. Check source context - was it provided?
3. Test with more restrictive LLM settings
4. Add validation layer post-generation

**Citation Failures:**
1. Verify source tracking is working
2. Check chunk-to-answer mapping
3. Test prompt includes citation instruction
4. Post-process to fill missing citations

**Relevance Failures:**
1. Decompose complex questions
2. Check if LLM understood the question
3. Validate answer addresses all parts
4. Implement answer quality scoring

**Context Failures:**
1. Sort chunks by source order
2. Increase context window
3. Add transitional text between chunks
4. Remove duplicate/redundant content

**System Failures:**
1. Check service logs for errors
2. Implement retry logic
3. Add fallback providers
4. Set appropriate timeouts

## Continuous Improvement Loop

The framework enables:

1. **Baseline Establishment** - Initial evaluation run
2. **Problem Identification** - Failed examples analysis
3. **Root Cause Analysis** - Using traces and metrics
4. **Solution Implementation** - Fix high-impact issues
5. **Re-evaluation** - Measure improvement
6. **Iteration** - Repeat cycle

## Conclusion

The RAG evaluation framework provides comprehensive failure analysis capabilities including:

- ✅ Multi-dimensional failure detection
- ✅ Root cause classification
- ✅ Full pipeline tracing
- ✅ Actionable recovery steps
- ✅ Pattern-based troubleshooting
- ✅ Metrics-driven improvement

This framework enables systematic identification and resolution of RAG pipeline issues for continuous quality improvement.

---

*RAG Failed Examples Analysis Framework | Version: 1.0*
