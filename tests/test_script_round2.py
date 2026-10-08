"""Round 2 (docs/plans/script-export/DEVIN_ROUND2.md): fixes from the adversarial test campaign."""

import subprocess
import sys

import pytest

from script_export_helpers import m, read_cells, run_script, script_export

CSV = "name,code\nAnn,a\nBo,b\n"
ROWS = [m("name", "Name"), m("code", "Code", "Categorical", "{'a': 'A', 'b': 'B'}")]


def make(tmp_path, name="tool.py", rows=ROWS):
    path = tmp_path / name
    path.write_text(script_export.render_script(script_export.build_config("S", rows)), encoding="utf-8")
    return path


def write_input(tmp_path, text=CSV, name="in.csv"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8", newline="")
    return path


# ---- 1. stray module files next to the script ----

@pytest.mark.parametrize("module", ["pandas", "csv", "json", "argparse"])
def test_stray_module_next_to_the_script_is_not_run(tmp_path, module):
    (tmp_path / f"{module}.py").write_text(
        "open('PWNED.txt', 'w').write('x')\nraise ImportError('fake')\n", encoding="utf-8")
    script = make(tmp_path)
    source = write_input(tmp_path)
    # no -I and no -E: the way a researcher runs it
    result = subprocess.run(
        [sys.executable, str(script), "--input", str(source), "--output", "o.csv"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=tmp_path, timeout=120)
    assert not (tmp_path / "PWNED.txt").exists()
    assert result.returncode == 0, result.stdout + result.stderr
    assert read_cells(tmp_path / "o.csv")["Code"].tolist() == ["A", "B"]


def test_all_stray_modules_together(tmp_path):
    for module in ("pandas", "csv", "json", "argparse"):
        (tmp_path / f"{module}.py").write_text("open('PWNED.txt', 'w').write('x')\n", encoding="utf-8")
    script = make(tmp_path)
    source = write_input(tmp_path)
    result = subprocess.run(
        [sys.executable, str(script), "--input", str(source), "--output", "o.csv"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=tmp_path, timeout=120)
    assert not (tmp_path / "PWNED.txt").exists()
    assert result.returncode == 0, result.stdout + result.stderr


def test_other_import_failure_names_the_real_error(tmp_path):
    """A pandas that fails for another reason must not be called 'not installed'."""
    template = (script_export._TEMPLATE_PATH).read_text(encoding="utf-8")
    assert "pandas is not installed" in template
    script = make(tmp_path)
    broken = tmp_path / "site" / "pandas"
    broken.mkdir(parents=True)
    (broken / "__init__.py").write_text("import numpy_that_is_not_there\n", encoding="utf-8")
    source = write_input(tmp_path)
    env = {"PYTHONPATH": str(tmp_path / "site")}
    import os
    result = subprocess.run(
        [sys.executable, "-s", str(script), "--input", str(source), "--output", "o.csv"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=tmp_path, timeout=120,
        env={**os.environ, **env})
    assert result.returncode == 2
    assert "numpy_that_is_not_there" in result.stderr
    assert "pandas is not installed" not in result.stderr


# ---- 2. decimal commas ----

COMMA_CSV = "id;wt\n1;78,6\n2;80,1\n3;65,25\n"
WT_ROWS = [m("id", "Id"), m("wt", "Weight", src="float", tgt="float")]
HINT = 'these look like decimal commas: re-run with --decimal ","'


def run_comma(tmp_path, *extra, rows=WT_ROWS, text=COMMA_CSV):
    script = make(tmp_path, rows=rows)
    source = write_input(tmp_path, text)
    return run_script(script, "--input", source, "--output", tmp_path / "o.csv", *extra)


def test_decimal_comma_file_is_explained_in_both_reports(tmp_path):
    result = run_comma(tmp_path)
    assert result.returncode == 0, result.stderr
    assert read_cells(tmp_path / "o.csv")["Weight"].tolist() == ["", "", ""]
    assert HINT in (tmp_path / "o_report.txt").read_text(encoding="utf-8")
    import json
    report = json.loads((tmp_path / "o_report.json").read_text(encoding="utf-8"))
    weight = [v for v in report["variables"] if v["variable"] == "wt"][0]
    assert any(HINT in note for note in weight["notes"])


def test_decimal_comma_option_reads_the_numbers(tmp_path):
    result = run_comma(tmp_path, "--decimal", ",")
    assert result.returncode == 0, result.stderr
    assert read_cells(tmp_path / "o.csv")["Weight"].tolist() == ["78.6", "80.1", "65.25"]
    assert HINT not in (tmp_path / "o_report.txt").read_text(encoding="utf-8")


def test_decimal_comma_with_integer_target_cuts_decimals_like_the_app(tmp_path):
    rows = [m("id", "Id"), m("wt", "Weight", src="float", tgt="integer")]
    result = run_comma(tmp_path, "--decimal", ",", rows=rows)
    assert result.returncode == 0, result.stderr
    assert read_cells(tmp_path / "o.csv")["Weight"].tolist() == ["78", "80", "65"]


def test_decimal_dot_is_the_default_and_changes_nothing(tmp_path):
    result = run_comma(tmp_path, "--decimal", ".", text="id;wt\n1;78.6\n2;80.1\n")
    assert result.returncode == 0, result.stderr
    assert read_cells(tmp_path / "o.csv")["Weight"].tolist() == ["78.6", "80.1"]
    assert HINT not in (tmp_path / "o_report.txt").read_text(encoding="utf-8")


def test_decimal_same_as_separator_is_refused(tmp_path):
    result = run_comma(tmp_path, "--sep", ",", "--decimal", ",", text="id,wt\n1,5\n")
    assert result.returncode == 2
    assert "--decimal" in result.stderr
    assert not (tmp_path / "o.csv").exists()


def test_no_hint_when_failures_are_not_decimal_commas(tmp_path):
    result = run_comma(tmp_path, text="id;wt\n1;abc\n2;def\n")
    assert result.returncode == 0, result.stderr
    assert HINT not in (tmp_path / "o_report.txt").read_text(encoding="utf-8")


# ---- 3. existing files are not overwritten ----

def run_plain(tmp_path, *extra):
    script = make(tmp_path)
    source = write_input(tmp_path)
    return run_script(script, "--input", source, "--output", tmp_path / "o.csv", *extra)


def test_existing_output_is_refused(tmp_path):
    (tmp_path / "o.csv").write_text("keep me", encoding="utf-8")
    result = run_plain(tmp_path)
    assert result.returncode == 2
    assert "o.csv" in result.stderr and "--overwrite" in result.stderr
    assert (tmp_path / "o.csv").read_text(encoding="utf-8") == "keep me"
    assert not (tmp_path / "o_report.txt").exists() and not (tmp_path / "o_report.json").exists()


@pytest.mark.parametrize("report_name", ["o_report.txt", "o_report.json"])
def test_existing_report_alone_is_refused(tmp_path, report_name):
    (tmp_path / report_name).write_text("keep me", encoding="utf-8")
    result = run_plain(tmp_path)
    assert result.returncode == 2
    assert report_name in result.stderr
    assert (tmp_path / report_name).read_text(encoding="utf-8") == "keep me"
    assert not (tmp_path / "o.csv").exists()


def test_overwrite_replaces_existing_files(tmp_path):
    for name in ("o.csv", "o_report.txt", "o_report.json"):
        (tmp_path / name).write_text("old", encoding="utf-8")
    result = run_plain(tmp_path, "--overwrite")
    assert result.returncode == 0, result.stderr
    assert read_cells(tmp_path / "o.csv")["Code"].tolist() == ["A", "B"]
    assert "Results report" in (tmp_path / "o_report.txt").read_text(encoding="utf-8")


def test_second_run_without_overwrite_is_refused(tmp_path):
    assert run_plain(tmp_path).returncode == 0
    again = run_plain(tmp_path)
    assert again.returncode == 2
    assert "already exists" in again.stderr


def test_same_file_protection_still_wins_with_overwrite(tmp_path):
    source = write_input(tmp_path)
    script = make(tmp_path)
    result = run_script(script, "--input", source, "--output", source, "--overwrite")
    assert result.returncode == 2
    assert source.read_text(encoding="utf-8") == CSV
