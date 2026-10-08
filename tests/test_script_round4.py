"""Round 4 (final review): the output and the report files must never be the same file."""

from script_export_helpers import m, run_script, script_export

ROWS = [m("sbsmk", "Smoking"), m("wt", "Weight")]
DATA = "id,sbsmk,wt\n1,F,70\n2,S,80\n"


def make(tmp_path):
    path = tmp_path / "tool.py"
    path.write_text(script_export.render_script(script_export.build_config("S", ROWS)), encoding="utf-8")
    source = tmp_path / "d.csv"
    source.write_text(DATA, encoding="utf-8")
    return path, source


def names(folder):
    return sorted(p.name for p in folder.iterdir() if p.name != "__pycache__")


def test_output_named_like_the_text_report_is_refused(tmp_path):
    tool, source = make(tmp_path)
    result = run_script(tool, "--input", source, "--output", tmp_path / "x.txt", "--report", tmp_path / "x")
    assert result.returncode == 2
    assert "same file" in result.stderr
    assert names(tmp_path) == ["d.csv", "tool.py"]


def test_output_named_like_the_json_report_is_refused(tmp_path):
    tool, source = make(tmp_path)
    result = run_script(tool, "--input", source, "--output", tmp_path / "y.json", "--report", tmp_path / "y")
    assert result.returncode == 2
    assert "same file" in result.stderr
    assert names(tmp_path) == ["d.csv", "tool.py"]


def test_relative_and_plain_names_count_as_one_file(tmp_path):
    tool, source = make(tmp_path)
    result = run_script(tool, "--input", "d.csv", "--output", "./x.txt", "--report", "x", cwd=tmp_path)
    assert result.returncode == 2
    assert names(tmp_path) == ["d.csv", "tool.py"]


def test_two_report_files_cannot_be_the_same_file(tmp_path):
    tool, source = make(tmp_path)
    # a report base ending in ".txt" gives "base.txt.txt" and "base.txt.json": distinct, so this is allowed
    result = run_script(tool, "--input", source, "--output", tmp_path / "o.csv", "--report", tmp_path / "r.txt")
    assert result.returncode == 0, result.stderr
    assert "o.csv" in names(tmp_path)


def test_normal_run_still_works(tmp_path):
    tool, source = make(tmp_path)
    result = run_script(tool, "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 0, result.stderr
    assert names(tmp_path) == ["d.csv", "o.csv", "o_report.json", "o_report.txt", "tool.py"]
