import logging
from typing import Optional
from fastapi import HTTPException, status
from app.core.config import settings
from app.services.llm.base import LLMService

logger = logging.getLogger(__name__)


class GeminiLLMService(LLMService):
    """Google Gemini LLM Service implementation with model fallback support."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        fallback_models: Optional[list[str]] = None,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self.fallback_models = fallback_models if fallback_models is not None else settings.fallback_models_list
        self.temperature = temperature if temperature is not None else settings.GEMINI_TEMPERATURE
        self.max_output_tokens = max_output_tokens if max_output_tokens is not None else settings.GEMINI_MAX_OUTPUT_TOKENS

        # Deduplicate models list preserving order
        all_models = [self.model_name] + [m for m in self.fallback_models if m != self.model_name]
        self.candidate_models = list(dict.fromkeys(all_models))

    def _get_client(self):
        """Lazy initialization of the google-genai Client."""
        if not self.api_key or not self.api_key.strip():
            logger.error("Gemini API key is not configured.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gemini LLM Provider is not configured. GEMINI_API_KEY is missing on backend."
            )
        try:
            from google import genai
            return genai.Client(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize google-genai client: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize Gemini LLM client: {str(e)}"
            )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Generate text response from Gemini with model fallback handling."""
        client = self._get_client()

        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
        )

        last_error = None
        for model in self.candidate_models:
            try:
                logger.info(f"Sending prompt to Gemini model: {model}")
                response = client.models.generate_content(
                    model=model,
                    contents=user_prompt,
                    config=config,
                )
                if response and response.text:
                    return response.text.strip()
                elif response and response.candidates and response.candidates[0].content:
                    parts = response.candidates[0].content.parts
                    if parts and len(parts) > 0 and hasattr(parts[0], 'text'):
                        return parts[0].text.strip()
                
                logger.warning(f"Model {model} returned empty response text, attempting fallback if available.")
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Gemini generation error with model '{model}': {error_msg}")
                last_error = e
                # If error indicates quota/rate limit/429/404 model not found, try fallback
                if any(term in error_msg.lower() for term in ["429", "quota", "limit", "resource_exhausted", "not found", "invalid"]):
                    continue
                else:
                    # For non-recoverable client error, break to fallback or raise
                    continue

        # If all candidates failed
        logger.error(f"All Gemini candidate models failed. Detailed technical exception: {repr(last_error)}")

        if last_error and ("quota" in str(last_error).lower() or "429" in str(last_error)):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Gemini service is experiencing high load or quota limits. Please try again in a moment."
            )
        
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to generate response from document intelligence service. Please check configuration or try again shortly."
        )

