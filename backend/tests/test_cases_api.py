from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.tables import Case
from app.services.seed import catalog_payloads


def _client(tmp_path):
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
    return TestClient(app), TestingSession


def test_seed_and_list_returns_catalog() -> None:
    client, Session = _client(None)
    db = Session()
    try:
        for payload in catalog_payloads():
            db.add(Case(**payload.model_dump(mode="json")))
        db.commit()
    finally:
        db.close()

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["database"] == "ok"

    listing = client.get("/api/v1/cases")
    assert listing.status_code == 200
    body = listing.json()
    assert body["pagination"]["total"] >= 30
    assert {item["concept_tag"] for item in body["items"]} >= {
        "vlan",
        "gateway",
        "dhcp",
        "dns",
        "routing",
        "acl",
        "nat",
        "wireless",
    }

    first = body["items"][0]
    detail = client.get(f"/api/v1/cases/by-code/{first['case_code']}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["symptom"]
    assert payload["topology_note"]
    assert payload["show_outputs"]
    assert payload["expected_fault"]
    assert payload["latest_diagnosis"] is None

    coverage = client.get("/api/v1/cases/coverage")
    assert coverage.status_code == 200
    assert coverage.json()["meets_coverage_gate"] is True


def test_duplicate_case_and_integrity_errors_do_not_leak_secrets() -> None:
    from sqlalchemy.exc import IntegrityError

    from app.db.session import get_db
    from app.main import create_app

    client, _Session = _client(None)
    payload = next(item for item in catalog_payloads() if item.case_code == "VLAN-001")
    body = payload.model_dump(mode="json")
    first = client.post("/api/v1/cases", json=body)
    assert first.status_code == 201
    duplicate = client.post("/api/v1/cases", json=body)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "conflict"
    assert "nvapi-" not in duplicate.text
    assert "sqlite" not in duplicate.text.lower()

    app = create_app()

    def broken_db():
        raise IntegrityError("INSERT INTO diagnoses", {}, Exception("nvapi-should-not-leak"))
        yield  # pragma: no cover

    app.dependency_overrides[get_db] = broken_db
    broken = TestClient(app, raise_server_exceptions=False)
    response = broken.get("/api/v1/cases")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "integrity_error"
    assert response.json()["error"]["message"] == "Database constraint failed"
    assert "nvapi-" not in response.text
    assert "INSERT INTO" not in response.text
