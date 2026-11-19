from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers (Gemini Cloud vs Ollama Local)."""

    @abstractmethod
    async def generate_response(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generates plain text response."""
        pass

    @abstractmethod
    async def extract_form_mapping(
        self,
        form_fields_schema: Dict[str, Any],
        profile_data: Dict[str, Any],
        image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """Maps web form fields to verified user data."""
        pass
