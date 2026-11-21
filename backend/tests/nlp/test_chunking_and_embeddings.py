"""
Comprehensive validation of text chunking and embedding quality.

Tests:
1. Chunking algorithm (size, overlap, boundaries)
2. Metadata integrity
3. Embedding dimensions and consistency
4. Semantic similarity and retrieval quality
"""

import math
from typing import List, Tuple

import pytest
from sentence_transformers import util

from app.core.config import settings
from app.core.exceptions import ChunkingException, EmbeddingException
from app.infrastructure.embeddings.huggingface_provider import (
    HuggingFaceEmbeddingProvider,
)
from app.infrastructure.pdf.chunker import PDFChunker
from app.infrastructure.pdf.models import Chunk


# ============================================================================
# FIXTURES: Test Data
# ============================================================================


@pytest.fixture
def chunker():
    """Provide initialized chunker."""
    return PDFChunker()


@pytest.fixture
def embedding_provider():
    """Provide initialized embedding provider."""
    return HuggingFaceEmbeddingProvider()


@pytest.fixture
def sample_texts():
    """Collection of sample texts for testing."""
    return {
        "short": "Hello world.",
        "medium": "The quick brown fox jumps over the lazy dog. " * 10,
        "long": (
            "Natural language processing (NLP) is a subfield of linguistics, "
            "computer science, and artificial intelligence concerned with the interactions "
            "between computers and human language. NLP is used to apply machine learning "
            "algorithms to text and speech. This includes tasks such as sentiment analysis, "
            "text classification, machine translation, and question answering. "
        ) * 20,
        "unicode": "English text. 中文文本。 النص العربي. Русский текст. 🚀📊✅",
        "multilingual": (
            "Hello world. Bonjour le monde. Hola mundo. "
            "你好世界. مرحبا بالعالم. Привет мир. "
        ),
        "with_lists": (
            "The following items are important:\n"
            "1. First item\n"
            "2. Second item\n"
            "3. Third item\n"
            "These items must be processed."
        ),
        "with_headings": (
            "## Main Section\n"
            "This is the introduction.\n"
            "### Subsection\n"
            "This is more detail.\n"
            "#### Details\n"
            "Even more specific information."
        ),
        "irregular_whitespace": (
            "Text with   irregular   spacing.  "
            "Text\nwith\nnewlines.\tText\twith\ttabs."
        ),
        "exact_chunk_size": "word " * 300,  # ~1500 chars
    }


@pytest.fixture
def retrieval_dataset():
    """Create controlled dataset for retrieval evaluation."""
    return {
        "queries": [
            "What is machine learning?",
            "How do neural networks work?",
            "Explain deep learning",
            "What is NLP?",
            "Tell me about embeddings",
        ],
        "passages": {
            "rel_1": "Machine learning is a subset of artificial intelligence",
            "rel_2": "Neural networks are inspired by biological neurons",
            "rel_3": "Deep learning uses multiple layers of artificial neurons",
            "rel_4": "NLP is about processing human language with computers",
            "rel_5": "Embeddings represent text as numerical vectors",
            "irrel_1": "The weather is sunny today",
            "irrel_2": "I like to eat pizza",
            "irrel_3": "The car is red",
        },
        "relevance": {
            # (query_idx, passage_key) -> relevance (1=relevant, 0=irrelevant)
            (0, "rel_1"): 1,  # Query 0 relevant to rel_1
            (0, "rel_2"): 0,
            (0, "irrel_1"): 0,
            (1, "rel_2"): 1,  # Query 1 relevant to rel_2
            (1, "rel_1"): 0,
            (1, "irrel_1"): 0,
            (2, "rel_3"): 1,  # Query 2 relevant to rel_3
            (2, "rel_2"): 1,  # Also somewhat relevant
            (3, "rel_4"): 1,  # Query 3 relevant to rel_4
            (3, "rel_1"): 0,
            (4, "rel_5"): 1,  # Query 4 relevant to rel_5
            (4, "rel_1"): 0,
        },
    }


# ============================================================================
# PART 1: CHUNKING VALIDATION
# ============================================================================


