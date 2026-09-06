import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.exceptions import ConflictError
from app.models.tables import Case, Diagnosis, RuleRun
from app.services.ai.errors import LlmResponseError, LlmUnavailableError
from app.services.ai.service import DiagnosisService
from app.services.seed import catalog_payloads

VALID = {
    "root_cause": "VLAN 30 is missing from the VLAN database so the server port is inactive.",
    "confidence": 0.84,
    "confidence_label": "high",
    "osi_layer": "L2",
    "concept_tag": "vlan",
    "severity": "high",
    "evidence": [
        {
            "quote": "Access Mode VLAN: 30 (Inactive)",
            "command": "show interfaces fa0/24 switchport",
            "why": "The access VLAN is inactive.",
        }
    ],
    "next_command": "show vlan brief",
    "next_commands": [],
    "fix_steps": ["Create VLAN 30.", "Recheck the access port."],
    "verification_command": "ping 192.168.30.10",
}


class FakeLlm:
    def __init__(self, raw: str):
        self.raw = raw

    def complete_json(self, system: str, user: str) -> str:
        assert "Symptom" in user
        assert "Show-command evidence" in user
        assert "Deterministic rule results" in user
        assert "JSON" in system or "json" in system.lower()
        return self.raw


def _session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    return TestingSession()


def _seed_vlan_case(db) -> Case:
    payload = next(item for item in catalog_payloads() if item.case_code == "VLAN-001")
    case = Case(**payload.model_dump(mode="json"))
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def test_service_persists_pending_review_from_valid_model_output() -> None:
    db = _session()
    case = _seed_vlan_case(db)
    service = DiagnosisService(db, llm=FakeLlm(json.dumps(VALID)))
    row = service.diagnose(case.id)
    assert row.status == "pending_review"
    assert row.grounded is True
    assert row.verification_command == "ping 192.168.30.10"
    assert row.severity == "high"
    assert row.expected_match is True


def test_service_rejects_malformed_model_output() -> None:
    db = _session()
    case = _seed_vlan_case(db)
    service = DiagnosisService(db, llm=FakeLlm("sorry, here is prose"))
    try:
        service.diagnose(case.id)
        assert False, "expected LlmResponseError"
    except LlmResponseError as exc:
        assert exc.status_code == 422
    assert db.scalar(select(Diagnosis)) is None


def test_service_rejects_second_pending_diagnosis() -> None:
    db = _session()
    case = _seed_vlan_case(db)
    DiagnosisService(db, llm=FakeLlm(json.dumps(VALID))).diagnose(case.id)
    try:
        DiagnosisService(db, llm=FakeLlm(json.dumps(VALID))).diagnose(case.id)
        assert False, "expected ConflictError"
    except ConflictError as exc:
        assert exc.status_code == 409


def test_missing_api_key_fails_closed_without_rule_or_diagnosis_rows(monkeypatch) -> None:
    from app.config import get_settings

    db = _session()
    case = _seed_vlan_case(db)
    get_settings.cache_clear()
    monkeypatch.setenv("LLM_API_KEY", "")
    get_settings.cache_clear()
    try:
        try:
            DiagnosisService(db).diagnose(case.id)
            assert False, "expected LlmUnavailableError"
        except LlmUnavailableError as exc:
            assert exc.status_code == 503
        assert db.scalar(select(Diagnosis)) is None
        assert db.scalar(select(RuleRun)) is None
    finally:
        get_settings.cache_clear()


def test_service_persists_ungrounded_flag_for_paraphrased_quote() -> None:
    db = _session()
    case = _seed_vlan_case(db)
    payload = dict(VALID)
    payload["evidence"] = [
        {
            "quote": "VLAN thirty is mysteriously gone from the switch",
            "command": "show vlan brief",
            "why": "Paraphrase that is not in the evidence.",
        }
    ]
    row = DiagnosisService(db, llm=FakeLlm(json.dumps(payload))).diagnose(case.id)
    assert row.status == "pending_review"
    assert row.grounded is False
