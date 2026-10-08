"""A failed run leaves nothing behind: no output, no report, no temporary files."""

import pytest

from script_export_helpers import run_script
from test_script_behaviour import load_script_module
from test_script_file_safety import CSV, make


def only(folder, *names):
    return sorted(p.name for p in folder.iterdir() if p.name != "__pycache__") == sorted(names)


def test_garbled_text_leaves_nothing(tmp_path):
    source = tmp_path / "u.csv"
    source.write_bytes("name,code\nAnn,a\n".encode("utf-16"))
    script = make(tmp_path)
    result = run_script(script, "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 2
    assert only(tmp_path, "u.csv", "tool.py")


def test_unknown_encoding_leaves_nothing(tmp_path):
    source = tmp_path / "d.csv"
    source.write_text(CSV, encoding="utf-8")
    result = run_script(make(tmp_path), "--input", source, "--output", tmp_path / "o.csv", "--encoding", "nope")
    assert result.returncode == 2
    assert only(tmp_path, "d.csv", "tool.py")


def test_one_column_guess_leaves_nothing(tmp_path):
    source = tmp_path / "colon.csv"
    source.write_text("a:b\n1:2\n", encoding="utf-8")
    result = run_script(make(tmp_path), "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 2
    assert only(tmp_path, "colon.csv", "tool.py")


def test_empty_input_leaves_nothing(tmp_path):
    source = tmp_path / "e.csv"
    source.write_bytes(b"")
    assert run_script(make(tmp_path), "--input", source, "--output", tmp_path / "o.csv").returncode == 2
    assert only(tmp_path, "e.csv", "tool.py")


def test_failure_in_the_second_pass_leaves_nothing(tmp_path):
    """The input changes between passes (a bad byte appears): the run stops with exit 2."""
    source = tmp_path / "d.csv"
    source.write_text(CSV, encoding="utf-8")
    module = load_script_module(make(tmp_path))
    original = module.read_chunks
    calls = []

    def spy(*args, **kwargs):
        calls.append(1)
        if len(calls) == 3:
            source.write_bytes(b"name,code\nAnn,\xff\xfe\xfa\n")
        return original(*args, **kwargs)

    module.read_chunks = spy
    with pytest.raises(SystemExit) as stopped:
        module.main(["--input", str(source), "--output", str(tmp_path / "o.csv")])
    assert stopped.value.code == 2
    assert len(calls) == 3
    assert only(tmp_path, "d.csv", "tool.py")


def test_failure_keeps_an_existing_output_untouched(tmp_path):
    source = tmp_path / "u.csv"
    source.write_bytes("name,code\nAnn,a\n".encode("utf-16"))
    old = tmp_path / "o.csv"
    old.write_text("previous good output\n", encoding="utf-8")
    assert run_script(make(tmp_path), "--input", source, "--output", old).returncode == 2
    assert old.read_text(encoding="utf-8") == "previous good output\n"
    assert only(tmp_path, "u.csv", "tool.py", "o.csv")


def test_output_that_is_a_folder_exits_1_and_leaves_nothing(tmp_path):
    source = tmp_path / "d.csv"
    source.write_text(CSV, encoding="utf-8")
    (tmp_path / "o.csv").mkdir()
    result = run_script(make(tmp_path), "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 1
    assert only(tmp_path, "d.csv", "tool.py", "o.csv")


def test_a_good_run_leaves_exactly_the_three_files(tmp_path):
    source = tmp_path / "d.csv"
    source.write_text(CSV, encoding="utf-8")
    assert run_script(make(tmp_path), "--input", source, "--output", tmp_path / "o.csv").returncode == 0
    assert only(tmp_path, "d.csv", "tool.py", "o.csv", "o_report.txt", "o_report.json")
