from fastapi import APIRouter

from core.eval_report_builder import build_report_issue_url
from models.schemas import EvalReportRequest

router = APIRouter()


@router.post("/report-url")
async def report_url(body: EvalReportRequest):
    """Builds the pre-filled GitHub issue URL for a participant's evaluation
    report. Same shape as /api/afpo/issue-url — server-side so the template
    and the performance-log read have one source of truth."""
    return {"url": build_report_issue_url(body.sections_markdown, body.has_skips)}
