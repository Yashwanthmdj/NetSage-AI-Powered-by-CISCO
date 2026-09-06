from __future__ import annotations

import json
from typing import Sequence

from app.models.tables import Case
from app.services.rules.result import RuleResult


def build_user_message(case: Case, rule_results: Sequence[RuleResult]) -> str:
    rules_payload = [item.model_dump() for item in rule_results]
    return "\n".join(
        [
            "Diagnose this Packet Tracer case using only the blocks below.",
            "",
            "## Symptom",
            case.symptom,
            "",
            "## Topology notes",
            case.topology_note,
            "",
            "## Show-command evidence",
            case.show_outputs,
            "",
            "## Deterministic rule results",
            json.dumps(rules_payload, indent=2),
            "",
            "Return the diagnosis JSON object now.",
        ]
    )
