"""
Builds the standalone transform script for one study.

The script text is a fixed template (script_template.py). The study's mappings go
in as a JSON data block: every line of the JSON is written as a quoted Python
string literal with repr(), so study names, variable names and instructions are
data the script reads at run time and never become code. The script parses
instructions with the same restricted AST evaluator as the app; eval() and
exec() are never used.
"""
from __future__ import annotations
import datetime
import json
from pathlib import Path
from typing import Any

from storage import db

_TEMPLATE_PATH = Path(__file__).with_name("script_template.py")
_MARKER = "# __CONFIG_LINES__"
_FORMAT_VERSION = 1


class NoMappedVariables(ValueError):
    """The study has no 'Successfully mapped' rows, so there is nothing to export."""


def build_config(study: str, mappings: list[dict[str, Any]]) -> dict[str, Any]:
    """Same selection and naming rules as transform_engine._transform_study."""
    variables = []
    for row in mappings:
        if str(row.get("marked") or "").strip() != "Successfully mapped":
            continue
        study_var = row.get("study_var")
        codebook_var = row.get("codebook_var")
        variables.append({
            "study_var": study_var,
            "codebook_var": codebook_var,
            "col_name": str(codebook_var) if codebook_var else str(study_var),
            "transformation_type": row.get("transformation_type"),
            "transformation_instructions": row.get("transformation_instructions"),
            "source_dtype": str(row.get("source_dtype") or "string"),
            "target_dtype": str(row.get("target_dtype") or "string"),
        })
    if not variables:
        raise NoMappedVariables(f"No variables marked 'Successfully mapped' in {study}")
    return {
        "format_version": _FORMAT_VERSION,
        "study": study,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "variables": variables,
    }


def render_script(config: dict[str, Any]) -> str:
    template = _TEMPLATE_PATH.read_text(encoding="utf-8")
    # ensure_ascii escapes every non-ASCII character and every control character
    # (including newlines), so each JSON line is one plain-ASCII line and repr()
    # of it is a safe, single-line Python string literal.
    lines = json.dumps(config, indent=1, ensure_ascii=True).split("\n")
    block = "\n".join(f"    {line!r}," for line in lines)
    marker_line = f"{_MARKER}\n"
    if template.count(marker_line) != 1:
        raise RuntimeError("script template marker not found exactly once")
    script = template.replace(marker_line, block + "\n")
    compile(script, "transform_script.py", "exec")  # syntax check only; nothing is run
    return script


def generate_script(study: str) -> str:
    """The script for one study, built from its stored mappings (never its data)."""
    return render_script(build_config(study, db.list_mappings(study)))
