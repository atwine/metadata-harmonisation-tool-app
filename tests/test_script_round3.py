"""Round 3 (docs/plans/script-export/DEVIN_ROUND3.md): three small gaps."""

import json

import pytest

from script_export_helpers import m, run_script, script_export
from test_script_behaviour import load_script_module

ROWS = [m("sbsmk", "Smoking"), m("wt", "Weight")]


def make(tmp_path, name="tool.py", rows=ROWS):
    path = tmp_path / name
    path.write_text(script_export.render_script(script_export.build_config("S", rows)), encoding="utf-8")
    return path


def only(folder, *names):
    return sorted(p.name for p in folder.iterdir() if p.name != "__pycache__") == sorted(names)


# ---- 1. show what the script saw ----

def test_unrelated_columns_are_listed_everywhere(tmp_path):
    source = tmp_path / "d.csv"
    source.write_text("smoking,wght\n1,70\n", encoding="utf-8")
    result = run_script(make(tmp_path), "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 2
    assert '"smoking", "wght"' in result.stderr
    assert 'separator ","' in result.stderr and "encoding utf-8-sig" in result.stderr
    text = (tmp_path / "o_report.txt").read_text(encoding="utf-8")
    assert '"smoking", "wght"' in text and 'separator ","' in text
    report = json.loads((tmp_path / "o_report.json").read_text(encoding="utf-8"))
    assert report["columns_found"] == ["smoking", "wght"]
    assert report["separator"] == "," and report["encoding"] == "utf-8-sig"


def test_column_list_is_capped_at_30(tmp_path):
    source = tmp_path / "d.csv"
    source.write_text(",".join("col%d" % i for i in range(100)) + "\n" + ",".join("1" for _ in range(100)) + "\n", encoding="utf-8")
    result = run_script(make(tmp_path), "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 2
    assert '"col29"' in result.stderr and '"col30"' not in result.stderr
    assert "and 70 more" in result.stderr
    text = (tmp_path / "o_report.txt").read_text(encoding="utf-8")
    assert '"col29"' in text and '"col30"' not in text and "and 70 more" in text
    report = json.loads((tmp_path / "o_report.json").read_text(encoding="utf-8"))
    assert len(report["columns_found"]) == 30 and report["columns_found_not_listed"] == 70


def test_wrong_sep_shows_one_long_column(tmp_path):
    source = tmp_path / "d.csv"
    source.write_text("smoking;wght\n1;70\n", encoding="utf-8")
    result = run_script(make(tmp_path), "--input", source, "--output", tmp_path / "o.csv", "--sep", ",")
    assert result.returncode == 2
    assert 'separator ","' in result.stderr and '"smoking;wght"' in result.stderr


def test_close_matches_keep_did_you_mean_and_skip_the_list(tmp_path):
    source = tmp_path / "d.csv"
    source.write_text("SBSMK,wt2\n1,70\n", encoding="utf-8")
    result = run_script(make(tmp_path), "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 2
    assert "did you mean" in result.stderr
    assert "Columns the script found" not in result.stderr
