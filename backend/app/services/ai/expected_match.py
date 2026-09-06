from __future__ import annotations

import re

from app.services.ai.schema import DiagnosisOutput


def _tokens(text: str) -> set[str]:
    return {part for part in re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).split() if part}


def expected_match(expected_fault: str, case_concept: str, output: DiagnosisOutput) -> bool:
    if output.concept_tag.value == case_concept:
        return True
    expected = _tokens(expected_fault)
    predicted = _tokens(output.root_cause)
    if not expected or not predicted:
        return False
    overlap = len(expected & predicted) / float(len(expected))
    return overlap >= 0.3
