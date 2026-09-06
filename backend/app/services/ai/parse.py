from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from app.services.ai.errors import LlmResponseError
from app.services.ai.schema import DiagnosisOutput

_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def extract_json_object(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        raise LlmResponseError("AI response was empty")
    if text.startswith("{"):
        return text
    fenced = _FENCE_RE.search(text)
    if fenced:
        return fenced.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]
    raise LlmResponseError(
        "AI response was not valid JSON",
        details={"raw": text[:1000]},
    )


def parse_diagnosis_json(raw: str) -> DiagnosisOutput:
    try:
        payload: Any = json.loads(extract_json_object(raw))
    except json.JSONDecodeError as exc:
        raise LlmResponseError(
            "AI response was not valid JSON",
            details={"json_error": str(exc), "raw": raw[:1000]},
        ) from exc
    if not isinstance(payload, dict):
        raise LlmResponseError("AI response JSON must be an object", details=payload)
    try:
        return DiagnosisOutput.model_validate(payload)
    except ValidationError as exc:
        raise LlmResponseError(
            "AI JSON did not match the diagnosis schema",
            details=exc.errors(),
        ) from exc
