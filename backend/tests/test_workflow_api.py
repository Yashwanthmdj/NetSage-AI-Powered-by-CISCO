import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.diagnoses import _service
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.services.ai.service import DiagnosisService

VALID = {
    "root_cause": "Duplicate IPv4 address 10.1.1.1 is configured on two routers.",
    "confidence": 0.9,
    "confidence_label": "high",
    "osi_layer": "L3",
    "concept_tag": "routing",
    "severity": "high",
    "evidence": [
        {
            "quote": "GigabitEthernet0/0     10.1.1.1        YES manual up                    up",
            "command": "show ip interface brief",
            "why": "The same address appears on two devices.",
        }
    ],
    "next_command": "show ip interface brief",
    "next_commands": [],
    "fix_steps": ["Change R2 to 10.1.1.2."],
    "verification_command": "ping 10.1.1.2",
}

NEW_CASE = {
    "case_code": "LAB-001",
    "title": "Duplicate WAN address",
    "symptom": "Two routers share 10.1.1.1 and the WAN is unstable.",
    "topology_note": "R1 and R2 connected on a /30.",
    "show_outputs": """
R1# show ip interface brief
GigabitEthernet0/0     10.1.1.1        YES manual up                    up
R2# show ip interface brief
GigabitEthernet0/0     10.1.1.1        YES manual up                    up
""".strip(),
    "expected_fault": "Duplicate IP on the WAN link.",
    "osi_layer": "L3",
    "concept_tag": "routing",
    "severity": "high",
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


def test_create_rules_diagnose_review_verify_updates_analytics() -> None:
    client, Session, app = _app_client()

    created = client.post("/api/v1/cases", json=NEW_CASE)
    assert created.status_code == 201
    case = created.json()
    assert case["case_code"] == "LAB-001"
    assert case["lifecycle_status"] == "imported"
    case_id = case["id"]

    rules = client.post(f"/api/v1/cases/{case_id}/rules", json={})
    assert rules.status_code == 200
    assert rules.json()["rule_run_id"]
    assert rules.json()["fail_count"] >= 1
    dup = next(item for item in rules.json()["results"] if item["rule_name"] == "DUP_IP")
    assert dup["status"] == "fail"

    def override_service():
        db = Session()
        try:
            yield DiagnosisService(db, llm=FakeLlm())
        finally:
            db.close()

    app.dependency_overrides[_service] = override_service
    diagnosis = client.post(f"/api/v1/cases/{case_id}/diagnoses")
    assert diagnosis.status_code == 200
    assert diagnosis.json()["status"] == "pending_review"
    diagnosis_id = diagnosis.json()["id"]

    too_early = client.post(
        f"/api/v1/cases/{case_id}/verifications",
        json={"verified_by": "Ada", "notes": "too soon"},
    )
    assert too_early.status_code == 409

    review = client.post(
        f"/api/v1/diagnoses/{diagnosis_id}/reviews",
        json={"verdict": "accepted", "reviewer_name": "Ada"},
    )
    assert review.status_code == 200
    assert review.json()["verdict"] == "accepted"
    review_id = review.json()["id"]

    blocked_verify = client.post(
        f"/api/v1/cases/{case_id}/verifications",
        json={"verified_by": "Ada", "notes": "fix not applied"},
    )
    assert blocked_verify.status_code == 409

    applied = client.post(
        f"/api/v1/reviews/{review_id}/apply-fix",
        json={"applied_by": "Ada"},
    )
    assert applied.status_code == 200
    assert applied.json()["fix_applied"] is True

    verified = client.post(
        f"/api/v1/cases/{case_id}/verifications",
        json={"verified_by": "Ada", "notes": "ping 10.1.1.2 succeeded"},
    )
    assert verified.status_code == 201
    assert verified.json()["verified_by"] == "Ada"

    again = client.post(
        f"/api/v1/cases/{case_id}/verifications",
        json={"verified_by": "Ada"},
    )
    assert again.status_code == 409

    detail = client.get(f"/api/v1/cases/by-code/LAB-001")
    assert detail.status_code == 200
    body = detail.json()
    assert body["lifecycle_status"] == "verified"
    assert body["latest_rule_run"]["id"]
    assert body["latest_diagnosis"]["id"] == diagnosis_id
    assert body["latest_review"]["verdict"] == "accepted"
    assert body["latest_verification"]["notes"] == "ping 10.1.1.2 succeeded"

    analytics = client.get("/api/v1/analytics/summary")
    assert analytics.status_code == 200
    summary = analytics.json()
    assert summary["case_count"] >= 1
    assert summary["diagnosed_count"] >= 1
    assert summary["reviewed_count"] >= 1
    assert summary["verified_count"] >= 1
    assert summary["pending_review_count"] == 0
    assert summary["accepted_count"] >= 1
    assert summary["unresolved_count"] == summary["case_count"] - summary["verified_count"]
    assert summary["verification_success"]["sample_size"] >= 1
    assert summary["verification_success"]["value"] == 1.0


def test_verified_case_keeps_verified_diagnosis_when_newer_pending_exists() -> None:
    client, Session, app = _app_client()
    case_id = client.post("/api/v1/cases", json=NEW_CASE).json()["id"]

    def override_service():
        db = Session()
        try:
            yield DiagnosisService(db, llm=FakeLlm())
        finally:
            db.close()

    app.dependency_overrides[_service] = override_service
    first = client.post(f"/api/v1/cases/{case_id}/diagnoses")
    assert first.status_code == 200
    first_id = first.json()["id"]
    first_raw = first.json()["raw_response"]

    review = client.post(
        f"/api/v1/diagnoses/{first_id}/reviews",
        json={"verdict": "accepted", "reviewer_name": "Ada"},
    )
    assert review.status_code == 200
    review_id = review.json()["id"]
    assert review.json()["original_ai"]["raw_response"] == first_raw

    assert client.post(f"/api/v1/reviews/{review_id}/apply-fix", json={"applied_by": "Ada"}).status_code == 200
    verified = client.post(
        f"/api/v1/cases/{case_id}/verifications",
        json={"verified_by": "Ada", "notes": "ping succeeded"},
    )
    assert verified.status_code == 201
    verification_id = verified.json()["id"]

    second = client.post(f"/api/v1/cases/{case_id}/diagnoses")
    assert second.status_code == 200
    second_id = second.json()["id"]
    assert second.json()["status"] == "pending_review"
    assert second_id != first_id

    detail = client.get("/api/v1/cases/by-code/LAB-001").json()
    assert detail["lifecycle_status"] == "verified"
    assert detail["latest_diagnosis"]["id"] == first_id
    assert detail["latest_diagnosis"]["status"] == "accepted"
    assert detail["latest_diagnosis"]["raw_response"] == first_raw
    assert detail["latest_review"]["id"] == review_id
    assert detail["latest_review"]["verdict"] == "accepted"
    assert detail["latest_review"]["fix_applied"] is True
    assert detail["latest_verification"]["id"] == verification_id

    stored_first = client.get(f"/api/v1/diagnoses/{first_id}").json()
    assert stored_first["raw_response"] == first_raw
    assert stored_first["status"] == "accepted"
    stored_second = client.get(f"/api/v1/diagnoses/{second_id}").json()
    assert stored_second["status"] == "pending_review"
    assert client.get("/api/v1/reviews/queue").json()["total"] == 1


def test_rejected_review_cannot_be_verified() -> None:
    client, Session, app = _app_client()
    case_id = client.post("/api/v1/cases", json=NEW_CASE).json()["id"]

    def override_service():
        db = Session()
        try:
            yield DiagnosisService(db, llm=FakeLlm())
        finally:
            db.close()

    app.dependency_overrides[_service] = override_service
    diagnosis_id = client.post(f"/api/v1/cases/{case_id}/diagnoses").json()["id"]
    client.post(
        f"/api/v1/diagnoses/{diagnosis_id}/reviews",
        json={
            "verdict": "rejected",
            "correction_reason": "Wrong layer.",
            "failure_class": "wrong_layer",
        },
    )
    response = client.post(
        f"/api/v1/cases/{case_id}/verifications",
        json={"verified_by": "Ada"},
    )
    assert response.status_code == 409
    assert client.get("/api/v1/analytics/summary").json()["verified_count"] == 0
    assert client.get("/api/v1/rai-events").json()["total"] == 1
