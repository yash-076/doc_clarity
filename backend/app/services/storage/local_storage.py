import os
from pathlib import Path
from typing import BinaryIO
from app.core.config import settings
from app.core.logging import logger
from app.services.storage.base import StorageProvider

class LocalFileStorage(StorageProvider):
    """Local filesystem implementation of StorageProvider."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = (base_dir or settings.UPLOAD_DIR).resolve()
        # Ensure uploads directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, filename_or_path: str) -> Path:
        """Resolve path and verify it stays within base_dir to prevent path traversal."""
        # Sanitize filename / relative path
        clean_name = Path(filename_or_path).name
        target_path = (self.base_dir / clean_name).resolve()
        if not str(target_path).startswith(str(self.base_dir)):
            logger.warning(f"Path traversal attempt blocked: {filename_or_path}")
            raise ValueError("Invalid target path detected.")
        return target_path

    async def save(self, file_data: BinaryIO, filename: str) -> str:
        target_path = self._resolve_safe_path(filename)
        
        # Rewind buffer to beginning
        file_data.seek(0)
        
        # Write bytes synchronously or via chunked stream
        with open(target_path, "wb") as f:
            while chunk := file_data.read(8192):
                f.write(chunk)
                
        logger.info(f"File safely saved to local storage: {target_path}")
        return str(target_path)

    async def delete(self, file_path: str) -> bool:
        try:
            target_path = Path(file_path).resolve()
            # Double check bounds
            if not str(target_path).startswith(str(self.base_dir)):
                logger.warning(f"Deletion path out of bounds: {file_path}")
                return False

            if target_path.exists() and target_path.is_file():
                target_path.unlink()
                logger.info(f"File deleted successfully from storage: {target_path}")
                return True
            else:
                logger.warning(f"File not found during deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file from local storage ({file_path}): {str(e)}")
            return False

    async def exists(self, file_path: str) -> bool:
        try:
            target_path = Path(file_path).resolve()
            return target_path.exists() and target_path.is_file()
        except Exception:
            return False
