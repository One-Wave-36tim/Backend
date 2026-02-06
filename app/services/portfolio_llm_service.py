from typing import Any

import httpx


def call_gemini(prompt: str, model: str | None, api_key: str) -> str:
    model_name = model or "models/gemini-2.5-flash"
    if model_name.startswith("models/"):
        model_name = model_name.split("/", 1)[1]

    url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent"
    params = {"key": api_key}
    payload: dict[str, Any] = {"contents": [{"parts": [{"text": prompt}]}]}

    with httpx.Client(timeout=30) as client:
        response = client.post(url, params=params, json=payload)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Gemini API 오류: {response.status_code} {response.text}") from exc
        data = response.json()

    try:
        value = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Gemini 응답을 파싱할 수 없습니다.") from exc

    return str(value)
