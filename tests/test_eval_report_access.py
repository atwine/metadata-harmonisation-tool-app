"""Access checks for the testing build's one extra route, POST /api/eval/report-url.

The audit's own test file (test_access.py) is kept unchanged, so the extra route
is covered here. It must follow the same rules as every other write route.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from main import app  # noqa: E402

URL = "/api/eval/report-url"
BODY = {"sections_markdown": ["### Test"], "has_skips": False, "session_id": "abcd1234"}


@pytest.fixture(scope="module")
def client():
    return TestClient(app, base_url="http://localhost:8000")


def test_researcher_page_can_build_a_report_link(client):
    r = client.post(URL, json=BODY, headers={"Origin": "http://localhost:8080"})
    assert r.status_code == 200
    assert r.json()["url"].startswith("https://github.com/")


@pytest.mark.parametrize("origin", ["https://evil.example", "null", "http://localhost.evil.example:8080"])
def test_other_websites_cannot_call_it(client, origin):
    r = client.post(URL, json=BODY, headers={"Origin": origin})
    assert r.status_code == 403


def test_rebinding_host_cannot_call_it():
    rebound = TestClient(app, base_url="http://evil.example")
    r = rebound.post(URL, json=BODY)
    assert r.status_code == 403
