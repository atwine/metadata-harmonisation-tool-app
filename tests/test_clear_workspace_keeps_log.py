"""Testing build only: Clear Workspace must not delete the tester's performance log.

logs/benchmark_log.jsonl feeds the "Submit Report" summary, and its hardware line is
written once at startup, so deleting it would lose data that cannot be recreated
without a restart. Everything else in logs/ is still cleared.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import main  # noqa: E402

ORIGIN = {"Origin": "http://localhost:8080"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    async def no_refresh():
        return None

    monkeypatch.setattr(main, "refresh_ontology", no_refresh)
    with TestClient(main.app, base_url="http://localhost:8000") as c:
        (tmp_path / "logs").mkdir(exist_ok=True)
        (tmp_path / "logs" / "benchmark_log.jsonl").write_text('{"event": "hardware_profile"}\n')
        (tmp_path / "logs" / "other.log").write_text("x")
        (tmp_path / "input").mkdir(exist_ok=True)
        (tmp_path / "input" / "study.csv").write_text("x")
        yield c


def test_performance_log_survives_clear_workspace(client, tmp_path):
    assert client.post("/api/initialise/clear-workspace", headers=ORIGIN).status_code == 200
    assert (tmp_path / "logs" / "benchmark_log.jsonl").read_text() == '{"event": "hardware_profile"}\n'


def test_everything_else_is_still_cleared(client, tmp_path):
    client.post("/api/initialise/clear-workspace", headers=ORIGIN)
    assert not (tmp_path / "logs" / "other.log").exists()
    assert list((tmp_path / "input").iterdir()) == []
