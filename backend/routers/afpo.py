import csv
import datetime
from pathlib import Path

from fastapi import APIRouter, Query

from core.afpo_lookup import lookup
from core.afpo_gap_reporter import build_github_issue_url
from models.schemas import (
    AfpoGapSubmittedRequest,
    AfpoLookupRequest,
    AfpoLookupResponse,
    AfpoLookupResult,
)

router = APIRouter()

_GAPS_PATH = Path("logs/afpo_gaps.csv")
_GAPS_HEADER = ["timestamp", "study", "variable_name", "unmatched_value", "submitted_to_github"]


def _log_gaps(study: str, variable_name: str, gaps: list[str]) -> None:
    """Append unmatched AfPO values to logs/afpo_gaps.csv, mirroring the reference app."""
    if not gaps:
        return
    _GAPS_PATH.parent.mkdir(exist_ok=True)
    file_exists = _GAPS_PATH.exists()
    with open(_GAPS_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(_GAPS_HEADER)
        for gap in gaps:
            writer.writerow([
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
                study,
                variable_name,
                gap,
                False,
            ])


def _load_submitted_values() -> dict[str, str]:
    """Returns {normalised_value: latest_timestamp} for every gap-log row already
    marked submitted_to_github=True, across ALL studies and variables — a value
    submitted once from one study must not look "new" again from another.
    This is the actual duplicate-submission guard: it's checked at lookup time,
    before the user ever sees a "Submit to AfPO" button for that value."""
    if not _GAPS_PATH.exists():
        return {}
    submitted: dict[str, str] = {}
    with open(_GAPS_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("submitted_to_github") == "True":
                key = row["unmatched_value"].strip().lower()
                ts = row["timestamp"]
                if key not in submitted or ts > submitted[key]:
                    submitted[key] = ts
    return submitted


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
    submitted_values = _load_submitted_values()

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

    _log_gaps(body.study, body.variable_name, gaps)

    return AfpoLookupResponse(results=results)


@router.post("/gaps/submitted")
async def mark_gap_submitted(body: AfpoGapSubmittedRequest):
    """Flips submitted_to_github to True for the most recent matching gap-log row.
    The reference Streamlit app's link_button can't do this (no server callback on
    click) — this closes that gap since we have a real client-server round trip."""
    if not _GAPS_PATH.exists():
        return {"status": "no_gap_log"}

    with open(_GAPS_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    if not rows:
        return {"status": "no_gap_log"}

    header, data_rows = rows[0], rows[1:]
    idx = {name: i for i, name in enumerate(header)}

    # Most recent matching row (last occurrence) that isn't already submitted.
    target_i = None
    for i in range(len(data_rows) - 1, -1, -1):
        row = data_rows[i]
        if (
            row[idx["study"]] == body.study
            and row[idx["variable_name"]] == body.variable_name
            and row[idx["unmatched_value"]] == body.value
            and row[idx["submitted_to_github"]] != "True"
        ):
            target_i = i
            break

    if target_i is None:
        return {"status": "not_found"}

    data_rows[target_i][idx["submitted_to_github"]] = "True"

    with open(_GAPS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data_rows)

    return {"status": "marked_submitted"}
