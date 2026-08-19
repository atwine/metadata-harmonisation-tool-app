from fastapi import APIRouter, Query

from core.afpo_lookup import lookup
from core.afpo_gap_reporter import build_github_issue_url
from models.schemas import (
    AfpoGapSubmittedRequest,
    AfpoLookupRequest,
    AfpoLookupResponse,
    AfpoLookupResult,
)
from storage import db

router = APIRouter()


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
