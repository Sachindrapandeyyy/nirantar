import json
import base64
import httpx
from typing import Any, Dict, Optional
from loguru import logger
from config.settings import settings
from brain.base import BaseLLMProvider
from brain.prompts import FORM_MAPPING_SYSTEM_PROMPT


class GeminiProvider(BaseLLMProvider):
    """
    High-speed, free-tier Gemini API client with native vision and JSON mode.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        # Using Gemini v1beta endpoint
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    async def generate_response(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2048
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(self.endpoint, json=payload)
                if response.status_code != 200:
                    logger.error(f"Gemini API error ({response.status_code}): {response.text}")
                    return ""
                
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return ""
            except Exception as e:
                logger.error(f"Gemini generation failed: {e}")
                return ""

    async def extract_form_mapping(
        self,
        form_fields_schema: Dict[str, Any],
        profile_data: Dict[str, Any],
        image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Maps form elements with high accuracy, optionally utilizing vision screenshot.
        """
        prompt = (
            f"Here is the candidate profile:\n{json.dumps(profile_data, indent=2)}\n\n"
            f"Here are the detected form elements on the career page:\n{json.dumps(form_fields_schema, indent=2)}\n\n"
            "Return a strictly valid JSON dictionary mapping element IDs/selectors to their values and action types."
        )

        parts: list = [{"text": prompt}]

        if image_bytes:
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            parts.append({
                "inlineData": {
                    "mimeType": "image/png",
                    "data": b64_image
                }
            })

        payload = {
            "contents": [{"parts": parts}],
            "systemInstruction": {"parts": [{"text": FORM_MAPPING_SYSTEM_PROMPT}]},
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        async with httpx.AsyncClient(timeout=40.0) as client:
            try:
                res = await client.post(self.endpoint, json=payload)
                if res.status_code != 200:
                    logger.error(f"Gemini form mapping error ({res.status_code}): {res.text}")
                    return {}
                
                raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_text)
            except Exception as e:
                logger.error(f"Form mapping parsing failed: {e}")
                return {}
