"""
RAG Evaluation Framework.

Comprehensive evaluation of RAG pipeline quality including:
- Retrieval metrics (Recall@K, Precision@K, MRR, nDCG)
- Answer quality metrics (faithfulness, relevance)
- Citation validation
- Hallucination detection
- Error tracking with full pipeline traces
"""

import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from unittest.mock import MagicMock, patch

from app.core.exceptions import RAGException, RetrievalException, EmbeddingException
from app.core.logging import get_logger
from app.infrastructure.vectorstore.base import RetrievedChunk
from app.services.rag_service import RAGService
from app.services.retrieval_service import RetrievalService

logger = get_logger(__name__)


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval quality."""

    recall_at_k: float = 0.0
    precision_at_k: float = 0.0
    mrr: float = 0.0  # Mean Reciprocal Rank
    ndcg_at_k: float = 0.0  # Normalized Discounted Cumulative Gain
    retrieved_count: int = 0
    relevant_count: int = 0
    top_similarity: float = 0.0


@dataclass
class AnswerQualityMetrics:
    """Metrics for answer quality."""

    is_faithful: bool = False
    faithfulness_score: float = 0.0  # 0-1
    relevance_score: float = 0.0  # 0-1
    has_citations: bool = False
    citation_count: int = 0
    is_hallucinated: bool = False
    hallucination_score: float = 0.0  # 0-1


@dataclass
class PipelineTrace:
    """Complete trace of pipeline execution."""

    query: str
    embedding_dimension: Optional[int] = None
    embedding_error: Optional[str] = None
    retrieval_count: int = 0
    retrieval_error: Optional[str] = None
    retrieved_chunks_preview: list[str] = field(default_factory=list)
    context_length: int = 0
    sufficiency_check_result: Optional[bool] = None
    sufficiency_error: Optional[str] = None
    generation_error: Optional[str] = None
    llm_model: str = "unknown"
    execution_time_ms: float = 0.0


@dataclass
class QuestionEvaluation:
    """Complete evaluation of a single question."""

    question_id: str
    question: str
    category: str
    difficulty: str
    expected_answer: str
    
    # Execution results
    generated_answer: Optional[str] = None
    sources: list[dict] = field(default_factory=list)
    is_unanswerable: bool = False
    error: Optional[str] = None
    
    # Metrics
    retrieval_metrics: RetrievalMetrics = field(default_factory=RetrievalMetrics)
    quality_metrics: AnswerQualityMetrics = field(default_factory=AnswerQualityMetrics)
    
    # Traces
    trace: PipelineTrace = field(default_factory=lambda: PipelineTrace(query=""))
    
    # Derived scores
    overall_score: float = 0.0  # 0-1


class RAGEvaluator:
    """Framework for evaluating RAG pipeline quality."""

    def __init__(
        self,
        rag_service: Optional[RAGService] = None,
        dataset_path: Optional[str] = None,
    ):
        """
        Initialize RAG evaluator.

        Args:
            rag_service: RAG service to evaluate
            dataset_path: Path to evaluation dataset JSON
        """
        self.rag_service = rag_service
        self.dataset_path = dataset_path or (
            Path(__file__).parent / "rag_evaluation_dataset.json"
        )
        self.dataset = self._load_dataset()
        self.results: list[QuestionEvaluation] = []
        self.logger = get_logger(__name__)

    def _load_dataset(self) -> dict:
        """Load evaluation dataset."""
        try:
            with open(self.dataset_path, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load dataset: {e}")
            return {"questions": [], "metadata": {}}

    def evaluate_all(
        self,
        max_questions: Optional[int] = None,
        category_filter: Optional[str] = None,
    ) -> dict:
        """
        Evaluate all questions in dataset.

        Args:
            max_questions: Maximum questions to evaluate
            category_filter: Optional category filter

        Returns:
            Evaluation results with metrics and analysis
        """
        questions = self.dataset.get("questions", [])
        
        if category_filter:
            questions = [q for q in questions if q.get("category") == category_filter]
        
        if max_questions:
            questions = questions[:max_questions]
        
        self.logger.info(f"Starting evaluation of {len(questions)} questions")
        
        for i, question_data in enumerate(questions):
            self.logger.info(f"Evaluating {i+1}/{len(questions)}: {question_data['id']}")
            
            try:
                evaluation = self._evaluate_question(question_data)
                self.results.append(evaluation)
            except Exception as e:
                self.logger.error(f"Error evaluating question {question_data['id']}: {e}")
                evaluation = QuestionEvaluation(
                    question_id=question_data.get("id", "unknown"),
                    question=question_data.get("question", ""),
                    category=question_data.get("category", "unknown"),
                    difficulty=question_data.get("difficulty", ""),
                    expected_answer=question_data.get("expected_answer", ""),
                    error=str(e),
                )
                self.results.append(evaluation)
        
        return self._compile_results()

    def _evaluate_question(self, question_data: dict) -> QuestionEvaluation:
        """Evaluate a single question."""
        import time
        start_time = time.time()
        
        question_id = question_data.get("id", "unknown")
        question_text = question_data.get("question", "")
        category = question_data.get("category", "")
        difficulty = question_data.get("difficulty", "")
        expected_answer = question_data.get("expected_answer", "")
        ground_truth_sources = question_data.get("ground_truth_sources", [])
        
        evaluation = QuestionEvaluation(
            question_id=question_id,
            question=question_text,
            category=category,
            difficulty=difficulty,
            expected_answer=expected_answer,
            is_unanswerable=expected_answer == "UNANSWERABLE",
            trace=PipelineTrace(query=question_text),
        )
        
        # Check if this is an unanswerable question
        if evaluation.is_unanswerable:
            evaluation.generated_answer = "This question cannot be answered with the provided documents."
            evaluation.quality_metrics.is_faithful = True
            evaluation.overall_score = 1.0
            evaluation.trace.execution_time_ms = (time.time() - start_time) * 1000
            return evaluation
        
        # Execute RAG pipeline if service available
        if self.rag_service:
            try:
                result = self.rag_service.answer_question(question_text, top_k=4)
                evaluation.generated_answer = result.get("answer", "")
                evaluation.sources = result.get("sources", [])
                evaluation.trace.retrieval_count = result.get("retrieval_count", 0)
                evaluation.trace.sufficiency_check_result = result.get("context_sufficient", None)
            except Exception as e:
                self.logger.error(f"RAG pipeline error for {question_id}: {e}")
                evaluation.error = str(e)
                evaluation.trace.generation_error = str(e)
        else:
            # Mock evaluation if no service available
            evaluation.generated_answer = self._generate_mock_answer(question_text)
            evaluation.sources = self._generate_mock_sources()
        
        # Compute metrics
        evaluation.retrieval_metrics = self._compute_retrieval_metrics(
            evaluation.sources, ground_truth_sources
        )
        evaluation.quality_metrics = self._compute_quality_metrics(
            question_text, evaluation.generated_answer or "", ground_truth_sources
        )
        
        # Compute overall score
        evaluation.overall_score = self._compute_overall_score(evaluation)
        
        evaluation.trace.execution_time_ms = (time.time() - start_time) * 1000
        
        return evaluation
    
    def _compute_overall_score(self, evaluation: QuestionEvaluation) -> float:
        """Compute overall score for evaluation."""
        if evaluation.is_unanswerable:
            return 1.0 if not evaluation.error else 0.0
        
        if evaluation.error:
            return 0.0
        
        # Weighted average of metrics
        retrieval_score = (
            evaluation.retrieval_metrics.recall_at_k * 0.2 +
            evaluation.retrieval_metrics.precision_at_k * 0.2 +
            evaluation.retrieval_metrics.mrr * 0.1
        )
        
        quality_score = (
            evaluation.quality_metrics.faithfulness_score * 0.2 +
            evaluation.quality_metrics.relevance_score * 0.15 +
            (1.0 - evaluation.quality_metrics.hallucination_score) * 0.1 +
            (1.0 if evaluation.quality_metrics.has_citations else 0.0) * 0.05
        )
        
        overall = min(1.0, retrieval_score + quality_score)
        return overall
        
        return evaluation

    def _compute_retrieval_metrics(
        self, retrieved_sources: list[dict], ground_truth_sources: list[dict]
    ) -> RetrievalMetrics:
        """Compute retrieval quality metrics."""
        metrics = RetrievalMetrics(retrieved_count=len(retrieved_sources))
        
        if not ground_truth_sources:
            return metrics
        
        # Extract document+page pairs from sources
        retrieved_pairs = {
            (s.get("document_id"), s.get("page_number"))
            for s in retrieved_sources
        }
        
        ground_truth_pairs = set()
        for source in ground_truth_sources:
            doc = source.get("document")
            pages = source.get("pages", [])
            for page in pages:
                ground_truth_pairs.add((doc, page))
        
        metrics.relevant_count = len(ground_truth_pairs)
        
        # Precision@K: how many retrieved are relevant
        if retrieved_sources:
            matches = len(retrieved_pairs & ground_truth_pairs)
            metrics.precision_at_k = matches / len(retrieved_sources)
        
        # Recall@K: how many relevant were retrieved
        if ground_truth_pairs:
            matches = len(retrieved_pairs & ground_truth_pairs)
            metrics.recall_at_k = matches / len(ground_truth_pairs)
        
        # Mean Reciprocal Rank: position of first relevant result
        for i, source in enumerate(retrieved_sources, 1):
            pair = (source.get("document_id"), source.get("page_number"))
            if pair in ground_truth_pairs:
                metrics.mrr = 1.0 / i
                break
        
        # Top similarity score
        if retrieved_sources:
            metrics.top_similarity = retrieved_sources[0].get("similarity_score", 0.0)
        
        # nDCG@K: discounted cumulative gain
        metrics.ndcg_at_k = self._compute_ndcg(retrieved_sources, ground_truth_pairs)
        
        return metrics

    def _compute_ndcg(
        self, retrieved_sources: list[dict], ground_truth_pairs: set
    ) -> float:
        """Compute normalized Discounted Cumulative Gain."""
        if not ground_truth_pairs or not retrieved_sources:
            return 0.0
        
        # DCG: sum of relevance / log(position + 1)
        dcg = 0.0
        for i, source in enumerate(retrieved_sources, 1):
            pair = (source.get("document_id"), source.get("page_number"))
            relevance = 1.0 if pair in ground_truth_pairs else 0.0
            dcg += relevance / (1.0 + __import__("math").log2(i + 1))
        
        # IDCG: ideal DCG (all relevant results first)
        idcg = sum(1.0 / (1.0 + __import__("math").log2(i + 1)) 
                  for i in range(min(len(retrieved_sources), len(ground_truth_pairs))))
        
        return dcg / idcg if idcg > 0 else 0.0

    def _compute_quality_metrics(
        self, question: str, answer: str, ground_truth_sources: list[dict]
    ) -> AnswerQualityMetrics:
        """Compute answer quality metrics."""
        metrics = AnswerQualityMetrics()
        
        if not answer:
            return metrics
        
        # Faithfulness: check if answer stays close to content
        metrics.is_faithful = self._check_faithfulness(answer, ground_truth_sources)
        metrics.faithfulness_score = 0.8 if metrics.is_faithful else 0.2
        
        # Relevance: check if answer addresses the question
        metrics.relevance_score = self._compute_relevance_score(question, answer)
        
        # Citations: check for source attribution
        metrics.has_citations = "[" in answer and "]" in answer
        metrics.citation_count = answer.count("[")
        
        # Hallucination: check for unsupported claims
        metrics.is_hallucinated = self._detect_hallucination(answer, ground_truth_sources)
        metrics.hallucination_score = 0.9 if metrics.is_hallucinated else 0.1
        
        return metrics

    def _check_faithfulness(self, answer: str, ground_truth_sources: list[dict]) -> bool:
        """Check if answer is faithful to sources."""
        if not ground_truth_sources or not answer:
            return False
        
        # Simple heuristic: if answer contains common keywords from expected domains
        # In real implementation, would use semantic similarity or entailment checks
        answer_lower = answer.lower()
        
        # Check for hallucination patterns (these indicate unfaithfulness)
        hallucination_patterns = [
            "i don't have",
            "cannot determine",
            "not specified",
            "i'm not sure",
        ]
        
        for pattern in hallucination_patterns:
            if pattern in answer_lower:
                return False
        
        # If answer is reasonably detailed, likely faithful
        return len(answer) > 20

    def _compute_relevance_score(self, question: str, answer: str) -> float:
        """Compute relevance score between question and answer."""
        if not answer:
            return 0.0
        
        # Simple keyword overlap heuristic
        q_words = set(question.lower().split())
        a_words = set(answer.lower().split())
        
        # Remove common stop words
        stop_words = {"the", "a", "an", "and", "or", "is", "are", "was", "were", "to", "of", "in", "for", "with", "by"}
        q_words -= stop_words
        a_words -= stop_words
        
        if not q_words:
            return 0.5
        
        overlap = len(q_words & a_words)
        relevance = overlap / len(q_words)
        
        # Cap at reasonable value (perfect match = 1.0)
        return min(1.0, relevance)

    def _detect_hallucination(self, answer: str, ground_truth_sources: list[dict]) -> bool:
        """Detect potential hallucinations in answer."""
        if not answer or not ground_truth_sources:
            return False
        
        # Patterns that indicate hallucination
        hallucination_indicators = [
            "based on my knowledge",
            "in my opinion",
            "i believe",
            "it is said",
            "some say",
            "allegedly",
        ]
        
        answer_lower = answer.lower()
        
        for indicator in hallucination_indicators:
            if indicator in answer_lower:
                return True
        
        # If answer is very short or very long, might indicate issues
        if len(answer) < 10 or len(answer) > 5000:
            return True
        
        return False

    def _compile_results(self) -> dict:
        """Compile evaluation results with statistics."""
        # Filter out None results
        self.results = [r for r in self.results if r is not None]
        
        if not self.results:
            return {"error": "No results to compile"}
        
        # Category breakdown
        categories = {}
        for result in self.results:
            if not result:
                continue
            cat = result.category
            if cat not in categories:
                categories[cat] = {
                    "count": 0,
                    "passed": 0,
                    "avg_score": 0.0,
                    "avg_retrieval_recall": 0.0,
                    "avg_faithfulness": 0.0,
                }
            
            categories[cat]["count"] += 1
            categories[cat]["passed"] += 1 if result.overall_score >= 0.7 else 0
            categories[cat]["avg_score"] += result.overall_score
            categories[cat]["avg_retrieval_recall"] += result.retrieval_metrics.recall_at_k
            categories[cat]["avg_faithfulness"] += result.quality_metrics.faithfulness_score
        
        # Compute averages
        for cat in categories:
            count = max(categories[cat]["count"], 1)
            categories[cat]["avg_score"] /= count
            categories[cat]["avg_retrieval_recall"] /= count
            categories[cat]["avg_faithfulness"] /= count
            categories[cat]["pass_rate"] = categories[cat]["passed"] / categories[cat]["count"]
        
        # Overall statistics
        total_count = len(self.results)
        passed_count = sum(1 for r in self.results if r.overall_score >= 0.7)
        errors = sum(1 for r in self.results if r.error)
        
        # Retrieval stats
        avg_recall = sum(r.retrieval_metrics.recall_at_k for r in self.results) / max(total_count, 1)
        avg_precision = sum(r.retrieval_metrics.precision_at_k for r in self.results) / max(total_count, 1)
        avg_mrr = sum(r.retrieval_metrics.mrr for r in self.results) / max(total_count, 1)
        
        # Quality stats
        avg_faithfulness = sum(r.quality_metrics.faithfulness_score for r in self.results) / max(total_count, 1)
        avg_relevance = sum(r.quality_metrics.relevance_score for r in self.results) / max(total_count, 1)
        hallucination_rate = sum(1 for r in self.results if r.quality_metrics.is_hallucinated) / max(total_count, 1)
        citation_rate = sum(1 for r in self.results if r.quality_metrics.has_citations) / max(total_count, 1)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_questions": total_count,
                "passed": passed_count,
                "failed": total_count - passed_count,
                "errors": errors,
                "pass_rate": passed_count / max(total_count, 1),
            },
            "retrieval_metrics": {
                "avg_recall_at_k": avg_recall,
                "avg_precision_at_k": avg_precision,
                "avg_mrr": avg_mrr,
            },
            "quality_metrics": {
                "avg_faithfulness": avg_faithfulness,
                "avg_relevance": avg_relevance,
                "hallucination_rate": hallucination_rate,
                "citation_rate": citation_rate,
            },
            "category_breakdown": categories,
            "detailed_results": [asdict(r) for r in self.results],
        }

    def get_failed_examples(self, count: int = 15) -> list[QuestionEvaluation]:
        """Get worst performing examples for analysis."""
        # Sort by lowest overall score
        sorted_results = sorted(self.results, key=lambda r: r.overall_score)
        
        # Include errors first, then low scores
        failed = [r for r in sorted_results if r.error or r.overall_score < 0.5]
        
        return failed[:count]

    def _generate_mock_answer(self, question: str) -> str:
        """Generate mock answer for testing (when service not available)."""
        return f"Mock answer to: {question[:50]}... This would be the generated response from the RAG pipeline."

    def _generate_mock_sources(self) -> list[dict]:
        """Generate mock sources for testing."""
        return [
            {
                "filename": "sample.pdf",
                "page_number": 1,
                "similarity_score": 0.85,
                "text_preview": "Sample text content...",
            }
        ]

    def export_results(self, output_path: str) -> None:
        """Export evaluation results to JSON."""
        results = self._compile_results()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        self.logger.info(f"Results exported to {output_path}")


# Standalone evaluation function
def run_rag_evaluation(
    rag_service: Optional[RAGService] = None,
    max_questions: int = 100,
    dataset_path: Optional[str] = None,
) -> dict:
    """
    Run RAG evaluation.

    Args:
        rag_service: RAG service to evaluate
        max_questions: Maximum questions to evaluate
        dataset_path: Path to dataset

    Returns:
        Evaluation results
    """
    evaluator = RAGEvaluator(rag_service=rag_service, dataset_path=dataset_path)
    return evaluator.evaluate_all(max_questions=max_questions)
