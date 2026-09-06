import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.diagnoses import _service
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.tables import Case, Diagnosis, RaiEvent
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
    def complete_json(self, system: str, user: str) -> str:
        return json.dumps(VALID)


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


def _diagnose(app, Session, case_id: int) -> int:
    def override_service():
        db = Session()
        try:
            yield DiagnosisService(db, llm=FakeLlm())
        finally:
            db.close()

    app.dependency_overrides[_service] = override_service
    client = TestClient(app)
    response = client.post(f"/api/v1/cases/{case_id}/diagnoses")
    assert response.status_code == 200
    return response.json()["id"]


def test_review_queue_lists_pending_then_clears_after_accept() -> None:
    client, Session, app = _app_client()
    case = _seed_vlan(Session)
    diagnosis_id = _diagnose(app, Session, case.id)
    queue = client.get("/api/v1/reviews/queue")
    assert queue.status_code == 200
    assert queue.json()["total"] == 1
    assert queue.json()["items"][0]["diagnosis_id"] == diagnosis_id

    accepted = client.post(
        f"/api/v1/diagnoses/{diagnosis_id}/reviews",
        json={"verdict": "accepted", "reviewer_name": "Ada"},
    )
    assert accepted.status_code == 200
    body = accepted.json()
    assert body["verdict"] == "accepted"
    assert body["original_ai"]["raw_response"]
    assert body["rai_event_id"] is None
    assert client.get("/api/v1/reviews/queue").json()["total"] == 0
    assert client.get("/api/v1/rai-events").json()["total"] == 0


def test_edit_and_reject_appear_in_rai_and_analytics() -> None:
    client, Session, app = _app_client()
    case = _seed_vlan(Session)
    first = _diagnose(app, Session, case.id)
    edited = client.post(
        f"/api/v1/diagnoses/{first}/reviews",
        json={
            "verdict": "edited",
            "reviewer_name": "Ada",
            "correction_reason": "Wrong VLAN conclusion.",
            "corrected_root_cause": "Access port is in VLAN 10.",
            "corrected_osi_layer": "L2",
            "corrected_concept_tag": "vlan",
            "corrected_fix_steps": ["Assign Fa0/24 to VLAN 30."],
            "failure_class": "wrong_concept",
        },
    )
    assert edited.status_code == 200
    assert edited.json()["rai_event_id"] is not None

    second = _diagnose(app, Session, case.id)
    rejected = client.post(
        f"/api/v1/diagnoses/{second}/reviews",
        json={
            "verdict": "rejected",
            "correction_reason": "Does not match the show output.",
            "failure_class": "hallucinated_evidence",
        },
    )
    assert rejected.status_code == 200

    rai = client.get("/api/v1/rai-events")
    assert rai.status_code == 200
    payload = rai.json()
    assert payload["total"] == 2
    classes = {item["failure_class"] for item in payload["items"]}
    assert classes == {"wrong_concept", "hallucinated_evidence"}
    assert all(item["ai_snapshot_json"].get("raw_response") for item in payload["items"])
    assert all(item["human_correction_json"].get("correction_reason") for item in payload["items"])
    assert all(item["verdict"] in {"edited", "rejected"} for item in payload["items"])

    analytics = client.get("/api/v1/analytics/summary")
    assert analytics.status_code == 200
    summary = analytics.json()
    assert summary["reviewed_count"] == 2
    assert summary["rai_event_count"] == 2
    verdicts = {item["key"]: item["count"] for item in summary["review_verdicts"]}
    assert verdicts["edited"] == 1
    assert verdicts["rejected"] == 1
    assert summary["ai_human_agreement"]["sample_size"] == 2
    assert summary["ai_human_agreement"]["value"] == 0

    db = Session()
    try:
        assert db.scalar(select(RaiEvent).where(RaiEvent.case_id == case.id)) is not None
        statuses = [row.status for row in db.scalars(select(Diagnosis)).all()]
        assert "pending_review" not in statuses
    finally:
        db.close()


def test_edit_without_corrections_is_rejected() -> None:
    client, Session, app = _app_client()
    case = _seed_vlan(Session)
    diagnosis_id = _diagnose(app, Session, case.id)
    response = client.post(
        f"/api/v1/diagnoses/{diagnosis_id}/reviews",
        json={"verdict": "edited", "correction_reason": "nope"},
    )
    assert response.status_code == 422