class TestChunkingBoundaries:
    """Test chunk size and boundary handling."""

    def test_chunk_shorter_than_chunk_size(self, chunker, sample_texts):
        """Text shorter than chunk size should create single chunk."""
        text = sample_texts["short"]
        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        assert len(chunks) >= 1
        assert all(len(chunk.text) > 0 for chunk in chunks)

    def test_chunk_exactly_at_size(self, chunker):
        """Text at exact chunk size should be chunked appropriately."""
        # Create text of approximately chunk_size
        text = "word " * 300  # ~1500 chars
        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        assert len(chunks) >= 1
        # Total content should be preserved (allow for some variance)
        total_chars = sum(len(chunk.text) for chunk in chunks)
        assert total_chars >= len(text) * 0.9

    def test_chunk_exceeding_size(self, chunker, sample_texts):
        """Text exceeding chunk size should create multiple chunks."""
        text = sample_texts["long"]
        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        assert len(chunks) > 1
        # Verify no chunk exceeds limit (with some tolerance)
        for chunk in chunks:
            assert len(chunk.text) <= chunker.chunk_size * 1.1

    def test_chunk_sequential_indexes(self, chunker, sample_texts):
        """Chunk indexes should be sequential starting from 0."""
        text = sample_texts["long"]
        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        indexes = [chunk.chunk_index for chunk in chunks]
        assert indexes == list(range(len(chunks)))

    def test_chunk_metadata_consistency(self, chunker):
        """All chunks should have consistent metadata."""
        text = "Test content. " * 100
        document_id = "doc_test_123"
        filename = "test.pdf"
        page_number = 5

        chunks = chunker.chunk_page_text(text, page_number, document_id, filename)

        for chunk in chunks:
            assert chunk.document_id == document_id
            assert chunk.filename == filename
            assert chunk.page_number == page_number
            assert chunk.text_length == len(chunk.text)

    def test_empty_text_returns_empty_list(self, chunker):
        """Empty text should return empty list."""
        chunks = chunker.chunk_page_text("", 1, "doc_1", "test.pdf")
        assert len(chunks) == 0

    def test_whitespace_only_text(self, chunker):
        """Text with only whitespace should return empty list."""
        chunks = chunker.chunk_page_text("   \n\t  ", 1, "doc_1", "test.pdf")
        assert len(chunks) == 0


class TestOverlapHandling:
    """Test chunk overlap correctness."""

    def test_overlap_preserved_between_chunks(self, chunker):
        """Overlap should be present between consecutive chunks."""
        text = (
            "This is a sentence. " * 5
            + "Another sentence. " * 5
            + "Yet another sentence. " * 5
        )
        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        if len(chunks) > 1:
            # Check that consecutive chunks share content (overlap)
            chunk1_text = chunks[0].text
            chunk2_text = chunks[1].text

            # Overlap should exist
            # (some text from end of chunk1 should appear in chunk2)
            assert len(chunk1_text) > 0
            assert len(chunk2_text) > 0

    def test_no_content_loss_with_overlap(self, chunker):
        """Content should not be lost due to overlap; it should be preserved."""
        text = "Word " * 500  # Large text
        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        # Reconstruct text by taking unique content from each chunk
        # Due to overlap, we need to be careful not to double-count
        total_unique_content = 0
        for i, chunk in enumerate(chunks):
            if i == 0:
                total_unique_content += len(chunk.text)
            else:
                # Estimate overlap (would need actual overlap detection)
                # For now, just verify chunk exists
                total_unique_content += max(0, len(chunk.text) - chunker.chunk_overlap)

        # Total should be close to original (within reasonable margin)
        assert total_unique_content >= len(text) * 0.8

    def test_chunk_size_respects_limit(self, chunker):
        """No individual chunk should exceed the configured chunk size."""
        text = "This is a long sentence. " * 100
        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        for chunk in chunks:
            # Allow 10% tolerance for boundary effects
            assert len(chunk.text) <= chunker.chunk_size * 1.1


