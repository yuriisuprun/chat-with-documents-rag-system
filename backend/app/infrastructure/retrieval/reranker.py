"""
Cross-encoder reranking for RAG retrieval (2026 best practice).

Problem: Vector search returns 20 candidates, LLM sees only top 5.
Solution: Cross-encoder reranker improves precision before LLM sees results.

Performance: ~5ms per result, worth the accuracy gain.
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """
    Rerank retrieved documents using cross-encoder similarity.

    2026 production pattern:
    1. Vector search retrieves many candidates (k=20)
    2. Cross-encoder reranks by relevance
    3. LLM sees only top few (k=5)
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-large"):
        """
        Initialize reranker.

        Args:
            model_name: HuggingFace model ID for cross-encoder
                       Default: BAAI/bge-reranker-large (lightweight, fast)

        Note:
            Requires: pip install sentence-transformers
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
        logger.info(f"CrossEncoderReranker initialized with {model_name}")

    def _load_model(self) -> None:
        """Load cross-encoder model lazily on first use."""
        try:
            from sentence_transformers import CrossEncoder

            self.model = CrossEncoder(self.model_name)
            logger.debug(f"Loaded cross-encoder model: {self.model_name}")
        except ImportError:
            logger.warning(
                "sentence-transformers not available for reranking. "
                "Install with: pip install sentence-transformers"
            )
            self.model = None

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents by relevance to query.

        Args:
            query: User query
            documents: List of document dicts with 'text' and optional metadata
            top_k: Number of top results to return

        Returns:
            Top-k reranked documents with 'rerank_score' added

        Example:
            >>> reranker = CrossEncoderReranker()
            >>> docs = [
            ...     {"text": "AI is transforming tech", "source": "doc1"},
            ...     {"text": "Python is a programming language", "source": "doc2"},
            ... ]
            >>> reranked = reranker.rerank("What is AI?", docs, top_k=1)
            >>> print(reranked[0]['source'])  # "doc1"
        """
        if not self.model:
            logger.warning(
                "Cross-encoder model not available. Returning original order."
            )
            return documents[:top_k]

        if not documents:
            return []

        logger.debug(f"Reranking {len(documents)} documents for query: {query[:50]}...")

        # Prepare pairs (query, document)
        pairs = [(query, doc.get("text", "")) for doc in documents]

        # Compute similarity scores
        scores = self.model.predict(pairs)

        # Add scores to documents
        reranked_docs = []
        for doc, score in zip(documents, scores):
            doc_copy = doc.copy()
            doc_copy["rerank_score"] = float(score)
            reranked_docs.append(doc_copy)

        # Sort by score
        reranked_docs.sort(key=lambda x: x["rerank_score"], reverse=True)

        logger.debug(f"Reranking complete. Top score: {reranked_docs[0]['rerank_score']:.3f}")
        return reranked_docs[:top_k]

    def batch_rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 32,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Rerank many documents in batches for efficiency.

        Use when reranking 100+ documents.

        Args:
            query: User query
            documents: List of document dicts
            batch_size: Documents per batch (balance speed vs memory)
            top_k: Number of results to return

        Returns:
            Top-k reranked documents

        Example:
            >>> large_doc_list = [{"text": f"doc {i}"} for i in range(1000)]
            >>> result = reranker.batch_rerank(query, large_doc_list, top_k=10)
        """
        if not self.model:
            return documents[:top_k]

        logger.debug(f"Batch reranking {len(documents)} docs in batches of {batch_size}")

        all_scores = []
        for batch_start in range(0, len(documents), batch_size):
            batch_end = min(batch_start + batch_size, len(documents))
            batch_docs = documents[batch_start:batch_end]

            pairs = [(query, doc.get("text", "")) for doc in batch_docs]
            batch_scores = self.model.predict(pairs)
            all_scores.extend(batch_scores)

        # Add scores and sort
        reranked_docs = []
        for doc, score in zip(documents, all_scores):
            doc_copy = doc.copy()
            doc_copy["rerank_score"] = float(score)
            reranked_docs.append(doc_copy)

        reranked_docs.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked_docs[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        """Get reranker statistics."""
        return {
            "model": self.model_name,
            "model_loaded": self.model is not None,
        }
