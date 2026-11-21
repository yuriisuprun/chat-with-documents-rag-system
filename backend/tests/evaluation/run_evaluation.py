"""
RAG Evaluation Runner.

Executes comprehensive evaluation and generates reports.

Usage:
    cd backend
    python -m pytest tests/evaluation/run_evaluation.py -v -s
    
    Or directly:
    python tests/evaluation/run_evaluation.py
"""

import json
import sys
from pathlib import Path
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.logging import get_logger
from tests.evaluation.rag_evaluator import RAGEvaluator, run_rag_evaluation

logger = get_logger(__name__)


def generate_evaluation_reports(results: dict, output_dir: str = "backend/tests/evaluation") -> None:
    """
    Generate evaluation reports.
    
    Args:
        results: Evaluation results from evaluator
        output_dir: Directory to save reports
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save full results JSON
    results_json_path = output_path / "evaluation_results.json"
    with open(results_json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved results to {results_json_path}")
    
    # Generate markdown reports
    generate_evaluation_results_report(results, output_path)
    generate_failed_examples_report(results, output_path)
    generate_recommendations_report(results, output_path)


def generate_evaluation_results_report(results: dict, output_dir: Path) -> None:
    """Generate comprehensive evaluation results report."""
    report_path = output_dir / "RAG_EVALUATION_RESULTS.md"
    
    summary = results.get("summary", {})
    retrieval = results.get("retrieval_metrics", {})
    quality = results.get("quality_metrics", {})
    categories = results.get("category_breakdown", {})
    
    report = """# RAG Pipeline Evaluation Results

**Evaluation Date:** {timestamp}

## Executive Summary

### Overall Performance
- **Total Questions Evaluated:** {total_questions}
- **Passed (Score ≥ 0.7):** {passed} ({pass_rate:.1%})
- **Failed (Score < 0.7):** {failed}
- **Errors:** {errors}

### Key Metrics
- **Average Retrieval Recall@K:** {avg_recall:.3f}
- **Average Retrieval Precision@K:** {avg_precision:.3f}
- **Average MRR (Mean Reciprocal Rank):** {avg_mrr:.3f}
- **Average Faithfulness Score:** {avg_faithfulness:.3f}
- **Average Relevance Score:** {avg_relevance:.3f}
- **Hallucination Rate:** {hallucination_rate:.1%}
- **Citation Rate:** {citation_rate:.1%}

## Detailed Metrics

### Retrieval Quality

The retrieval phase is critical for RAG quality. These metrics measure how well the vector search finds relevant documents.

- **Recall@K (0.0-1.0):** Measures what fraction of relevant chunks were retrieved
  - Target: > 0.80 for production
  - Current: {avg_recall:.3f}
  - {recall_status}
  
- **Precision@K (0.0-1.0):** Measures what fraction of retrieved chunks are actually relevant
  - Target: > 0.75 for production
  - Current: {avg_precision:.3f}
  - {precision_status}
  
- **Mean Reciprocal Rank (0.0-1.0):** Measures how quickly the first relevant result appears
  - Target: > 0.70 for production
  - Current: {avg_mrr:.3f}
  - {mrr_status}

### Answer Quality

Measures generated answer faithfulness and relevance to query.

- **Faithfulness (0.0-1.0):** Indicates answers are grounded in retrieved context
  - Target: > 0.85 for production
  - Current: {avg_faithfulness:.3f}
  - {faithfulness_status}
  
- **Relevance (0.0-1.0):** Indicates answers address the user's question
  - Target: > 0.80 for production
  - Current: {avg_relevance:.3f}
  - {relevance_status}
  
- **Hallucination Rate (0.0-1.0):** Fraction of answers with unsupported claims
  - Target: < 0.10 for production
  - Current: {hallucination_rate:.1%}
  - {hallucination_status}
  
- **Citation Rate (0.0-1.0):** Fraction of answers with source attribution
  - Target: > 0.90 for production
  - Current: {citation_rate:.1%}
  - {citation_status}

## Performance by Category

{category_section}

## Findings & Analysis

### Strengths
- {strengths}

### Weaknesses
- {weaknesses}

### System Bottlenecks
1. **Retrieval Quality:** {retrieval_analysis}
2. **Answer Generation:** {generation_analysis}
3. **Context Assembly:** {context_analysis}
4. **Error Handling:** {error_analysis}

## Recommendations

1. **Retrieval Optimization:**
   - Tune embedding model for domain specificity
   - Optimize chunk size and overlap for better context
   - Implement query expansion and reformulation

