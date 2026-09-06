from fastapi.testclient import TestClient

from app.main import create_app
from app.services.rules.engine import evaluate


SAMPLE = """
R1# show ip interface brief
GigabitEthernet0/0     10.1.1.1        YES manual up                    up
R2# show ip interface brief
GigabitEthernet0/0     10.1.1.1        YES manual up                    up
""".strip()


def test_evaluate_rejects_empty_evidence() -> None:
    client = TestClient(create_app())
    response = client.post("/api/v1/rules/evaluate", json={"show_outputs": "", "topology_note": ""})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_evaluate_returns_all_six_rules() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/rules/evaluate",
        json={"show_outputs": SAMPLE, "topology_note": ""},
    )
    assert response.status_code == 200
    names = [item["rule_name"] for item in response.json()["results"]]
    assert names == ["DUP_IP", "BAD_MASK", "GW_MISMATCH", "IF_DOWN", "MISSING_VLAN", "MISSING_ROUTE"]
    assert response.json()["rule_run_id"] is None
    assert response.json()["case_id"] is None


def test_evaluate_endpoint_is_stateless() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/rules/evaluate",
        json={"show_outputs": SAMPLE, "topology_note": ""},
    )
    assert response.status_code == 200
    body = response.json()
    dup = next(item for item in body["results"] if item["rule_name"] == "DUP_IP")
    assert dup["status"] == "fail"
    assert body["fail_count"] >= 1
    local = evaluate(SAMPLE)
    assert local.fail_count == body["fail_count"]
