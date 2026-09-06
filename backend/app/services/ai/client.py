from __future__ import annotations

from typing import Any, Protocol

import httpx

from app.config import get_settings
from app.services.ai.errors import LlmResponseError, LlmUnavailableError


class LlmClient(Protocol):
    def complete_json(self, system: str, user: str) -> str: ...


class OpenAICompatibleClient:
    def ensure_ready(self) -> None:
        settings = get_settings()
        if not settings.llm_api_key:
            raise LlmUnavailableError(
                "LLM_API_KEY is not set. Diagnosis fails closed and will not invent an answer."
            )

    def complete_json(self, system: str, user: str) -> str:
        self.ensure_ready()
        settings = get_settings()
        url = settings.llm_base_url.rstrip("/") + "/chat/completions"
        payload: dict[str, Any] = {
            "model": settings.llm_model,
            "temperature": 0,
            "max_tokens": settings.llm_max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if settings.llm_json_object:
            payload["response_format"] = {"type": "json_object"}
        if settings.llm_enable_thinking:
            payload["chat_template_kwargs"] = {"enable_thinking": True}
        headers = {
            "Authorization": "Bearer %s" % settings.llm_api_key,
            "Content-Type": "application/json",
        }
        last_error: Exception | None = None
        response = None
        for attempt in range(3):
            try:
                with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
                    response = client.post(url, json=payload, headers=headers)
            except httpx.HTTPError as exc:
                last_error = exc
                continue
            if response.status_code >= 500:
                last_error = LlmUnavailableError(
                    "LLM provider returned %s" % response.status_code,
                    details=response.text[:500],
                )
                continue
            break
        if response is None:
            raise LlmUnavailableError("LLM request failed: %s" % last_error) from last_error
        if response.status_code >= 500:
            raise last_error or LlmUnavailableError(
                "LLM provider returned %s" % response.status_code,
                details=response.text[:500],
            )
        if response.status_code >= 400:
            raise LlmUnavailableError(
                "LLM provider rejected the request (%s)" % response.status_code,
                details=response.text[:500],
            )
        try:
            body = response.json()
        except ValueError as exc:
            raise LlmResponseError("LLM returned non-JSON transport payload") from exc
        content = _message_text(body)
        if not content:
            raise LlmResponseError("LLM returned an empty message", details=body)
        return content


def _message_text(body: object) -> str:
    try:
        message = body["choices"][0]["message"]  # type: ignore[index]
    except (KeyError, IndexError, TypeError) as exc:
        raise LlmResponseError("LLM response is missing choices[0].message", details=body) from exc
    content = message.get("content") if isinstance(message, dict) else None
    if content and str(content).strip():
        return str(content)
    reasoning = message.get("reasoning_content") if isinstance(message, dict) else None
    if reasoning and str(reasoning).strip():
        return str(reasoning)
    return ""
