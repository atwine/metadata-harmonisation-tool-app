"""The report names the tester's own operating system, as reported by their browser.

The hardware line in the report comes from inside Docker, so on Windows and Mac it
says "Linux" (Docker's own virtual machine). The browser knows the real system.
Only a short fixed set of names is accepted; anything else is shown as "not reported".
"""

import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from core.eval_report_builder import build_report_issue_url  # noqa: E402
from main import app  # noqa: E402

LINE = "**Operating system (reported by your browser):**"


def body_of(url: str) -> str:
    return parse_qs(urlparse(url).query)["body"][0]


@pytest.mark.parametrize("name", ["Windows", "macOS", "Linux", "Android", "iOS", "Other"])
def test_known_systems_are_shown(name):
    body = body_of(build_report_issue_url(["### Test"], False, "abcd1234", host_os=name))
    assert f"{LINE} {name}" in body


@pytest.mark.parametrize("bad", ["", "<script>alert(1)</script>", "Windows 11 Pro build 22631 on my work laptop", "windows", "x" * 500])
def test_anything_else_is_not_reported(bad):
    body = body_of(build_report_issue_url(["### Test"], False, "abcd1234", host_os=bad))
    assert f"{LINE} not reported" in body
    assert "<script>" not in body


def test_missing_value_still_works_for_old_callers():
    body = body_of(build_report_issue_url(["### Test"], False, "abcd1234"))
    assert f"{LINE} not reported" in body


def test_route_passes_the_value_through():
    client = TestClient(app, base_url="http://localhost:8000")
    payload = {"sections_markdown": ["### Test"], "has_skips": False, "session_id": "abcd1234", "host_os": "Windows"}
    r = client.post("/api/eval/report-url", json=payload, headers={"Origin": "http://localhost:8080"})
    assert r.status_code == 200
    assert f"{LINE} Windows" in body_of(r.json()["url"])


def test_route_still_accepts_a_request_without_the_field():
    client = TestClient(app, base_url="http://localhost:8000")
    payload = {"sections_markdown": ["### Test"], "has_skips": False, "session_id": "abcd1234"}
    r = client.post("/api/eval/report-url", json=payload, headers={"Origin": "http://localhost:8080"})
    assert r.status_code == 200
