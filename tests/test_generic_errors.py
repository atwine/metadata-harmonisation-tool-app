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
