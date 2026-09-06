import httpx
import pytest

from app.services.ai.client import OpenAICompatibleClient
from app.services.ai.errors import LlmUnavailableError
from app.services.ai.prompt_loader import load_prompt, load_schema_notes


def test_diagnose_prompt_has_required_fields_and_examples() -> None:
    body, digest, path = load_prompt("diagnose_prompt.md")
    assert path.name == "diagnose_prompt.md"
    assert digest
    for field in (
        "root_cause",
        "confidence",
        "osi_layer",
        "concept_tag",
        "severity",
        "evidence",
        "next_command",
        "fix_steps",
        "verification_command",
    ):
        assert field in body
    assert body.count("Valid JSON") >= 2
    schema = load_schema_notes()
    assert "verification_command" in schema


def test_client_fails_closed_without_api_key(monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LLM_API_KEY", "")
    get_settings.cache_clear()
    try:
        client = OpenAICompatibleClient()
        try:
            client.complete_json("sys", "user")
            raised = False
        except LlmUnavailableError as exc:
            raised = True
            assert exc.status_code == 503
        assert raised
    finally:
        get_settings.cache_clear()


class _FakeResponse:
    def __init__(self, status_code: int, text: str = "provider error"):
        self.status_code = status_code
        self.text = text

    def json(self):
        raise ValueError("not used")


class _FakeHttpx:
    def __init__(self, response):
        self._response = response

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def post(self, *_args, **_kwargs):
        return self._response


def test_client_maps_provider_failures_to_unavailable(monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.services.ai.client.httpx.Client",
        lambda *args, **kwargs: _FakeHttpx(_FakeResponse(503)),
    )
    try:
        with pytest.raises(LlmUnavailableError) as exc:
            OpenAICompatibleClient().complete_json("sys", "user")
        assert exc.value.status_code == 503
    finally:
        get_settings.cache_clear()


class _TimeoutHttpx:
    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def post(self, *_args, **_kwargs):
        raise httpx.TimeoutException("LLM request timed out")


def test_client_maps_timeout_to_unavailable(monkeypatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.services.ai.client.httpx.Client",
        lambda *args, **kwargs: _TimeoutHttpx(),
    )
    try:
        with pytest.raises(LlmUnavailableError) as exc:
            OpenAICompatibleClient().complete_json("sys", "user")
        assert exc.value.status_code == 503
        assert "nvapi-" not in str(exc.value)
        assert "sk-test" not in (exc.value.details or "")
    finally:
        get_settings.cache_clear()
