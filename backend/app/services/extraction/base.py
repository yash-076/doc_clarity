from abc import ABC, abstractmethod
from typing import List
from app.schemas.processing import ExtractedContent

class DocumentExtractor(ABC):
    """Abstract interface for format-specific document extractors."""

    @abstractmethod
    def extract(self, file_path: str) -> List[ExtractedContent]:
        """Extract structured text elements from document file."""
        pass
