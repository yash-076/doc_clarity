import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Doc Clarity"
    VERSION: str = "3.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/doc_clarity"
    
    # File Upload Settings
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    MAX_FILE_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx", ".txt"}
    
    # Allowed MIME Types
    ALLOWED_MIME_TYPES: set[str] = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/msword",
    }
    
    # Mock User ID for Phase 1, 2 & 3
    MOCK_USER_ID: str = "00000000-0000-0000-0000-000000000001"
    
    # Phase 2: OCR Settings
    TESSERACT_CMD: str = ""
    OCR_ENABLED: bool = True
    OCR_LANGUAGE: str = "eng"
    OCR_MIN_TEXT_CHARS: int = 50
    OCR_DPI: int = 200

    # Phase 2: Chunking Settings
    CHUNK_SIZE: int = 800       # Target ~800 tokens (~3200 characters)
    CHUNK_OVERLAP: int = 100     # Target ~100 tokens (~400 characters)

    # Phase 3: Embedding Model Settings
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 32

    # Phase 3: ChromaDB Configuration
    CHROMA_PERSIST_DIRECTORY: Path = BASE_DIR / "data" / "chroma"
    CHROMA_COLLECTION_NAME: str = "document_chunks"

    # Phase 3: Retrieval Settings
    DEFAULT_TOP_K: int = 5
    MAX_TOP_K: int = 20

    # Phase 4: RAG & LLM Settings
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_FALLBACK_MODELS: str = "gemini-2.0-flash,gemini-1.5-flash,gemini-1.5-pro"
    GEMINI_TEMPERATURE: float = 0.1
    GEMINI_MAX_OUTPUT_TOKENS: int = 1000

    DEFAULT_RAG_TOP_K: int = 5
    MAX_RAG_TOP_K: int = 10
    MAX_CONTEXT_CHARS: int = 12000

    # Phase 5: Analysis Settings
    ANALYSIS_TOP_K: int = 5
    ANALYSIS_MAX_CHUNKS: int = 30
    ANALYSIS_MAX_CONTEXT_CHARS: int = 30000

    # Phase 6: Guided Questions & Conversation Settings
    SUGGESTED_QUESTION_COUNT: int = 6
    MAX_SUGGESTED_QUESTIONS: int = 10
    MAX_CONVERSATION_MESSAGES: int = 10
    MAX_CONVERSATION_CONTEXT_CHARS: int = 6000

    @property
    def fallback_models_list(self) -> list[str]:
        if not self.GEMINI_FALLBACK_MODELS:
            return []
        return [m.strip() for m in self.GEMINI_FALLBACK_MODELS.split(",") if m.strip()]

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
