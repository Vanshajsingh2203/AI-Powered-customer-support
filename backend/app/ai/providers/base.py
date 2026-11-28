from abc import ABC, abstractmethod
from typing import Any

class BaseLLMProvider(ABC):
    """
    Common interface for all LLM providers.

    Provider-specific implementations (Gemini, etc.)
    must implement the generate method.
    """
    
    @abstractmethod
    async def generate(
        self,
        prompt:str,
        system_instruction:str |None = None,
        temperature :float = 0.2,
        response_scheme: dict[str, Any] |None = None,
    )-> str:
        """
        Generate a response from the configured language model.

        Args:
            prompt: User prompt sent to the model.
            system_instruction: Optional system-level instructions.
            temperature: Controls response randomness.
            response_schema: Optional structured JSON schema.

        Returns:
            Generated response as text.
        """
        
        raise NotImplementedError