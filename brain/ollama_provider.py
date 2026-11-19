import json
import httpx
from typing import Any, Dict, Optional
from loguru import logger
from config.settings import settings
from brain.base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """
    Offline local LLM provider running on RTX 4050 GPU (e.g. Qwen 2.5 7B).
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    async def generate_response(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_instruction or "",
            "stream": False
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    return res.json().get("response", "")
                return ""
            except Exception as e:
                logger.warning(f"Ollama local connection failed: {e}")
                return ""

    async def extract_form_mapping(
        self,
        form_fields_schema: Dict[str, Any],
        profile_data: Dict[str, Any],
        image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        prompt = (
            f"Candidate Profile: {json.dumps(profile_data)}\n"
            f"Form Fields: {json.dumps(form_fields_schema)}\n"
            "Return JSON mapping element ID to filled value strictly based on the profile."
        )
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    return json.loads(res.json().get("response", "{}"))
                return {}
            except Exception as e:
                logger.warning(f"Ollama form extraction failed: {e}")
                return {}
