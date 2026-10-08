"""Shared helpers for the script-export tests.

Builds a throwaway workspace (input/ and db/ in a temp folder), stores mappings
the way the app does, runs the in-app engine, and runs the generated script as a
separate process (python -I) so the two outputs can be compared cell for cell.
"""

import io
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "backend"))

from core import script_export  # noqa: E402
from core.transform_engine import apply_transformations  # noqa: E402
from storage import db  # noqa: E402

OK = "Successfully mapped"


def m(study_var, codebook_var=None, t_type=None, instr=None, src="string", tgt="string", marked=OK):
    """One mapping row, with the same fields the app stores."""
    return {
        "study_var": study_var,
        "codebook_var": codebook_var,
        "marked": marked,
        "transformation_type": t_type,
        "transformation_instructions": instr,
        "source_dtype": src,
        "target_dtype": tgt,
        "afpo_values_mapped": "{}",
        "afpo_values_gaps": "[]",
    }


def setup_study(tmp_path, monkeypatch, study, data_csv, mappings):
    """Workspace in tmp_path: input/<study>/example_data.csv plus mapping rows."""
    monkeypatch.chdir(tmp_path)
    folder = tmp_path / "input" / study
    folder.mkdir(parents=True)
    if isinstance(data_csv, bytes):
        (folder / "example_data.csv").write_bytes(data_csv)
    else:
        (folder / "example_data.csv").write_text(data_csv, encoding="utf-8", newline="")
    db.init_db()
    for row in mappings:
        db.upsert_mapping(study, row["study_var"], row)


def app_output(study):
    """Run the in-app engine. Returns (output as text cells, success/error lines)."""
    zip_bytes, results = apply_transformations([study])
    assert results[0]["status"] == "ok", results
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        csv_text = zf.read(f"{study}/{study}_transformed.csv").decode("utf-8")
        report = zf.read(f"{study}/validation_report.txt").decode("utf-8")
    frame = pd.read_csv(io.StringIO(csv_text), dtype=str, keep_default_na=False)
    return frame, parse_validation(report)


def parse_validation(text):
    """{variable: (successes, errors)} from 'Validation Report' lines."""
    found = {}
    for line in text.splitlines():
        hit = re.match(r"^- (.+): success=(\d+), errors=(\d+)$", line)
        if hit:
            found[hit.group(1)] = (int(hit.group(2)), int(hit.group(3)))
    return found


def make_script(tmp_path, study):
    path = tmp_path / f"transform_{study}.py"
    path.write_text(script_export.generate_script(study), encoding="utf-8")
    return path


def run_script(script, *args, cwd=None):
    """The script as the researcher runs it: a separate isolated Python process."""
    return subprocess.run(
        [sys.executable, "-I", str(script), *map(str, args)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=cwd, timeout=120,
    )


def read_cells(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)