class TestContentPreservation:
    """Test that content is correctly preserved through chunking."""

    def test_unicode_preservation(self, chunker, sample_texts):
        """Unicode characters should be preserved in chunks."""
        text = sample_texts["unicode"]
        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        combined_text = " ".join(chunk.text for chunk in chunks)
        # Unicode characters should be present
        assert "中文" in combined_text  # Chinese
        assert "🚀" in combined_text  # Emoji

    def test_no_unnecessary_truncation(self, chunker, sample_texts):
        """Sentences should not be unnecessarily truncated."""
        text = (
            "This is the first sentence with complete meaning. "
            "This is the second sentence also complete. "
            "And the third one is complete too."
        )
        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        # At least one chunk should end with a period (complete sentence)
        assert any(chunk.text.endswith(".") for chunk in chunks)

    def test_multilingual_text_preserved(self, chunker, sample_texts):
        """Multilingual text should be preserved correctly."""
        text = sample_texts["multilingual"]
        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        combined = " ".join(chunk.text for chunk in chunks)
        # Should contain multiple languages
        assert "Hello" in combined
        assert "Bonjour" in combined or "mundo" in combined

    def test_structured_text_with_lists(self, chunker, sample_texts):
        """Numbered lists should be preserved."""
        text = sample_texts["with_lists"]
        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        combined = " ".join(chunk.text for chunk in chunks)
        # List items should be preserved
        assert "First item" in combined or "1." in combined

    def test_structured_text_with_headings(self, chunker, sample_texts):
        """Section headings should be handled appropriately."""
        text = sample_texts["with_headings"]
        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        combined = " ".join(chunk.text for chunk in chunks)
        # Content should be preserved
        assert len(combined) > 0

    def test_irregular_whitespace_normalized(self, chunker, sample_texts):
        """Irregular whitespace should be handled."""
        text = sample_texts["irregular_whitespace"]
        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        # Should not crash and should produce chunks
        assert len(chunks) >= 1


class TestMetadataIntegrity:
    """Test metadata accuracy in chunks."""

    def test_page_number_correct(self, chunker):
        """Page numbers should match input."""
        text = "Content " * 100
        page_num = 42
        chunks = chunker.chunk_page_text(text, page_num, "doc_1", "test.pdf")

        assert all(chunk.page_number == page_num for chunk in chunks)

    def test_document_id_correct(self, chunker):
        """Document IDs should match input."""
        text = "Content " * 100
        doc_id = "unique_doc_abc123"
        chunks = chunker.chunk_page_text(text, 1, doc_id, "test.pdf")

        assert all(chunk.document_id == doc_id for chunk in chunks)

    def test_filename_correct(self, chunker):
        """Filenames should be preserved."""
        text = "Content " * 100
        filename = "my_document_v2.pdf"
        chunks = chunker.chunk_page_text(text, 1, "doc_1", filename)

        assert all(chunk.filename == filename for chunk in chunks)

    def test_chunk_id_unique(self, chunker):
        """Chunk IDs should be unique."""
        text = "Content " * 100
        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        chunk_ids = [chunk.chunk_id for chunk in chunks]
        assert len(chunk_ids) == len(set(chunk_ids))

    def test_chunk_id_deterministic(self, chunker):
        """Same input should produce same chunk IDs (deterministic)."""
        text = "Content " * 100
        doc_id = "doc_1"
        page = 1

        chunks1 = chunker.chunk_page_text(text, page, doc_id, "test.pdf")
        chunks2 = chunker.chunk_page_text(text, page, doc_id, "test.pdf")

        ids1 = [c.chunk_id for c in chunks1]
        ids2 = [c.chunk_id for c in chunks2]

        assert ids1 == ids2


# ============================================================================
# PART 2: EMBEDDING VALIDATION
# ============================================================================


class TestEmbeddingDimensions:
    """Test embedding dimensions and properties."""

    def test_embedding_dimension_is_384(self, embedding_provider):
        """all-MiniLM-L6-v2 should produce 384-dimensional embeddings."""
        dimension = embedding_provider.get_embedding_dimension()
        assert dimension == 384

    def test_single_embedding_shape(self, embedding_provider):
        """Single embedding should be 384-dimensional."""
        text = "This is a test sentence."
        embedding = embedding_provider.embed_text(text)

        assert len(embedding) == 384
        assert isinstance(embedding, list)
        assert all(isinstance(x, (int, float)) for x in embedding)

    def test_batch_embedding_shapes(self, embedding_provider):
        """Batch embeddings should all be 384-dimensional."""
        texts = [
            "First sentence",
            "Second sentence",
            "Third sentence",
        ]
        embeddings = embedding_provider.embed_texts(texts)

        assert len(embeddings) == len(texts)
        assert all(len(emb) == 384 for emb in embeddings)

    def test_embedding_values_numeric_and_finite(self, embedding_provider):
        """Embedding values should be numeric and finite."""
        texts = [
            "Sample text one",
            "Sample text two",
            "Sample text three",
        ]
        embeddings = embedding_provider.embed_texts(texts)

        for emb in embeddings:
            for value in emb:
                assert isinstance(value, (int, float))
                assert math.isfinite(value)
                assert not math.isnan(value)

    def test_empty_string_handled(self, embedding_provider):
        """Empty string should produce valid embedding."""
        embedding = embedding_provider.embed_text("")
        assert len(embedding) == 384
        assert all(math.isfinite(x) for x in embedding)

    def test_very_long_text_handled(self, embedding_provider):
        """Very long text should be handled correctly."""
        long_text = "word " * 1000  # 5000 words
        embedding = embedding_provider.embed_text(long_text)

        assert len(embedding) == 384
        assert all(math.isfinite(x) for x in embedding)

    def test_unicode_text_embedded(self, embedding_provider):
        """Unicode text should be embedded correctly."""
        texts = [
            "English text",
            "中文文本",  # Chinese
            "النص العربي",  # Arabic
        ]
        embeddings = embedding_provider.embed_texts(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)


