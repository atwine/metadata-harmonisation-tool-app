import datetime

from fastapi import APIRouter, Query

from core.afpo_github_check import check_github_for_term
from core.afpo_lookup import lookup, ontology_status
from core.afpo_gap_reporter import build_github_issue_url
from models.schemas import (
    AfpoGapSubmittedRequest,
    AfpoLookupRequest,
    AfpoLookupResponse,
    AfpoLookupResult,
    GithubCheckResponse,
    OntologyStatusResponse,
)
from storage import db

router = APIRouter()

_GITHUB_CHECK_CACHE_TTL = datetime.timedelta(hours=24)


def _search_issues_url(value: str) -> str:
    """A GitHub issue search link — useful even for values our own log has never
    seen submitted, since someone could have filed one outside this tool."""
    from urllib.parse import quote
    return f"https://github.com/h3abionet/afpo/issues?q={quote(f'is:issue {value}')}"


@router.get("/issue-url")
async def afpo_issue_url(
    value: str = Query(...),
    study: str = Query(...),
    variable_name: str = Query(...),
):
    """Builds the pre-filled GitHub issue URL for a (possibly user-edited) gap
    term. Kept server-side so the issue title/body template has one source of
    truth — the frontend calls this instead of re-deriving the template."""
    return {"url": build_github_issue_url(value, study, variable_name)}


@router.post("/lookup", response_model=AfpoLookupResponse)
async def afpo_lookup(body: AfpoLookupRequest):
    results: list[AfpoLookupResult] = []
    gaps: list[str] = []
    submitted_values = db.load_submitted_afpo_values()

    for value in body.values:
        match = lookup(value)
        if match:
            results.append(AfpoLookupResult(
                input_value=value,
                afpo_id=match["afpo_id"],
                canonical_name=match["canonical_name"],
                matched_via=match["matched_via"],
                confidence=match["confidence"],
            ))
        else:
            gaps.append(value)
            key = value.strip().lower()
            results.append(AfpoLookupResult(
                input_value=value,
                github_issue_url=build_github_issue_url(value, body.study, body.variable_name),
                search_issues_url=_search_issues_url(value),
                already_submitted=key in submitted_values,
                previously_submitted_at=submitted_values.get(key),
            ))

    db.log_afpo_gaps(body.study, body.variable_name, gaps)

    return AfpoLookupResponse(results=results)


@router.post("/gaps/submitted")
async def mark_gap_submitted(body: AfpoGapSubmittedRequest):
    """Flips submitted_to_github to True for the most recent matching gap-log row.
    The reference Streamlit app's link_button can't do this (no server callback on
    click) — this closes that gap since we have a real client-server round trip."""
    if db.mark_afpo_gap_submitted(body.study, body.variable_name, body.value):
        return {"status": "marked_submitted"}
    return {"status": "not_found"}


@router.get("/check-github", response_model=GithubCheckResponse)
async def check_github(value: str = Query(...)):
    """Live-checks GitHub for an existing open/closed issue requesting this
    term, before the frontend lets the user file a new one — this is the
    actual cross-installation dedup guard (see core.afpo_github_check for
    why a local-only flag can't do this job on its own).

    Cached for 24h per normalised term: GitHub's search API is capped at
    10 req/min unauthenticated, so re-checking on every render isn't viable."""
    key = value.strip().lower()

    cached = db.get_github_check_cache(key)
    if cached is not None:
        checked_at = datetime.datetime.fromisoformat(cached["checked_at"])
        if datetime.datetime.now(datetime.timezone.utc) - checked_at < _GITHUB_CHECK_CACHE_TTL:
            return GithubCheckResponse(
                status=cached["status"],
                issues=cached["issues"],
                checked_at=cached["checked_at"],
                from_cache=True,
            )

    result = check_github_for_term(value)
    if result["status"] != "unavailable":
        db.set_github_check_cache(key, result["status"], result["issues"])

    return GithubCheckResponse(
        status=result["status"],
        issues=result["issues"],
        checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        from_cache=False,
    )


@router.get("/ontology-status", response_model=OntologyStatusResponse)
async def get_ontology_status():
    return OntologyStatusResponse(**ontology_status())
