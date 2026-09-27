from typing import List, Optional
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging import logger
from app.services.embeddings.base import BaseEmbeddingService

class LocalEmbeddingService(BaseEmbeddingService):
    """Local SentenceTransformer embedding service supporting BAAI/bge-small-en-v1.5."""

    _model_instance: Optional[SentenceTransformer] = None

    def __init__(self, model_name: Optional[str] = None):
        self._model_name = model_name or settings.EMBEDDING_MODEL
        self._batch_size = settings.EMBEDDING_BATCH_SIZE
        self._expected_dimension = settings.EMBEDDING_DIMENSION

    def _get_model(self) -> SentenceTransformer:
        if LocalEmbeddingService._model_instance is None:
            logger.info(f"Loading local SentenceTransformer embedding model '{self._model_name}'...")
            LocalEmbeddingService._model_instance = SentenceTransformer(self._model_name)
            
            # Dimension sanity check
            test_vector = LocalEmbeddingService._model_instance.encode("test", normalize_embeddings=True)
            actual_dim = len(test_vector)
            if actual_dim != self._expected_dimension:
                logger.warning(
                    f"Configured EMBEDDING_DIMENSION ({self._expected_dimension}) differs from actual model dimension ({actual_dim})."
                )
        return LocalEmbeddingService._model_instance

    @property
    def dimension(self) -> int:
        return self._expected_dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        model = self._get_model()
        logger.info(f"Generating embeddings for {len(texts)} chunks using batch_size={self._batch_size}...")
        
        embeddings = model.encode(
            texts,
            batch_size=self._batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        if not text or not text.strip():
            raise ValueError("Query string cannot be empty.")

        model = self._get_model()
        # BGE models recommend query prefix for optimal retrieval
        query_input = text.strip()
        if "bge" in self._model_name.lower() and not query_input.startswith("Represent this sentence"):
            query_input = f"Represent this sentence for searching relevant passages: {query_input}"

        embedding = model.encode(
            query_input,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        return embedding.tolist()
