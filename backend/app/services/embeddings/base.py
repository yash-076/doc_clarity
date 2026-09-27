from abc import ABC, abstractmethod
from typing import List

class BaseEmbeddingService(ABC):
    """Abstract interface for text embedding models."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate dense vector embeddings for a list of document chunk texts."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate a dense vector embedding for a single user search query."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return expected embedding vector dimension."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return embedding model identifier string."""
        pass