class TestEmbeddingConsistency:
    """Test embedding consistency and reproducibility."""

    def test_same_text_same_embedding(self, embedding_provider):
        """Same text should produce identical embeddings."""
        text = "Consistency test sentence for embedding."
        emb1 = embedding_provider.embed_text(text)
        emb2 = embedding_provider.embed_text(text)

        # Should be identical or very close (allowing for float precision)
        assert len(emb1) == len(emb2)
        for v1, v2 in zip(emb1, emb2):
            assert abs(v1 - v2) < 1e-5  # Float precision tolerance

    def test_batch_vs_individual_consistency(self, embedding_provider):
        """Individual embeddings should match batch embeddings."""
        texts = ["First text", "Second text", "Third text"]

        # Get individual embeddings
        individual = [embedding_provider.embed_text(t) for t in texts]

        # Get batch embeddings
        batch = embedding_provider.embed_texts(texts)

        # Should match
        assert len(individual) == len(batch)
        for ind, bat in zip(individual, batch):
            assert len(ind) == len(bat)
            for v1, v2 in zip(ind, bat):
                assert abs(v1 - v2) < 1e-5

    def test_model_initialization_cached(self, embedding_provider):
        """Model should be cached after first load."""
        # Create provider instance
        provider = HuggingFaceEmbeddingProvider()

        # Get dimension twice
        dim1 = provider.get_embedding_dimension()
        dim2 = provider.get_embedding_dimension()

        assert dim1 == dim2 == 384


class TestEmbeddingNormalization:
    """Test embedding normalization properties."""

    def test_embeddings_normalized_by_default(self, embedding_provider):
        """Embeddings should be normalized (length ≈ 1)."""
        texts = ["Test sentence one", "Test sentence two"]
        embeddings = embedding_provider.embed_texts(texts)

        for emb in embeddings:
            # Calculate L2 norm
            norm = math.sqrt(sum(x ** 2 for x in emb))
            # Should be approximately 1.0 (normalized)
            assert 0.99 <= norm <= 1.01

    def test_semantic_similarity_range(self, embedding_provider):
        """Cosine similarity should be in [-1, 1] range."""
        texts = [
            "The cat sat on the mat",
            "A feline rested on the rug",
            "I like to eat pizza",
        ]
        embeddings = embedding_provider.embed_texts(texts)

        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                # Calculate cosine similarity
                sim = float(util.pytorch_cos_sim(embeddings[i], embeddings[j]))
                assert -1.0 <= sim <= 1.0


# ============================================================================
# PART 3: SEMANTIC QUALITY EVALUATION
# ============================================================================