2. **Answer Quality:**
   - Improve prompt engineering for more faithful responses
   - Add post-processing to filter hallucinations
   - Enhance citation formatting and accuracy

3. **System Reliability:**
   - Implement fallback retrieval strategies
   - Add result validation layer
   - Improve error recovery mechanisms

4. **Evaluation Metrics:**
   - Add RAGAS (Retrieval-Augmented Generation Assessment) metrics
   - Implement semantic similarity evaluation
   - Track user satisfaction feedback

## Test Coverage by Difficulty

- **Easy Questions:** {easy_count} ({easy_pass:.1%} pass rate)
- **Medium Questions:** {medium_count} ({medium_pass:.1%} pass rate)
- **Hard Questions:** {hard_count} ({hard_pass:.1%} pass rate)

## Next Steps

1. Address failed questions with highest impact first
2. Focus on retrieval quality improvements
3. Implement advanced evaluation metrics (RAGAS, semantic similarity)
4. Set up continuous evaluation in CI/CD pipeline
5. Monitor production metrics against baselines

---

*Report generated by RAG Evaluation Framework*
""".format(
        timestamp=results.get("timestamp", "Unknown"),
        total_questions=summary.get("total_questions", 0),
        passed=summary.get("passed", 0),
        failed=summary.get("failed", 0),
        errors=summary.get("errors", 0),
        pass_rate=summary.get("pass_rate", 0.0),
        avg_recall=retrieval.get("avg_recall_at_k", 0.0),
        avg_precision=retrieval.get("avg_precision_at_k", 0.0),
        avg_mrr=retrieval.get("avg_mrr", 0.0),
        avg_faithfulness=quality.get("avg_faithfulness", 0.0),
        avg_relevance=quality.get("avg_relevance", 0.0),
        hallucination_rate=quality.get("hallucination_rate", 0.0),
        citation_rate=quality.get("citation_rate", 0.0),
        recall_status="✅ GOOD" if retrieval.get("avg_recall_at_k", 0.0) > 0.80 else "⚠️ NEEDS IMPROVEMENT",
        precision_status="✅ GOOD" if retrieval.get("avg_precision_at_k", 0.0) > 0.75 else "⚠️ NEEDS IMPROVEMENT",
        mrr_status="✅ GOOD" if retrieval.get("avg_mrr", 0.0) > 0.70 else "⚠️ NEEDS IMPROVEMENT",
        faithfulness_status="✅ EXCELLENT" if quality.get("avg_faithfulness", 0.0) > 0.85 else "⚠️ NEEDS IMPROVEMENT",
        relevance_status="✅ GOOD" if quality.get("avg_relevance", 0.0) > 0.80 else "⚠️ NEEDS IMPROVEMENT",
        hallucination_status="✅ LOW" if quality.get("hallucination_rate", 0.0) < 0.10 else "⚠️ HIGH",
        citation_status="✅ GOOD" if quality.get("citation_rate", 0.0) > 0.90 else "⚠️ NEEDS IMPROVEMENT",
        category_section=_format_category_breakdown(categories),
        strengths=_analyze_strengths(results),
        weaknesses=_analyze_weaknesses(results),
        retrieval_analysis=_analyze_retrieval(results),
        generation_analysis=_analyze_generation(results),
        context_analysis=_analyze_context(results),
        error_analysis=_analyze_errors(results),
        easy_count=_count_by_difficulty(results, "easy"),
        easy_pass=_pass_rate_by_difficulty(results, "easy"),
        medium_count=_count_by_difficulty(results, "medium"),
        medium_pass=_pass_rate_by_difficulty(results, "medium"),
        hard_count=_count_by_difficulty(results, "hard"),
        hard_pass=_pass_rate_by_difficulty(results, "hard"),
    )
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"Saved evaluation report to {report_path}")


def generate_failed_examples_report(results: dict, output_dir: Path) -> None:
    """Generate failed examples analysis."""
    report_path = output_dir / "RAG_FAILED_EXAMPLES.md"
    
    detailed = results.get("detailed_results", [])
    
    # Sort by score
    failed = sorted([r for r in detailed if r.get("overall_score", 0) < 0.7], 
                   key=lambda x: x.get("overall_score", 0))[:15]
    
    report = """# RAG Pipeline Failed Examples Analysis

**Total Failed Examples:** {total_failed}

## Detailed Failure Cases

{examples}

## Root Cause Analysis

### Common Failure Patterns

