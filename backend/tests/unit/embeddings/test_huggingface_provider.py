"""
Unit tests for HuggingFace embedding provider.

Tests embedding generation, consistency, and caching.
"""

import pytest

from app.infrastructure.embeddings.huggingface_provider import (
    HuggingFaceEmbeddingProvider,
)


@pytest.fixture
def embedding_provider():
    """Create embedding provider instance."""
    # Note: This will attempt to download the model on first use
    # For tests, you may want to mock this
    provider = HuggingFaceEmbeddingProvider()
    return provider


class TestEmbeddingProvider:
    """Test embedding provider functionality."""

    def test_provider_initialization(self, embedding_provider):
        """Test that provider initializes without errors."""
        assert embedding_provider is not None
        assert embedding_provider.model_name is not None

    def test_singleton_pattern(self):
        """Test that provider follows singleton pattern."""
        provider1 = HuggingFaceEmbeddingProvider()
        provider2 = HuggingFaceEmbeddingProvider()

        # Should be same instance
        assert provider1 is provider2

    def test_get_model_name(self, embedding_provider):
        """Test getting model name."""
        model_name = embedding_provider.get_model_name()

        assert isinstance(model_name, str)
        assert len(model_name) > 0

    def test_embed_text_returns_list(self, embedding_provider):
        """Test that embed_text returns a list of floats."""
        text = "This is a test sentence."

        embedding = embedding_provider.embed_text(text)

        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_text_consistent(self, embedding_provider):
        """Test that embedding same text produces consistent results."""
        text = "Consistent text for testing."

        embedding1 = embedding_provider.embed_text(text)
        embedding2 = embedding_provider.embed_text(text)

        # Should be identical
        assert embedding1 == embedding2

    def test_embed_texts_batch(self, embedding_provider):
        """Test batch embedding."""
        texts = [
            "First sentence.",
            "Second sentence.",
            "Third sentence.",
        ]

        embeddings = embedding_provider.embed_texts(texts)

        assert len(embeddings) == len(texts)
        assert all(isinstance(emb, list) for emb in embeddings)
        assert all(len(emb) > 0 for emb in embeddings)

    def test_embedding_dimension_consistency(self, embedding_provider):
        """Test that all embeddings have same dimension."""
        texts = ["Text 1", "Text 2", "Much longer text with more content"]

        embeddings = embedding_provider.embed_texts(texts)
        dimension = embedding_provider.get_embedding_dimension()

        assert all(len(emb) == dimension for emb in embeddings)

    def test_different_texts_different_embeddings(self, embedding_provider):
        """Test that different texts produce different embeddings."""
        text1 = "The cat sat on the mat."
        text2 = "The dog ran in the park."

        emb1 = embedding_provider.embed_text(text1)
        emb2 = embedding_provider.embed_text(text2)

        # Embeddings should be different
        assert emb1 != emb2

    def test_similarity_text_variations(self, embedding_provider):
        """Test that similar texts have similar embeddings."""
        text1 = "The cat is on the table"
        text2 = "The cat is on the desk"

        emb1 = embedding_provider.embed_text(text1)
        emb2 = embedding_provider.embed_text(text2)

        # Calculate cosine similarity
        def cosine_similarity(a, b):
            dot_product = sum(x * y for x, y in zip(a, b))
            magnitude_a = sum(x ** 2 for x in a) ** 0.5
            magnitude_b = sum(x ** 2 for x in b) ** 0.5
            if magnitude_a == 0 or magnitude_b == 0:
                return 0
            return dot_product / (magnitude_a * magnitude_b)

        similarity = cosine_similarity(emb1, emb2)

        # Similar texts should have high similarity (>0.8)
        assert similarity > 0.8

    def test_get_embedding_dimension(self, embedding_provider):
        """Test getting embedding dimension."""
        dimension = embedding_provider.get_embedding_dimension()

        assert isinstance(dimension, int)
        assert dimension > 0

    def test_normalize_embeddings(self, embedding_provider):
        """Test that normalized embeddings have unit norm."""
        text = "Test text for normalization."

        embedding = embedding_provider.embed_text(text)

        # Calculate norm
        norm = sum(x ** 2 for x in embedding) ** 0.5

        # For normalized embeddings, norm should be close to 1.0
        assert 0.99 <= norm <= 1.01

    def test_empty_string_handling(self, embedding_provider):
        """Test handling of empty strings."""
        # Empty strings should still produce embeddings
        embedding = embedding_provider.embed_text("")

        assert isinstance(embedding, list)
        assert len(embedding) > 0
