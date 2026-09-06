from __future__ import annotations

import re
from typing import List

from app.services.ai.schema import DiagnosisOutput, EvidenceItem


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def quote_is_grounded(quote: str, show_outputs: str) -> bool:
    haystack = normalize_ws(show_outputs)
    needle = normalize_ws(quote)
    return bool(needle) and needle in haystack


def ungrounded_quotes(output: DiagnosisOutput, show_outputs: str) -> List[EvidenceItem]:
    return [item for item in output.evidence if not quote_is_grounded(item.quote, show_outputs)]