{patterns}

### By Category

{category_analysis}

## Mitigation Strategies

1. **Retrieval Failures:** Implement embedding model tuning, query expansion
2. **Generation Failures:** Add response validation, confidence scoring
3. **Context Issues:** Improve chunk assembly and context windowing
4. **Citation Errors:** Enhance source tracking and attribution

---

*Report generated by RAG Evaluation Framework*
""".format(
        total_failed=len(failed),
        examples=_format_failed_examples(failed),
        patterns=_analyze_failure_patterns(failed),
        category_analysis=_analyze_category_failures(failed),
    )
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"Saved failed examples report to {report_path}")


def generate_recommendations_report(results: dict, output_dir: Path) -> None:
    """Generate prioritized recommendations."""
    report_path = output_dir / "RAG_RECOMMENDATIONS.md"
    
    summary = results.get("summary", {})
    retrieval = results.get("retrieval_metrics", {})
    quality = results.get("quality_metrics", {})
    
    pass_rate = summary.get("pass_rate", 0.0)
    
    report = """# RAG Pipeline Improvement Recommendations

**Current Pass Rate:** {pass_rate:.1%}
**Production Target:** 95%+ pass rate

## Priority 1: Critical Issues (Implement First)

### 1.1 Retrieval Quality Improvement
**Impact:** HIGH | **Effort:** MEDIUM | **Priority:** 🔴 CRITICAL

Current recall@k: {avg_recall:.3f} (Target: > 0.80)
Current precision@k: {avg_precision:.3f} (Target: > 0.75)

**Actions:**
1. Evaluate embedding models:
   - Current: sentence-transformers/all-MiniLM-L6-v2
   - Test: all-mpnet-base-v2 (better quality, slower)
   - Test: all-MiniLM-L12-v2 (better quality)
2. Optimize chunking strategy:
   - Experiment with chunk_size: 500-1500 chars
   - Test overlap: 50-200 chars
   - Implement semantic boundaries (sentence/paragraph splits)
3. Implement query expansion:
   - Paraphrase user queries before embedding
   - Add query reformulation for ambiguous questions
4. Add hybrid search:
   - Combine dense (embedding) + sparse (BM25) retrieval
   - Rerank results using cross-encoder models

**Expected Impact:** +15-25% improvement in recall and precision

### 1.2 Hallucination Reduction
**Impact:** HIGH | **Effort:** LOW | **Priority:** 🔴 CRITICAL

Current hallucination rate: {hallucination_rate:.1%} (Target: < 0.10)

**Actions:**
1. Implement prompt engineering improvements:
   - Add explicit constraint: "Only answer based on provided context"
   - Include confidence instructions: "Say 'I don't know' if uncertain"
   - Add format specification for citations
2. Add post-processing validation:
   - Check answer doesn't contradict retrieved context
   - Validate all claims have supporting evidence
   - Strip unsupported generalizations
3. Implement retrieval sufficiency check (already in pipeline):
   - Verify context covers query before generation
   - Reject low-confidence contexts

**Expected Impact:** -50-70% hallucination rate

## Priority 2: Quality Improvements (Implement Second)

### 2.1 Citation Accuracy
**Impact:** MEDIUM | **Effort:** LOW | **Priority:** 🟠 HIGH

Current citation rate: {citation_rate:.1%} (Target: > 0.90)

**Actions:**
1. Enhance source extraction in RAG service:
   - Track which context chunks generated which sentences
   - Implement bidirectional chunk-to-answer mapping
   - Use NER to link entities to sources
2. Improve citation formatting:
   - Show document name + page number for each citation
   - Include confidence score for each source
   - Add text preview for user verification

**Expected Impact:** +30-40% better citations

### 2.2 Answer Relevance
**Impact:** MEDIUM | **Effort:** MEDIUM | **Priority:** 🟠 HIGH

Current relevance score: {avg_relevance:.3f} (Target: > 0.80)

**Actions:**
1. Implement answer validation:
   - Use semantic similarity to check answer addresses question
   - Add clarity check for jargon/terminology
   - Validate answer length (too short/long = worse)
2. Improve prompt templates:
   - Add explicit instruction to address all parts of question
   - Include examples of good/bad answers
   - Specify output format requirements
3. Add question understanding:
   - Classify question type (factual, comparative, explanatory)
   - Tailor prompt based on question type

**Expected Impact:** +15-20% better relevance

## Priority 3: System Reliability (Implement Third)

