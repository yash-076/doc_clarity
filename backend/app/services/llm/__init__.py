from app.services.llm.base import LLMService
from app.services.llm.gemini_service import GeminiLLMService
from app.core.config import settings


def get_llm_service() -> LLMService:
    """Factory to get the configured LLM provider service instance."""
    provider = settings.LLM_PROVIDER.lower()
    if provider == "gemini":
        return GeminiLLMService()
    else:
        # Default fallback to Gemini
        return GeminiLLMService()


__all__ = ["LLMService", "GeminiLLMService", "get_llm_service"]
