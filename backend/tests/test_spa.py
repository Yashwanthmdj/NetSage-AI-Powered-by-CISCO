from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def test_spa_serves_index_and_keeps_api(tmp_path: Path, monkeypatch) -> None:
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>NetSage</title>", encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log('ok')", encoding="utf-8")

    monkeypatch.setenv("SERVE_FRONTEND", "true")
    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())
        home = client.get("/")
        assert home.status_code == 200
        assert "NetSage" in home.text
        deep = client.get("/cases/VLAN-001")
        assert deep.status_code == 200
        assert "NetSage" in deep.text
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["app"]
    finally:
        get_settings.cache_clear()