### 3.1 Error Handling & Recovery
**Impact:** MEDIUM | **Effort:** MEDIUM | **Priority:** 🟠 HIGH

Current error rate: {error_count} errors

**Actions:**
1. Implement graceful degradation:
   - If retrieval fails, provide raw documents
   - If LLM unavailable, return best matching chunk
   - Add timeout handling with fallbacks
2. Add detailed error logging:
   - Log full pipeline trace for every error
   - Include decision points and alternatives tried
   - Support debugging and root cause analysis
3. Implement retry strategies:
   - Retry failed embeddings with different model
   - Fallback to alternative LLM providers
   - Queue failed requests for later retry

**Expected Impact:** 99%+ system availability

### 3.2 Performance Optimization
**Impact:** LOW-MEDIUM | **Effort:** MEDIUM | **Priority:** 🟡 MEDIUM

**Actions:**
1. Implement caching:
   - Cache embeddings for frequent queries
   - Batch embedding requests for efficiency
   - Implement LRU cache for results
2. Optimize vector store:
   - Implement approximate nearest neighbor search
   - Use vector quantization for memory efficiency
   - Add indexing strategy tuning
3. Add async processing:
   - Parallelize embedding and retrieval
   - Implement background indexing
   - Add request queuing for bursty load

**Expected Impact:** 30-50% faster responses

## Priority 4: Advanced Features (Implement Fourth)

### 4.1 Advanced Evaluation Metrics
**Impact:** MEDIUM | **Effort:** HIGH | **Priority:** 🟡 MEDIUM

**Actions:**
1. Implement RAGAS metrics:
   - Faithfulness (0-1): Does answer contain only supported info
   - Answer relevance (0-1): Does answer address the question
   - Context recall (0-1): Does context cover all needed info
   - Context precision (0-1): Does context contain only relevant info
2. Add semantic similarity evaluation:
   - Compare generated answer to ground truth semantically
   - Measure semantic equivalence not string matching
   - Use embeddings for similarity computation
3. Implement user satisfaction metrics:
   - Add user feedback collection UI
   - Track helpful/unhelpful ratings
   - Build feedback loop for continuous improvement

**Expected Impact:** Better understanding of quality dimensions

### 4.2 Domain-Specific Tuning
**Impact:** HIGH | **Effort:** HIGH | **Priority:** 🟡 MEDIUM

**Actions:**
1. Fine-tune embedding models on domain data
2. Implement domain-specific prompt templates
3. Add domain-specific validations and checks
4. Create domain-specific evaluation datasets

**Expected Impact:** 20-40% improvement for specific domains

## Implementation Roadmap

### Month 1: Critical Fixes
- [ ] Retrieval quality improvements (embedding + chunking)
- [ ] Hallucination reduction (prompt + post-processing)
- [ ] Better error handling

### Month 2: Quality Improvements
- [ ] Citation accuracy enhancement
- [ ] Answer relevance improvement
- [ ] Performance optimization

### Month 3: Advanced Features
- [ ] RAGAS metrics implementation
- [ ] Caching layer
- [ ] Domain-specific tuning

## Success Metrics

| Metric | Current | Month 1 | Month 2 | Month 3 |
|--------|---------|---------|---------|---------|
| Pass Rate | {pass_rate:.1%} | 75% | 85% | 95%+ |
| Recall@K | {avg_recall:.3f} | 0.75 | 0.85 | 0.90+ |
| Precision@K | {avg_precision:.3f} | 0.70 | 0.80 | 0.85+ |
| Faithfulness | {avg_faithfulness:.3f} | 0.80 | 0.90 | 0.95+ |
| Hallucination Rate | {hallucination_rate:.1%} | 5% | 2% | < 1% |
| Citations | {citation_rate:.1%} | 75% | 90% | 95%+ |

## Cost-Benefit Analysis

### Quick Wins (Low Effort, High Impact)
1. Prompt engineering improvements: **2-4 hours → +10-15% quality**
2. Post-processing validation: **4-8 hours → -30-50% hallucinations**
3. Better error messages: **2-3 hours → +debugging efficiency**

### Medium Term (Medium Effort, High Impact)
1. Embedding model tuning: **1-2 weeks → +15-25% recall/precision**
2. Hybrid retrieval: **2-3 weeks → +20-30% quality**
3. Citation enhancement: **1-2 weeks → +30-40% citations**

### Long Term (High Effort, High Impact)
1. RAGAS metrics: **2-3 weeks → Better understanding**
2. Domain fine-tuning: **3-4 weeks → Domain-specific excellence**
3. ML-based ranking: **4-6 weeks → Advanced optimization**

