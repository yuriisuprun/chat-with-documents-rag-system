"""
Retrieval service for semantic search.

Orchestrates embedding query and vector store search.
"""

from typing import Optional

from app.core.exceptions import EmbeddingException, RetrievalException
from app.core.logging import get_logger
from app.infrastructure.embeddings.huggingface_provider import (
    HuggingFaceEmbeddingProvider,
)
from app.infrastructure.vectorstore.base import RetrievedChunk
from app.infrastructure.vectorstore.chroma import ChromaVectorStore

logger = get_logger(__name__)


class RetrievalService:
    """Service for semantic search and retrieval."""

    def __init__(
        self,
        embedding_provider: Optional[HuggingFaceEmbeddingProvider] = None,
        vector_store: Optional[ChromaVectorStore] = None,
    ):
        """
        Initialize retrieval service.

        Args:
            embedding_provider: Embedding provider (uses singleton by default)
            vector_store: Vector store (uses ChromaDB by default)
        """
        self.embedding_provider = embedding_provider or HuggingFaceEmbeddingProvider()
        self.vector_store = vector_store or ChromaVectorStore()

        logger.debug(
            f"RetrievalService initialized: "
            f"embedding_model={self.embedding_provider.get_model_name()}"
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        document_ids: Optional[list[str]] = None,
    ) -> list[RetrievedChunk]:
        """
        Retrieve relevant chunks for a query.

        Steps:
        1. Embed query text
        2. Search vector store
        3. Return results with metadata

        Args:
            query: Query text
            top_k: Number of results to return
            document_ids: Optional list of document IDs to filter by

        Returns:
            List of RetrievedChunk objects with similarity scores

        Raises:
            EmbeddingException: If query embedding fails
            RetrievalException: If search fails
        """
        try:
            logger.debug(f"Retrieving chunks for query: '{query[:50]}...'")

            # Step 1: Embed query
            try:
                query_embedding = self.embedding_provider.embed_text(query)
                logger.debug(f"Query embedded to {len(query_embedding)} dimensions")
            except Exception as e:
                logger.error(f"Failed to embed query: {e}")
                raise EmbeddingException(f"Query embedding failed: {str(e)}")

            # Step 2: Build filter if document IDs specified
            filter_dict = None
            if document_ids:
                # ChromaDB $in operator for filtering
                filter_dict = {"document_id": {"$in": document_ids}}
                logger.debug(f"Filtering to {len(document_ids)} documents")

            # Step 3: Search vector store
            retrieved_chunks = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filter_dict=filter_dict,
            )

            logger.info(
                f"Retrieved {len(retrieved_chunks)} chunks for query, "
                f"top similarity: {retrieved_chunks[0].similarity_score:.3f}"
                if retrieved_chunks
                else "Retrieved 0 chunks for query"
            )

            return retrieved_chunks

        except (EmbeddingException, RetrievalException):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during retrieval: {e}")
            raise RetrievalException(f"Retrieval failed: {str(e)}")

    def index_document(
        self,
        chunks: list,  # List of Chunk objects from ingestion_service
        embedding_model: str,
    ) -> int:
        """
        Index a document's chunks.

        Steps:
        1. Extract text from chunks
        2. Embed all texts
        3. Add to vector store

        Args:
            chunks: List of Chunk objects with text and metadata
            embedding_model: Name of embedding model used

        Returns:
            Number of chunks indexed

        Raises:
            EmbeddingException: If embedding fails
            RetrievalException: If indexing fails
        """
        try:
            logger.debug(f"Indexing {len(chunks)} chunks")

            if not chunks:
                logger.warning("No chunks to index")
                return 0

            # Step 1: Extract data
            chunk_ids = [chunk.chunk_id for chunk in chunks]
            texts = [chunk.text for chunk in chunks]

            # Build metadata list
            metadata_list = []
            for chunk in chunks:
                metadata = {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "filename": chunk.filename,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "embedding_model": embedding_model,
                }
                metadata_list.append(metadata)

            # Step 2: Embed texts
            try:
                embeddings = self.embedding_provider.embed_texts(texts)
                logger.debug(
                    f"Embedded {len(embeddings)} texts to "
                    f"{len(embeddings[0])} dimensions"
                )
            except Exception as e:
                logger.error(f"Failed to embed chunks: {e}")
                raise EmbeddingException(f"Embedding failed: {str(e)}")

            # Step 3: Add to vector store
            try:
                self.vector_store.add_chunks(
                    chunk_ids=chunk_ids,
                    texts=texts,
                    embeddings=embeddings,
                    metadata_list=metadata_list,
                )
                logger.info(f"Indexed {len(chunk_ids)} chunks")
                return len(chunk_ids)

            except Exception as e:
                logger.error(f"Failed to add chunks to vector store: {e}")
                raise RetrievalException(f"Indexing failed: {str(e)}")

        except (EmbeddingException, RetrievalException):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during indexing: {e}")
            raise RetrievalException(f"Indexing failed: {str(e)}")

    def delete_document_chunks(self, document_id: str) -> int:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID

        Returns:
            Number of chunks deleted

        Raises:
            RetrievalException: If deletion fails
        """
        try:
            logger.debug(f"Deleting chunks for document: {document_id}")

            # Get current size
            size_before = self.vector_store.get_collection_size()

            # Delete document
            self.vector_store.delete_document(document_id)

            # Get new size
            size_after = self.vector_store.get_collection_size()
            deleted_count = size_before - size_after

            logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete document chunks: {e}")
            raise RetrievalException(f"Deletion failed: {str(e)}")

    def get_collection_stats(self) -> dict:
        """
        Get vector store collection statistics.

        Returns:
            Dictionary with collection stats
        """
        try:
            size = self.vector_store.get_collection_size()
            dimension = self.embedding_provider.get_embedding_dimension()

            return {
                "chunk_count": size,
                "embedding_dimension": dimension,
                "embedding_model": self.embedding_provider.get_model_name(),
            }

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "error": str(e),
            }
