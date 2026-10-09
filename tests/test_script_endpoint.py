"""P5: the script download route. Access rules for it are in ACCESS.md section 4."""

import sys
from pathlib import Path
from pathlib import Path as _Path

import pytest
from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "backend"))

import main  # noqa: E402
from storage import db  # noqa: E402

STUDY = "ACE_Test"
LOCAL_HOST = "localhost:8000"
LOCAL_ORIGIN = "http://localhost:8080"
EVIL_ORIGIN = "https://evil.example"
EVIL_HOST = "evil.example:8000"


@pytest.fixture
def client(tmp_path, monkeypatch):
    (tmp_path / "input" / STUDY).mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    async def no_refresh():
        return None

    monkeypatch.setattr(main, "refresh_ontology", no_refresh)
    with TestClient(main.app, base_url=f"http://{LOCAL_HOST}") as c:
        yield c


def store(marked, study=STUDY):
    db.upsert_mapping(study, "age", {
        "codebook_var": "Age", "marked": marked, "source_dtype": "float", "target_dtype": "float",
        "transformation_type": "Direct", "transformation_instructions": "x * 1",
        "afpo_values_mapped": "{}", "afpo_values_gaps": "[]",
    })


def test_script_download_returns_a_python_file(client):
    store("Successfully mapped")
    r = client.get(f"/api/download/{STUDY}/script", headers={"Origin": LOCAL_ORIGIN})
    assert r.status_code == 200
    assert r.headers["content-disposition"] .startswith(f'attachment; filename="transform_{STUDY}.py"')
    compile(r.text, "downloaded.py", "exec")
    assert "--input" in r.text and "--output" in r.text


def test_script_download_name_is_sanitised(client):
    (_Path("input") / "ACE_Test_2").mkdir(parents=True)
    store("Successfully mapped", study="ACE_Test_2")
    r = client.get("/api/download/ACE%20Test%202!/script")
    assert r.status_code == 200
    assert 'filename="transform_ACE_Test_2.py"' in r.headers["content-disposition"]


def test_no_mapped_variables_gives_422(client):
    store("To do")
    r = client.get(f"/api/download/{STUDY}/script")
    assert r.status_code == 422
    assert "Successfully mapped" in r.json()["detail"]


def test_unknown_study_gives_404(client):
    assert client.get("/api/download/Nobody/script").status_code == 404


def test_empty_study_name_gives_400(client):
    assert client.get("/api/download/%20/script").status_code == 400


def test_foreign_host_gets_403(client):
    store("Successfully mapped")
    r = client.get(f"/api/download/{STUDY}/script", headers={"Host": EVIL_HOST})
    assert r.status_code == 403


def test_foreign_website_cannot_read_the_reply(client):
    """A GET from another site is sent, but the browser hands the reply to the
    page only if the API allows that origin, and it does not."""
    store("Successfully mapped")
    r = client.get(f"/api/download/{STUDY}/script", headers={"Origin": EVIL_ORIGIN})
    assert r.headers.get("access-control-allow-origin") not in (EVIL_ORIGIN, "*")


def test_unexpected_failure_hides_the_error_text(client, monkeypatch):
    from routers import download

    def boom(study):
        raise RuntimeError("C:/secret/path/participant_7.csv")

    monkeypatch.setattr(download, "generate_script", boom)
    r = client.get(f"/api/download/{STUDY}/script")
    assert r.status_code == 500
    assert "secret" not in r.text and "participant" not in r.text


def test_non_latin_study_name_gets_an_rfc6266_header(client, tmp_path):
    from urllib.parse import quote

    name = "Исследование_1"
    (tmp_path / "input" / name).mkdir()
    store("Successfully mapped", study=name)
    r = client.get(f"/api/download/{quote(name)}/script")
    assert r.status_code == 200
    header = r.headers["content-disposition"]
    assert header.startswith("attachment; filename=")
    assert header.encode("ascii")
    assert f"filename*=UTF-8''transform_{quote(name)}.py" in header
    compile(r.text, "downloaded.py", "exec")
