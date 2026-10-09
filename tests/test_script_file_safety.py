"""The script must never overwrite the input or itself, and must not leave partial files behind."""

import os

import pytest

from script_export_helpers import m, run_script, script_export

CSV = "name,code\nAnn,a\nBo,b\n"


def make(tmp_path, name="tool.py"):
    rows = [m("name", "Name"), m("code", "Code", "Categorical", "{'a': 'A', 'b': 'B'}")]
    path = tmp_path / name
    path.write_text(script_export.render_script(script_export.build_config("S", rows)), encoding="utf-8")
    return path


def files_in(folder):
    return sorted(p.name for p in folder.iterdir())


def refused(result, *paths_and_text):
    assert result.returncode == 2, result.stdout + result.stderr
    for path, text in paths_and_text:
        assert path.read_text(encoding="utf-8") == text


def test_output_with_different_letter_case_is_the_input(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text(CSV, encoding="utf-8")
    if not (tmp_path / "DATA.csv").exists():
        pytest.skip("case sensitive file system")
    result = run_script(make(tmp_path), "--input", source, "--output", tmp_path / "DATA.csv")
    refused(result, (source, CSV))
    assert "same file" in result.stderr


def test_output_that_is_a_link_to_the_input(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text(CSV, encoding="utf-8")
    link = tmp_path / "link.csv"
    try:
        os.symlink(source, link)
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links not available here")
    refused(run_script(make(tmp_path), "--input", source, "--output", link), (source, CSV))


@pytest.mark.parametrize("input_name", ["in.txt", "in.json"])
def test_report_aimed_at_the_input(tmp_path, input_name):
    source = tmp_path / input_name
    source.write_text(CSV, encoding="utf-8")
    result = run_script(make(tmp_path), "--input", source, "--output", tmp_path / "o.csv", "--report", tmp_path / "in")
    refused(result, (source, CSV))
    assert not (tmp_path / "o.csv").exists()


def test_output_is_the_script_itself(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text(CSV, encoding="utf-8")
    script = make(tmp_path)
    original = script.read_text(encoding="utf-8")
    refused(run_script(script, "--input", source, "--output", script), (script, original))


def test_report_aimed_at_the_script(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text(CSV, encoding="utf-8")
    script = make(tmp_path, "tool.txt")
    original = script.read_text(encoding="utf-8")
    result = run_script(script, "--input", source, "--output", tmp_path / "o.csv", "--report", tmp_path / "tool")
    refused(result, (script, original))
    assert not (tmp_path / "o.csv").exists()


def test_output_that_is_a_hard_link_to_the_input(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text(CSV, encoding="utf-8")
    link = tmp_path / "hard.csv"
    try:
        os.link(source, link)
    except (OSError, NotImplementedError):
        pytest.skip("hard links not available here")
    refused(run_script(make(tmp_path), "--input", source, "--output", link), (source, CSV))