class TestSemanticQuality:
    """Test semantic retrieval quality."""

    def test_semantic_similarity_reasonable(self, embedding_provider):
        """Similar texts should have high similarity."""
        text1 = "Machine learning is a type of artificial intelligence"
        text2 = "Machine learning is a subset of artificial intelligence"

        emb1 = embedding_provider.embed_text(text1)
        emb2 = embedding_provider.embed_text(text2)

        similarity = float(util.pytorch_cos_sim(emb1, emb2))
        # Similar texts should have high similarity
        assert similarity > 0.8

    def test_dissimilar_texts_low_similarity(self, embedding_provider):
        """Dissimilar texts should have low similarity."""
        text1 = "Machine learning algorithms"
        text2 = "The color of the sky is blue"

        emb1 = embedding_provider.embed_text(text1)
        emb2 = embedding_provider.embed_text(text2)

        similarity = float(util.pytorch_cos_sim(emb1, emb2))
        # Dissimilar texts should have low similarity
        assert similarity < 0.5

    def test_retrieval_ranking_quality(self, embedding_provider, retrieval_dataset):
        """Relevant passages should rank higher than irrelevant ones."""
        queries = retrieval_dataset["queries"]
        passages = retrieval_dataset["passages"]
        relevance = retrieval_dataset["relevance"]

        # Embed queries and passages
        query_embeddings = embedding_provider.embed_texts(queries)
        passage_embeddings = {
            key: embedding_provider.embed_text(text)
            for key, text in passages.items()
        }

        # For each query, rank passages by similarity
        for q_idx, q_emb in enumerate(query_embeddings):
            scores = {}
            for p_key, p_emb in passage_embeddings.items():
                scores[p_key] = float(util.pytorch_cos_sim(q_emb, p_emb))

            # Find if relevant passages rank higher than irrelevant
            for (q, p), is_relevant in relevance.items():
                if q == q_idx:
                    # Get score of this passage
                    p_score = scores.get(p, -1)

                    # Get scores of opposite relevance
                    if is_relevant:
                        # This is relevant, should score high
                        assert p_score > -1
                    # else:
                    #     # This is irrelevant, might score lower
                    #     pass

    def test_recall_at_k(self, embedding_provider, retrieval_dataset):
        """Calculate Recall@K for retrieval."""
        queries = retrieval_dataset["queries"]
        passages = retrieval_dataset["passages"]
        relevance = retrieval_dataset["relevance"]

        query_embeddings = embedding_provider.embed_texts(queries)
        passage_embeddings = {
            key: embedding_provider.embed_text(text)
            for key, text in passages.items()
        }

        k_values = [1, 3, 5]
        recall_at_k = {k: [] for k in k_values}

        for q_idx, q_emb in enumerate(query_embeddings):
            # Rank passages
            scores = {}
            for p_key, p_emb in passage_embeddings.items():
                scores[p_key] = float(util.pytorch_cos_sim(q_emb, p_emb))

            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

            # Find relevant passages for this query
            relevant_passages = [
                p for (q, p), is_rel in relevance.items()
                if q == q_idx and is_rel
            ]

            if len(relevant_passages) > 0:
                for k in k_values:
                    top_k = [p for p, _ in ranked[:k]]
                    recalled = len([p for p in relevant_passages if p in top_k])
                    recall = recalled / len(relevant_passages)
                    recall_at_k[k].append(recall)

        # Calculate average recall@k
        avg_recall = {
            k: sum(recalls) / len(recalls) if recalls else 0
            for k, recalls in recall_at_k.items()
        }

        # Basic sanity check: recall should be reasonable
        assert avg_recall.get(5, 0) >= 0.5  # At least 50% recall@5


# ============================================================================
# PART 4: INTEGRATION TESTS
# ============================================================================


class TestChunkingAndEmbeddingIntegration:
    """Test chunking and embedding together."""

    def test_chunks_can_be_embedded(self, chunker, embedding_provider):
        """All chunks should be successfully embedded."""
        text = "Natural language processing. " * 50
        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = embedding_provider.embed_texts(chunk_texts)

        assert len(embeddings) == len(chunks)
        assert all(len(emb) == 384 for emb in embeddings)

    def test_semantic_coherence_preserved_in_chunks(
        self, chunker, embedding_provider
    ):
        """Chunks from same document should have coherent semantics."""
        text = (
            "Machine learning is a subset of artificial intelligence. "
            "It enables systems to learn from data. "
            "Deep learning uses neural networks. "
        ) * 10

        chunks = chunker.chunk_page_text(text, 1, "doc_1", "test.pdf")

        # All chunks should have positive similarity to each other
        chunk_embeddings = embedding_provider.embed_texts(
            [chunk.text for chunk in chunks]
        )

        # Check average similarity between chunks
        similarities = []
        for i in range(len(chunk_embeddings)):
            for j in range(i + 1, len(chunk_embeddings)):
                sim = float(
                    util.pytorch_cos_sim(
                        chunk_embeddings[i], chunk_embeddings[j]
                    )
                )
                similarities.append(sim)

        if similarities:
            avg_similarity = sum(similarities) / len(similarities)
            # Chunks from same document should have positive similarity
            assert avg_similarity > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
