import json
from typing import Any

from google import genai

from app.core.config import get_settings


def _extract_text(response: Any) -> str:
    if getattr(response, "text", None):
        return response.text
    candidates = getattr(response, "candidates", None) or []
    if candidates:
        content = getattr(candidates[0], "content", None)
        parts = getattr(content, "parts", None) or []
        if parts and getattr(parts[0], "text", None):
            return parts[0].text
    raise ValueError("Gemini response did not contain text")


def _parse_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


class GeminiClient:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is missing")
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model or "models/gemini-2.5-flash"

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        prompt = f"{system_prompt}\n\n{user_prompt}"
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
        except TypeError:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
        text = _extract_text(response)
        return _parse_json(text)