## Monitoring & Metrics

### Real-time Monitoring
- Daily pass rate tracking
- Error rate by type
- Average retrieval latency
- Hallucination rate trending

### Evaluation Cadence
- Weekly: Run full evaluation suite
- Monthly: Review metrics and adjust strategy
- Quarterly: Update embedding/LLM models
- Annually: Major architecture review

---

*Recommendations generated by RAG Evaluation Framework*
""".format(
        pass_rate=pass_rate,
        avg_recall=retrieval.get("avg_recall_at_k", 0.0),
        avg_precision=retrieval.get("avg_precision_at_k", 0.0),
        hallucination_rate=quality.get("hallucination_rate", 0.0),
        citation_rate=quality.get("citation_rate", 0.0),
        avg_relevance=quality.get("avg_relevance", 0.0),
        avg_faithfulness=quality.get("avg_faithfulness", 0.0),
        error_count=summary.get("errors", 0),
    )
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"Saved recommendations report to {report_path}")


# Helper functions
def _format_category_breakdown(categories: dict) -> str:
    """Format category breakdown for report."""
    if not categories:
        return "No category data"
    
    lines = []
    for cat, stats in categories.items():
        lines.append(f"""
### {cat.replace('_', ' ').title()}
- Count: {stats.get('count', 0)} questions
- Pass Rate: {stats.get('pass_rate', 0):.1%}
- Avg Score: {stats.get('avg_score', 0):.3f}
- Avg Recall: {stats.get('avg_retrieval_recall', 0):.3f}
- Avg Faithfulness: {stats.get('avg_faithfulness', 0):.3f}
""")
    return "\n".join(lines)


def _format_failed_examples(failed: list) -> str:
    """Format failed examples."""
    if not failed:
        return "No failed examples"
    
    lines = []
    for i, result in enumerate(failed, 1):
        lines.append(f"""
### Example {i}: {result.get('question_id', 'Unknown')}

**Question:** {result.get('question', '')[:100]}...

**Expected:** {result.get('expected_answer', '')[:100]}...

**Generated:** {result.get('generated_answer', '')[:100] if result.get('generated_answer') else 'ERROR'}...

**Score:** {result.get('overall_score', 0):.3f}

**Metrics:**
- Recall@K: {result.get('retrieval_metrics', {}).get('recall_at_k', 0):.3f}
- Faithfulness: {result.get('quality_metrics', {}).get('faithfulness_score', 0):.3f}
- Hallucinated: {result.get('quality_metrics', {}).get('is_hallucinated', False)}

**Error:** {result.get('error', 'None')}
""")
    return "\n".join(lines[:15])


def _analyze_failure_patterns(failed: list) -> str:
    """Analyze failure patterns."""
    if not failed:
        return "No failures"
    
    patterns = {
        "low_recall": sum(1 for r in failed if r.get('retrieval_metrics', {}).get('recall_at_k', 0) < 0.5),
        "hallucinated": sum(1 for r in failed if r.get('quality_metrics', {}).get('is_hallucinated', False)),
        "no_answer": sum(1 for r in failed if not r.get('generated_answer')),
        "low_citations": sum(1 for r in failed if not r.get('quality_metrics', {}).get('has_citations', False)),
    }
    
    return f"""
