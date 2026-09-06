import pytest

from app.services.ai.errors import LlmResponseError
from app.services.ai.grounding import quote_is_grounded, ungrounded_quotes
from app.services.ai.parse import parse_diagnosis_json
from app.services.ai.schema import DiagnosisOutput

VALID = {
    "root_cause": "VLAN 30 is missing from the VLAN database.",
    "confidence": 0.8,
    "confidence_label": "high",
    "osi_layer": "L2",
    "concept_tag": "vlan",
    "severity": "high",
    "evidence": [
        {
            "quote": "Access Mode VLAN: 30 (Inactive)",
            "command": "show interfaces fa0/24 switchport",
            "why": "Server port VLAN is inactive.",
        }
    ],
    "next_command": "show vlan brief",
    "next_commands": ["show interfaces trunk"],
    "fix_steps": ["Create VLAN 30 on S1."],
    "verification_command": "ping 192.168.30.10",
}

SHOW = """
S1# show interfaces fa0/24 switchport
Access Mode VLAN: 30 (Inactive)
"""


def test_parse_accepts_schema_valid_json() -> None:
    output = parse_diagnosis_json(__import__("json").dumps(VALID))
    assert output.concept_tag.value == "vlan"
    assert output.next_command in output.next_commands
    assert output.verification_command.startswith("ping")


def test_parse_accepts_concept_alias() -> None:
    payload = dict(VALID)
    payload.pop("concept_tag")
    payload["concept"] = "vlan"
    output = parse_diagnosis_json(__import__("json").dumps(payload))
    assert output.concept_tag.value == "vlan"


def test_parse_extracts_json_from_fenced_text() -> None:
    raw = "Here is the diagnosis:\n```json\n" + __import__("json").dumps(VALID) + "\n```\n"
    output = parse_diagnosis_json(raw)
    assert output.concept_tag.value == "vlan"


def test_parse_rejects_malformed_json() -> None:
    with pytest.raises(LlmResponseError) as exc:
        parse_diagnosis_json("not json {")
    assert exc.value.status_code == 422


def test_parse_rejects_missing_required_fields() -> None:
    payload = dict(VALID)
    del payload["fix_steps"]
    with pytest.raises(LlmResponseError):
        parse_diagnosis_json(__import__("json").dumps(payload))


def test_grounding_accepts_real_quote_and_rejects_paraphrase() -> None:
    output = DiagnosisOutput.model_validate(VALID)
    assert quote_is_grounded(output.evidence[0].quote, SHOW)
    assert ungrounded_quotes(output, SHOW) == []
    fake = output.model_copy(
        update={
            "evidence": [
                output.evidence[0].model_copy(update={"quote": "VLAN thirty seems gone"})
            ]
        }
    )
    assert ungrounded_quotes(fake, SHOW)
