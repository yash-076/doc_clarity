from abc import ABC, abstractmethod
from typing import List, Dict, Any

class VectorStore(ABC):
    """Abstract interface for vector database stores (ChromaDB, Qdrant, etc.)."""

    @abstractmethod
    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """Add batch of vector points to collection."""
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        document_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search top_k nearest vector points filtered strictly by document_id."""
        pass

    @abstractmethod
    def delete_document(self, document_id: str) -> None:
        """Delete all vector points belonging to a specific document_id."""
        pass

    @abstractmethod
    def get_indexed_count(self, document_id: str) -> int:
        """Count indexed vector points for a specific document_id."""
        pass