- Low Retrieval Recall: {patterns['low_recall']} failures
- Hallucinated Content: {patterns['hallucinated']} failures
- No Answer Generated: {patterns['no_answer']} failures
- Missing Citations: {patterns['low_citations']} failures
"""


def _analyze_category_failures(failed: list) -> str:
    """Analyze failures by category."""
    by_category = {}
    for f in failed:
        cat = f.get('category', 'unknown')
        if cat not in by_category:
            by_category[cat] = 0
        by_category[cat] += 1
    
    lines = []
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        lines.append(f"- **{cat.replace('_', ' ').title()}:** {count} failures")
    
    return "\n".join(lines) if lines else "No category data"


def _analyze_strengths(results: dict) -> str:
    """Analyze strengths."""
    quality = results.get("quality_metrics", {})
    retrieval = results.get("retrieval_metrics", {})
    pass_rate = results.get("summary", {}).get("pass_rate", 0)
    
    strengths = []
    if pass_rate > 0.6:
        strengths.append(f"Good overall pass rate ({pass_rate:.1%})")
    if quality.get("avg_faithfulness", 0) > 0.75:
        strengths.append("Strong answer faithfulness")
    if retrieval.get("avg_recall_at_k", 0) > 0.7:
        strengths.append("Good retrieval recall")
    if quality.get("citation_rate", 0) > 0.8:
        strengths.append("Good citation coverage")
    
    return " | ".join(strengths) if strengths else "Limited strengths identified"


def _analyze_weaknesses(results: dict) -> str:
    """Analyze weaknesses."""
    quality = results.get("quality_metrics", {})
    retrieval = results.get("retrieval_metrics", {})
    
    weaknesses = []
    if quality.get("hallucination_rate", 0) > 0.15:
        weaknesses.append(f"High hallucination rate ({quality.get('hallucination_rate', 0):.1%})")
    if retrieval.get("avg_recall_at_k", 0) < 0.65:
        weaknesses.append(f"Low retrieval recall ({retrieval.get('avg_recall_at_k', 0):.3f})")
    if quality.get("avg_relevance", 0) < 0.7:
        weaknesses.append(f"Low answer relevance ({quality.get('avg_relevance', 0):.3f})")
    if quality.get("citation_rate", 0) < 0.7:
        weaknesses.append(f"Poor citation rate ({quality.get('citation_rate', 0):.1%})")
    
    return " | ".join(weaknesses) if weaknesses else "Good overall quality"


def _analyze_retrieval(results: dict) -> str:
    """Analyze retrieval performance."""
    retrieval = results.get("retrieval_metrics", {})
    recall = retrieval.get("avg_recall_at_k", 0)
    
    if recall > 0.85:
        return "Excellent retrieval quality. Minor optimizations possible."
    elif recall > 0.70:
        return "Good retrieval quality. Focus on improving embedding model and chunk strategy."
    else:
        return "Retrieval needs significant improvement. Consider hybrid search and query expansion."


def _analyze_generation(results: dict) -> str:
    """Analyze generation performance."""
    quality = results.get("quality_metrics", {})
    faithfulness = quality.get("avg_faithfulness", 0)
    hallucination = quality.get("hallucination_rate", 0)
    
    if faithfulness > 0.85 and hallucination < 0.1:
        return "Strong generation quality. Minor prompt refinements recommended."
    elif faithfulness > 0.75:
        return "Good generation quality. Focus on reducing hallucinations via post-processing."
    else:
        return "Generation needs improvement. Implement stricter validation and better prompting."


def _analyze_context(results: dict) -> str:
    """Analyze context assembly."""
    summary = results.get("summary", {})
    errors = summary.get("errors", 0)
    
    if errors == 0:
        return "Context assembly working reliably. No issues detected."
    else:
        return f"Context assembly has {errors} errors. Improve error handling and fallbacks."


def _analyze_errors(results: dict) -> str:
    """Analyze error patterns."""
    summary = results.get("summary", {})
    errors = summary.get("errors", 0)
    total = summary.get("total_questions", 1)
    error_rate = errors / max(total, 1)
    
    if error_rate < 0.01:
        return "Excellent reliability with minimal errors."
    elif error_rate < 0.05:
        return f"Good reliability. {error_rate:.1%} error rate. Monitor and address outliers."
    else:
        return f"High error rate ({error_rate:.1%}). Systematic issues need investigation."


def _count_by_difficulty(results: dict, difficulty: str) -> int:
    """Count questions by difficulty."""
    detailed = results.get("detailed_results", [])
    return len([r for r in detailed if r.get("difficulty") == difficulty])


def _pass_rate_by_difficulty(results: dict, difficulty: str) -> float:
    """Calculate pass rate by difficulty."""
    detailed = results.get("detailed_results", [])
    by_difficulty = [r for r in detailed if r.get("difficulty") == difficulty]
    
    if not by_difficulty:
        return 0.0
    
    passed = len([r for r in by_difficulty if r.get("overall_score", 0) >= 0.7])
    return passed / len(by_difficulty)


def main():
    """Run evaluation and generate reports."""
    logger.info("Starting RAG Evaluation...")
    
    try:
        # Run evaluation (with mocked service for demonstration)
        results = run_rag_evaluation(
            rag_service=None,  # Would normally pass real service
            max_questions=100,
        )
        
        # Generate reports
        generate_evaluation_reports(results)
        
        logger.info("✅ Evaluation completed successfully")
        logger.info(f"Pass Rate: {results.get('summary', {}).get('pass_rate', 0):.1%}")
        logger.info("Reports saved to backend/tests/evaluation/")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
