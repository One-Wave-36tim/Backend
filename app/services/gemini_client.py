import json
from typing import Any, cast

from app.core.config import get_settings


def _extract_text(response: Any) -> str:
    if getattr(response, "text", None):
        return str(response.text)

    candidates = getattr(response, "candidates", None) or []
    if candidates:
        content = getattr(candidates[0], "content", None)
        parts = getattr(content, "parts", None) or []
        if parts and getattr(parts[0], "text", None):
            return str(parts[0].text)

    raise ValueError("Gemini response did not contain text")


def _parse_json(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
        return cast(dict[str, Any], parsed)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(text[start : end + 1])
        return cast(dict[str, Any], parsed)


class GeminiClient:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is missing")

        try:
            from google import genai
        except ModuleNotFoundError as exc:  # pragma: no cover - local env dependency.
            raise RuntimeError(
                "google-genai dependency is missing. Install it to use Gemini features."
            ) from exc

        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

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
