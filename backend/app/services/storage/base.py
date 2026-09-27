from abc import ABC, abstractmethod
from typing import BinaryIO

class StorageProvider(ABC):
    """Abstract base class for document storage services (Local FS, S3, MinIO, etc.)."""
    
    @abstractmethod
    async def save(self, file_data: BinaryIO, filename: str) -> str:
        """Save file content and return relative storage path."""
        pass

    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        """Delete physical file from storage."""
        pass

    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        """Check if file exists in storage."""
        pass
