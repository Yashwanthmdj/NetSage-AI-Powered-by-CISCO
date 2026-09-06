from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.tables import Case
from app.services.seed import catalog_payloads


def _client():
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


def test_ops_endpoints_are_computed_not_mocked() -> None:
    client, Session = _client()
    db = Session()
    try:
        for payload in catalog_payloads()[:8]:
            db.add(Case(**payload.model_dump(mode="json")))
        db.commit()
    finally:
        db.close()

    analytics = client.get("/api/v1/analytics/summary")
    assert analytics.status_code == 200
    body = analytics.json()
    assert body["case_count"] == 8
    assert body["diagnosed_count"] == 0
    assert body["accepted_count"] == 0
    assert body["edited_count"] == 0
    assert body["rejected_count"] == 0
    assert body["unresolved_count"] == 8
    assert body["ai_human_agreement"]["sample_size"] == 0
    assert body["ai_human_agreement"]["value"] is None
    assert body["ai_expected_match"]["value"] is None
    assert body["verification_success"]["value"] is None

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    health_body = health.json()
    assert health_body["status"] == "ok"
    assert "llm_configured" in health_body
    assert "api_key" not in str(health_body).lower()
    assert "sk-" not in str(health_body)

    queue = client.get("/api/v1/reviews/queue")
    assert queue.status_code == 200
    assert queue.json()["total"] == 0

    rai = client.get("/api/v1/rai-events")
    assert rai.status_code == 200
    assert rai.json()["items"] == []
