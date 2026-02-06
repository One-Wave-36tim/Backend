import json
from typing import Any, cast

import httpx

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
        self._api_key = settings.gemini_api_key
        self._model = settings.gemini_model
        self._client: Any | None = None
        try:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)
        except ModuleNotFoundError:
            self._client = None

    def _generate_with_http(self, prompt: str) -> str:
        if self._model.startswith("models/"):
            model_name = self._model.split("/", 1)[1]
        else:
            model_name = self._model
        url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent"
        params = {"key": self._api_key}
        payload: dict[str, Any] = {"contents": [{"parts": [{"text": prompt}]}]}
        with httpx.Client(timeout=30) as client:
            response = client.post(url, params=params, json=payload)
            response.raise_for_status()
            data = response.json()
        try:
            return str(data["candidates"][0]["content"]["parts"][0]["text"])
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Gemini HTTP response parse failed") from exc

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        prompt = f"{system_prompt}\n\n{user_prompt}"
        if self._client is not None:
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
        else:
            text = self._generate_with_http(prompt)
        return _parse_json(text)
