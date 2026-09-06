import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.diagnoses import _service
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.tables import Case
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
        return self.raw


def _app_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_db
    return TestClient(app), TestingSession, app


def _seed_vlan(Session) -> Case:
    db = Session()
    try:
        payload = next(item for item in catalog_payloads() if item.case_code == "VLAN-001")
        case = Case(**payload.model_dump(mode="json"))
        db.add(case)
        db.commit()
        db.refresh(case)
        return case
    finally:
        db.close()


def test_diagnose_fails_closed_without_api_key(monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LLM_API_KEY", "")
    get_settings.cache_clear()
    client, Session, _app = _app_client()
    case = _seed_vlan(Session)
    try:
        response = client.post(f"/api/v1/cases/{case.id}/diagnoses")
        assert response.status_code == 503
        body = response.json()
        assert body["error"]["code"] == "llm_unavailable"
        assert "invent" in body["error"]["message"].lower() or "not set" in body["error"]["message"].lower()
    finally:
        get_settings.cache_clear()


def test_diagnose_endpoint_validates_and_returns_pending_review() -> None:
    client, Session, app = _app_client()
    case = _seed_vlan(Session)

    def override_service():
        db = Session()
        try:
            yield DiagnosisService(db, llm=FakeLlm(json.dumps(VALID)))
        finally:
            db.close()

    app.dependency_overrides[_service] = override_service
    response = client.post(f"/api/v1/cases/{case.id}/diagnoses")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending_review"
    assert body["root_cause"]
    assert body["verification_command"] == "ping 192.168.30.10"
    assert body["severity"] == "high"
    assert body["grounded"] is True
    assert body["next_command"] == "show vlan brief"
    assert body["concept"] == "vlan"
    assert body["concept_tag"] == "vlan"
    fetched = client.get(f"/api/v1/diagnoses/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


def test_diagnose_endpoint_rejects_malformed_json() -> None:
    client, Session, app = _app_client()
    case = _seed_vlan(Session)

    def override_service():
        db = Session()
        try:
            yield DiagnosisService(db, llm=FakeLlm("this is not json"))
        finally:
            db.close()

    app.dependency_overrides[_service] = override_service
    response = client.post(f"/api/v1/cases/{case.id}/diagnoses")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "llm_response_invalid"
