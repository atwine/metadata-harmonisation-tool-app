"""Clear Workspace empties input/, results/ and logs/ but keeps the folders themselves.

In Docker those folders are mounted from the host, so deleting the folder (rather than
its contents) fails with "Device or resource busy" and leaves a half-cleared workspace.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import main  # noqa: E402
from routers import initialise  # noqa: E402
from storage import db  # noqa: E402

ORIGIN = {"Origin": "http://localhost:8080"}
FOLDERS = ["input", "results", "logs"]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    async def no_refresh():
        return None

    monkeypatch.setattr(main, "refresh_ontology", no_refresh)
    with TestClient(main.app, base_url="http://localhost:8000") as c:
        for d in FOLDERS:
            (tmp_path / d / "sub" / "deeper").mkdir(parents=True)
            (tmp_path / d / "file.csv").write_text("x")
            (tmp_path / d / "sub" / "deeper" / "nested.txt").write_text("y")
        yield c


def test_contents_deleted_folders_kept(client, tmp_path):
    r = client.post("/api/initialise/clear-workspace", headers=ORIGIN)
    assert r.status_code == 200
    assert r.json() == {"status": "cleared", "directories": FOLDERS}
    for d in FOLDERS:
        assert (tmp_path / d).is_dir()
        assert list((tmp_path / d).iterdir()) == []


def test_mounted_folder_cannot_be_removed(client, tmp_path, monkeypatch):
    """Simulate Docker: the folder itself can never be removed or replaced, only emptied."""
    real_rmtree = initialise.shutil.rmtree
    mounted = {(tmp_path / d).resolve() for d in FOLDERS}

    def rmtree(path, *a, **kw):
        if Path(path).resolve() in mounted:
            raise OSError(16, "Device or resource busy")
        return real_rmtree(path, *a, **kw)

    monkeypatch.setattr(initialise.shutil, "rmtree", rmtree)
    r = client.post("/api/initialise/clear-workspace", headers=ORIGIN)
    assert r.status_code == 200
    assert all(list((tmp_path / d).iterdir()) == [] for d in FOLDERS)


def test_database_is_cleared_too(client):
    values = {c: "" for c in db._MAPPING_COLS}
    values["marked"] = "To do"
    db.upsert_mapping("S1", "age", values)
    assert db.all_mappings_for_export("S1")
    assert client.post("/api/initialise/clear-workspace", headers=ORIGIN).status_code == 200
    assert not db.all_mappings_for_export("S1")


def test_failure_returns_generic_message(client, monkeypatch):
    def boom(*a, **kw):
        raise OSError("secret path /home/lab/participants")

    monkeypatch.setattr(initialise.shutil, "rmtree", boom)
    r = client.post("/api/initialise/clear-workspace", headers=ORIGIN)
    assert r.status_code == 500
    assert r.json()["detail"] == "Something went wrong. Check the server log."
    assert "secret" not in r.text
