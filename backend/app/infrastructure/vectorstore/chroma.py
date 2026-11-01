"""
ChromaDB vector store implementation.

Wrapper around ChromaDB for persistent vector storage and retrieval.
"""

from typing import Optional

from app.core.config import settings
from app.core.exceptions import IndexingException, RetrievalException
from app.core.logging import get_logger
from app.infrastructure.vectorstore.base import RetrievedChunk, VectorStore

logger = get_logger(__name__)


class ChromaVectorStore(VectorStore):
    """Vector store implementation using ChromaDB."""

    def __init__(self):
        """Initialize ChromaDB client and collection."""
        try:
            import chromadb

            logger.debug(f"Initializing ChromaDB with path: {settings.chromadb_persist_dir}")

            # Create persistent client
            self.client = chromadb.PersistentClient(
                path=str(settings.chroma_directory)
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=settings.chromadb_collection_name,
                metadata={"hnsw:space": "cosine"},
            )

            logger.info(
                f"ChromaDB initialized: collection={settings.chromadb_collection_name}, "
                f"path={settings.chromadb_persist_dir}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise IndexingException(f"ChromaDB initialization failed: {str(e)}")

    def add_chunks(
        self,
        chunk_ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadata_list: list[dict],
    ) -> None:
        """
        Add chunks to vector store.

        Args:
            chunk_ids: List of chunk IDs
            texts: List of chunk texts
            embeddings: List of embedding vectors
            metadata_list: List of metadata dicts for each chunk

        Raises:
            IndexingException: If adding fails
        """
        try:
            logger.debug(f"Adding {len(chunk_ids)} chunks to ChromaDB")

            self.collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadata_list,
            )

            logger.debug(f"Successfully added {len(chunk_ids)} chunks")

        except Exception as e:
            logger.error(f"Failed to add chunks to ChromaDB: {e}")
            raise IndexingException(f"Failed to add chunks: {str(e)}")

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 4,
        filter_dict: dict | None = None,
    ) -> list[RetrievedChunk]:
        """
        Search for similar chunks.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            filter_dict: Optional metadata filter (e.g., {"document_id": "..."})

        Returns:
            List of retrieved chunks with similarity scores

        Raises:
            RetrievalException: If search fails
        """
        try:
            logger.debug(f"Searching with top_k={top_k}, filter={filter_dict}")

            # Build where filter if provided
            where_filter = None
            if filter_dict:
                where_filter = filter_dict

            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
            )

            # Convert results to RetrievedChunk objects
            retrieved_chunks = []

            if results and results["ids"] and len(results["ids"]) > 0:
                chunk_ids = results["ids"][0]
                distances = results["distances"][0]
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(chunk_ids)

                for chunk_id, distance, text, metadata in zip(chunk_ids, distances, documents, metadatas):
                    # Convert distance to similarity (cosine distance to similarity)
                    # For cosine space: similarity = 1 - distance
                    similarity_score = 1 - distance

                    chunk = RetrievedChunk(
                        chunk_id=chunk_id,
                        text=text,
                        similarity_score=similarity_score,
                        metadata=metadata,
                    )
                    retrieved_chunks.append(chunk)

            logger.debug(f"Found {len(retrieved_chunks)} similar chunks")
            return retrieved_chunks

        except Exception as e:
            logger.error(f"Failed to search ChromaDB: {e}")
            raise RetrievalException(f"Search failed: {str(e)}")

    def delete_chunks(self, chunk_ids: list[str]) -> None:
        """
        Delete chunks from vector store.

        Args:
            chunk_ids: List of chunk IDs to delete

        Raises:
            IndexingException: If deletion fails
        """
        try:
            logger.debug(f"Deleting {len(chunk_ids)} chunks from ChromaDB")

            self.collection.delete(ids=chunk_ids)

            logger.debug(f"Successfully deleted {len(chunk_ids)} chunks")

        except Exception as e:
            logger.error(f"Failed to delete chunks: {e}")
            raise IndexingException(f"Failed to delete chunks: {str(e)}")

    def delete_document(self, document_id: str) -> None:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID

        Raises:
            IndexingException: If deletion fails
        """
        try:
            logger.debug(f"Deleting all chunks for document: {document_id}")

            # Query to find all chunks for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )

            if results and results["ids"]:
                chunk_ids = results["ids"]
                self.delete_chunks(chunk_ids)
                logger.debug(
                    f"Deleted {len(chunk_ids)} chunks for document {document_id}"
                )

        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise IndexingException(f"Failed to delete document: {str(e)}")

    def get_collection_size(self) -> int:
        """
        Get number of chunks in collection.

        Returns:
            Number of chunks
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to get collection size: {e}")
            return 0

    def clear(self) -> None:
        """
        Clear all data from vector store.

        Raises:
            IndexingException: If clearing fails
        """
        try:
            logger.warning("Clearing all data from ChromaDB collection")

            # Get all IDs and delete
            results = self.collection.get()
            if results and results["ids"]:
                self.collection.delete(ids=results["ids"])

            logger.info("ChromaDB collection cleared")

        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise IndexingException(f"Failed to clear collection: {str(e)}")
