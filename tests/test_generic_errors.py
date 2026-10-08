"""Server errors (500) return a fixed message; the details stay in the server log (item 8)."""

import logging
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import main  # noqa: E402
from routers import codebook, download  # noqa: E402

SECRET = "participant 4711 /home/lab/private/file.csv"
GENERIC = "Something went wrong. Check the server log."


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "input").mkdir()
    (tmp_path / "input" / "target_variables.csv").write_text("variable_name,description\nage,Age\n")

    async def no_refresh():
        return None

    monkeypatch.setattr(main, "refresh_ontology", no_refresh)
    with TestClient(main.app, base_url="http://localhost:8000") as c:
        yield c


def _boom(*a, **kw):
    raise RuntimeError(SECRET)


def test_codebook_read_failure_is_generic(client, monkeypatch, caplog):
    monkeypatch.setattr(codebook.pd, "read_csv", _boom)
    with caplog.at_level(logging.ERROR):
        r = client.get("/api/codebook/")
    assert r.status_code == 500
    assert r.json()["detail"] == GENERIC
    assert SECRET not in r.text
    assert "RuntimeError" in caplog.text and "/api/codebook/" in caplog.text
    assert SECRET not in caplog.text


def test_transformation_failure_is_generic(client, monkeypatch, caplog):
    monkeypatch.setattr(download, "apply_transformations", _boom)
    with caplog.at_level(logging.ERROR):
        r = client.post("/api/download/transformed-data", json={"studies": ["S1"]})
    assert r.status_code == 500
    assert r.json()["detail"] == GENERIC
    assert SECRET not in r.text
    assert "RuntimeError" in caplog.text and "/api/download/transformed-data" in caplog.text
    assert SECRET not in caplog.text


def test_validation_messages_are_kept(client):
    r = client.post("/api/download/transformed-data", json={"studies": []})
    assert r.status_code == 400
    assert r.json()["detail"] == "No studies specified"


# ── item N3: other places that used to echo exception text ──────────────────

from core.errors import CSV_UNREADABLE, ai_error_message  # noqa: E402
from routers import studies  # noqa: E402


def test_codebook_parse_failure_is_generic(client, monkeypatch, caplog):
    monkeypatch.setattr(codebook, "read_csv_robust", _boom)
    with caplog.at_level(logging.ERROR):
        r = client.post("/api/codebook/upload", files={"file": ("c.csv", b"a,b\n1,2\n", "text/csv")})
    assert r.status_code == 400
    assert r.json()["detail"] == CSV_UNREADABLE
    assert SECRET not in r.text and SECRET not in caplog.text
    assert "RuntimeError" in caplog.text


def test_study_parse_failure_is_generic(client, monkeypatch, caplog):
    monkeypatch.setattr(studies, "read_csv_robust", _boom)
    with caplog.at_level(logging.ERROR):
        r = client.post(
            "/api/studies/upload",
            data={"study_title": "S1"},
            files={"variables_file": ("v.csv", b"variable_name\nage\n", "text/csv")},
        )
    assert r.status_code == 400
    assert r.json()["detail"] == CSV_UNREADABLE
    assert SECRET not in r.text and SECRET not in caplog.text


def test_ai_connection_test_failure_is_generic(client, monkeypatch, caplog):
    from core import ai_provider

    def broken(self):
        raise ConnectionError(SECRET)

    monkeypatch.setattr(ai_provider.AIProviderWrapper, "validate_connection", broken)
    with caplog.at_level(logging.ERROR):
        r = client.post("/api/ai-config/test", json={"chat": {"provider": "ollama", "model": "m"}})
    assert r.status_code == 200
    body = r.json()
    assert body["connected"] is False
    assert SECRET not in r.text and SECRET not in caplog.text
    assert "Could not reach the AI service" in body["chat"]["message"]


def test_initialise_step_failure_is_generic(client, monkeypatch):
    from routers import initialise

    monkeypatch.setattr(initialise, "_run_pdf_conversion", _boom)
    monkeypatch.setattr(initialise, "_run_descriptions", _boom)
    with client.stream("POST", "/api/initialise/run", json={"ai_config": {"chat": {"provider": "ollama", "model": "m"}}, "init_prompt": "p"}) as r:
        text = "".join(r.iter_text())
    assert "failed" in text
    assert SECRET not in text


def test_ai_error_message_uses_class_not_text():
    class AuthenticationError(Exception):
        pass

    class APITimeoutError(Exception):
        pass

    assert "API key" in ai_error_message(AuthenticationError("sk-live-123"))
    assert "in time" in ai_error_message(APITimeoutError("x"))
    assert "sk-live-123" not in ai_error_message(AuthenticationError("sk-live-123"))
    assert "Check the provider" in ai_error_message(ValueError("whatever"))


def test_app_written_config_messages_are_kept():
    from core.errors import ConfigError

    assert ai_error_message(ConfigError("Invalid OpenAI API key format")) == "Invalid OpenAI API key format"
