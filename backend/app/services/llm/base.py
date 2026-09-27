from abc import ABC, abstractmethod


class LLMService(ABC):
    """Abstract Base Class for LLM Provider implementations."""

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Generate response text from system instructions and user prompt.
        
        Args:
            system_prompt: High-priority system grounding instructions.
            user_prompt: User question combined with retrieved document context.

        Returns:
            Generated response string.
        """
        raise NotImplementedError
