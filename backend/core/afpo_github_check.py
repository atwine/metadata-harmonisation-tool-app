"""
Live-checks the h3abionet/afpo GitHub repo for an existing term request before
letting a user file a new one. This is the actual cross-installation dedup
guard: every installation of this app, anywhere, points at the same shared
GitHub repo, so a live search there is authoritative regardless of which
instance is asking — unlike any local flag, which only knows what *this*
installation has done.

GitHub's search API is capped at 10 req/min unauthenticated (30/min with a
token) — much tighter than the general REST API limit. Callers are expected
to cache results (see storage.db.get_github_check_cache); this module does
the live call only.
"""
from __future__ import annotations
import os
from typing import Any

import httpx

_REPO = "h3abionet/afpo"
_SEARCH_URL = "https://api.github.com/search/issues"
_TIMEOUT = 8.0


def check_github_for_term(value: str) -> dict[str, Any]:
    """Returns {"status": "open_exists" | "closed_exists" | "none" | "unavailable",
    "issues": [{"number", "url", "state", "title"}, ...]}.

    Searches issue titles for our own submission template's exact wording
    (see afpo_gap_reporter.build_github_issue_url) so a match is precise
    rather than matching any issue that happens to mention the term."""
    query = f'repo:{_REPO} in:title "New term request: {value}"'
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = httpx.get(_SEARCH_URL, params={"q": query}, headers=headers, timeout=_TIMEOUT)
    except httpx.HTTPError:
        return {"status": "unavailable", "issues": []}

    if resp.status_code != 200:
        return {"status": "unavailable", "issues": []}

    items = resp.json().get("items", [])
    issues = [
        {"number": i["number"], "url": i["html_url"], "state": i["state"], "title": i["title"]}
        for i in items
    ]

    if any(i["state"] == "open" for i in issues):
        status = "open_exists"
    elif issues:
        status = "closed_exists"
    else:
        status = "none"

    return {"status": status, "issues": issues}
