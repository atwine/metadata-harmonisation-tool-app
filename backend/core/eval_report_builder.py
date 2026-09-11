"""
Builds the pre-filled GitHub Issue URL for a participant's evaluation
report — same pattern as afpo_gap_reporter.py: no GitHub API call, no
stored credentials. The URL just opens GitHub's own "new issue" form
already filled in; the participant reviews it and submits it themselves
under their own GitHub account.

Kept server-side (like the AfPO issue-url endpoint) so there's one source
of truth for the template and for reading the automated performance log —
the frontend sends its already-formatted answer sections and gets back a
ready-to-open URL.
"""
from __future__ import annotations
import datetime
import json
from pathlib import Path
from urllib.parse import urlencode

REPO = "atwine/metadata-harmonisation-tool-app"
LOG_PATH = Path("logs") / "benchmark_log.jsonl"

# Keeps issue bodies well under GitHub's practical URL-length ceiling. The
# full performance log is never inlined here regardless — it's attached to
# the issue as a file by the participant, not embedded in the link.
_MAX_BODY_CHARS = 6000


def _read_performance_summary() -> str:
    """Best-effort summary of the automated log: hardware, AI config,
    per-stage timings, errors. Never the content of a participant's data —
    see eval_logger.py, which only ever writes performance numbers."""
    if not LOG_PATH.exists():
        return "_No performance log found for this session._"

    hardware = None
    ai_config = None
    stage_durations: dict[str, float] = {}
    errors: list[str] = []

    try:
        with open(LOG_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                event = ev.get("event")
                if event == "hardware_profile":
                    hardware = ev
                elif event == "ai_config":
                    ai_config = ev
                elif event == "stage_end":
                    stage_durations[ev.get("stage", "?")] = ev.get("duration_seconds")
                elif event == "stage_error":
                    errors.append(f"{ev.get('stage')}: {ev.get('error')}")
    except OSError:
        return "_Performance log could not be read._"

    lines: list[str] = []
    if hardware:
        lines.append(
            f"- **Hardware:** {hardware.get('cpu')}, {hardware.get('cores')} cores, "
            f"{hardware.get('ram_gb')} GB RAM, GPU: {hardware.get('gpu') or 'none detected'}, "
            f"{hardware.get('os')}, Python {hardware.get('python')}"
        )
    if ai_config:
        embedding_model = ai_config.get("embedding_model")
        embedding_desc = (
            f"{ai_config.get('embedding_provider')}/{embedding_model}"
            if embedding_model else "same as chat"
        )
        lines.append(
            f"- **AI config:** chat = {ai_config.get('chat_provider')}/{ai_config.get('chat_model')}, "
            f"embedding = {embedding_desc}"
        )
    if stage_durations:
        parts = ", ".join(f"{k}={v}s" for k, v in stage_durations.items())
        lines.append(f"- **Stage timings:** {parts}")

    lines.append(f"- **Errors during processing:** {'; '.join(errors) if errors else 'none'}")

    return "\n".join(lines)


def build_report_issue_url(sections_markdown: list[str], has_skips: bool) -> str:
    today = datetime.date.today().isoformat()
    title = f"[Eval] Testing report — {today}"

    body_parts = [
        "## Metadata Harmonisation Tool — Evaluation Report",
        "",
        "### Performance log summary",
        _read_performance_summary(),
        "",
        "_The full performance log (`logs/benchmark_log.jsonl`) isn't included above — "
        "if you're able to find it, please attach that file to this issue before submitting._",
        "",
        *sections_markdown,
        "",
        "---",
        "*Submitted via the Metadata Harmonisation Tool's evaluation testing build.*",
    ]
    body = "\n".join(body_parts)

    if len(body) > _MAX_BODY_CHARS:
        body = (
            body[:_MAX_BODY_CHARS]
            + "\n\n_(shortened to fit GitHub's link length limit — feel free to add detail "
              "back before submitting; nothing you wrote was lost, it's just not pre-filled "
              "past this point)_"
        )

    labels = ["evaluation"]
    if has_skips:
        labels.append("has-skipped-checkins")

    params = {"title": title, "body": body, "labels": ",".join(labels)}
    return f"https://github.com/{REPO}/issues/new?{urlencode(params)}"
