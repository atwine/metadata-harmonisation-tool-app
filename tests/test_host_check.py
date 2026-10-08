"""Host-header check (finding F3): only the tool's own host names are answered."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import main  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    async def no_refresh():
        return None

    monkeypatch.setattr(main, "refresh_ontology", no_refresh)
    with TestClient(main.app, base_url="http://localhost:8000") as c:
        yield c


@pytest.mark.parametrize("host", ["localhost:8000", "LOCALHOST:8000", "127.0.0.1:8000", "[::1]:8000", "[::1]", "localhost"])
def test_own_hosts_are_answered(client, host):
    assert client.get("/api/studies/", headers={"Host": host}).status_code == 200


@pytest.mark.parametrize("host", ["evil.example:8000", "localhost.evil.example", "127.0.0.1.evil.example:8000", "[::2]:8000", ""])
def test_foreign_hosts_are_refused(client, host):
    r = client.get("/api/studies/", headers={"Host": host})
    assert r.status_code == 403


def test_extra_hosts_come_from_the_environment(monkeypatch):
    monkeypatch.delenv("MHT_ALLOWED_HOSTS", raising=False)
    assert main.allowed_hosts() == ["localhost", "127.0.0.1", "::1"]
    monkeypatch.setenv("MHT_ALLOWED_HOSTS", "lab-pc.local, 192.168.1.20 ,")
    assert main.allowed_hosts() == ["localhost", "127.0.0.1", "::1", "lab-pc.local", "192.168.1.20"]
