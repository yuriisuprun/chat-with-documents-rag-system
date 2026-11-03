"""
Hybrid retrieval combining dense (vector) and sparse (keyword) search.

2026 best practice: Pure vector search misses exact keywords.
Hybrid approach combines:
- Dense: Semantic similarity via embeddings
- Sparse: Exact keyword matching via BM25
"""

from typing import List, Dict, Any, Optional, Tuple
import logging

from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Combine vector and BM25 keyword search for better recall."""

    def __init__(self, alpha: float = 0.6):
        """
        Initialize hybrid retriever.

        Args:
            alpha: Weight for dense retrieval (0.0-1.0)
                   - 1.0 = pure dense, 0.0 = pure sparse
                   - 0.6 default = 60% dense + 40% sparse
        """
        self.alpha = alpha
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[str] = []
        logger.info(f"HybridRetriever initialized with alpha={alpha}")

    def build_sparse_index(self, documents: List[str]) -> None:
        """
        Build BM25 sparse index from documents.

        Args:
            documents: List of document texts to index

        Example:
            >>> retriever = HybridRetriever()
            >>> retriever.build_sparse_index(["doc1", "doc2", "doc3"])
        """
        logger.debug(f"Building BM25 index for {len(documents)} documents")
        self.documents = documents
        tokenized_docs = [doc.lower().split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized_docs)
        logger.debug("BM25 index built successfully")

    def retrieve_hybrid(
        self,
        query: str,
        dense_results: List[Tuple[str, float]],
        top_k: int = 5,
        normalize: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve results combining dense and sparse scores.

        Args:
            query: User query string
            dense_results: List of (document_text, similarity_score) from vector search
            top_k: Number of results to return
            normalize: Whether to normalize scores to 0-1 range

        Returns:
            List of results with combined scores, sorted by relevance

        Example:
            >>> dense_results = [("text1", 0.95), ("text2", 0.82)]
            >>> results = retriever.retrieve_hybrid(
            ...     "find documents about AI",
            ...     dense_results,
            ...     top_k=5
            ... )
            >>> print(f"Top result score: {results[0]['combined_score']}")
        """
        if not self.bm25:
            logger.warning("BM25 index not built, returning dense results only")
            return [
                {
                    "text": text,
                    "dense_score": score,
                    "sparse_score": 0.0,
                    "combined_score": score * self.alpha,
                }
                for text, score in dense_results[:top_k]
            ]

        # Get sparse scores (BM25)
        logger.debug(f"Computing BM25 scores for query: {query[:50]}...")
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        # Normalize sparse scores
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
        normalized_bm25 = [score / max_bm25 for score in bm25_scores]

        # Create dense score map
        dense_map = {text: score for text, score in dense_results}

        # Combine scores
        combined_results = []
        for idx, document in enumerate(self.documents):
            dense_score = dense_map.get(document, 0.0)
            sparse_score = normalized_bm25[idx]

            # Weighted combination
            combined_score = (self.alpha * dense_score) + (
                (1 - self.alpha) * sparse_score
            )

            combined_results.append(
                {
                    "text": document,
                    "dense_score": dense_score,
                    "sparse_score": sparse_score,
                    "combined_score": combined_score,
                    "index": idx,
                }
            )

        # Sort by combined score
        combined_results.sort(key=lambda x: x["combined_score"], reverse=True)

        logger.debug(
            f"Hybrid retrieval: returning top {top_k} of {len(combined_results)} results"
        )
        return combined_results[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics."""
        return {
            "alpha": self.alpha,
            "num_documents": len(self.documents),
            "bm25_ready": self.bm25 is not None,
        }
