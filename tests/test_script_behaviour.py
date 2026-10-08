"""Tests P2 (malicious input), P3 (big file), P4 (edge cases), P7 (results report)."""

import ast
import importlib.util
import json
import re
import time

import pandas as pd
import pytest

from script_export_helpers import (
    REPO, app_output, script_export, m, make_script, read_cells, run_script, setup_study,
)

STUDY = "EDGE_STUDY"


def write_script(tmp_path, study, rows, name="script.py"):
    path = tmp_path / name
    path.write_text(script_export.render_script(script_export.build_config(study, rows)), encoding="utf-8")
    return path


def load_script_module(path):
    spec = importlib.util.spec_from_file_location("generated_script", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---- P2: user-controlled text never becomes code ---------------------------------

EVIL_TEXTS = [
    "__import__('os').system('echo PWNED > pwned.txt')",
    'quote " and \' and """ and \'\'\' and \\ and \n newline and \r and {braces} %s %(x)s',
    "x" * 200_000,
    "'; import os; os.system('echo PWNED > pwned.txt') #",
    "\u202e unicode \u2028 separators \U0001F600",
]


@pytest.mark.parametrize("evil", EVIL_TEXTS, ids=["import", "quotes", "long", "breakout", "unicode"])
def test_p2_user_text_stays_data(tmp_path, monkeypatch, evil):
    monkeypatch.chdir(tmp_path)
    rows = [
        m(evil, evil, "Direct", evil, "float", "float"),
        m("code", "Code", "Categorical", evil),
        m("plain", "Plain", "Direct", "__import__('os').system('echo PWNED > pwned.txt')", "float", "float"),
    ]
    script_path = write_script(tmp_path, evil, rows)
    script_text = script_path.read_text(encoding="utf-8")

    tree = ast.parse(script_text)
    called = {
        n.func.id for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert not called & {"eval", "exec", "compile", "__import__"}, called
    assert "echo PWNED" not in "\n".join(
        line for line in script_text.splitlines() if not line.lstrip().startswith("'")
    ), "user text found outside the data block"

    data = pd.DataFrame({evil: ["1", "2"], "code": ["a", "b"], "plain": ["3", "4"]})
    source = tmp_path / "data.csv"
    data.to_csv(source, index=False)
    result = run_script(script_path, "--input", source, "--output", tmp_path / "out.csv", cwd=tmp_path)

    assert result.returncode == 0, result.stderr[-500:]
    assert not (tmp_path / "pwned.txt").exists()
    report = json.loads((tmp_path / "out_report.json").read_text(encoding="utf-8"))
    by_var = {v["variable"]: v for v in report["variables"]}
    assert by_var["plain"]["errors"] == 2
    assert by_var["plain"]["converted"] == 0
    assert by_var["code"]["converted"] == 0


def test_p2_help_works_with_percent_in_study_name(tmp_path):
    script = write_script(tmp_path, "100% %(prog)s study", [m("a", "A")])
    result = run_script(script, "--help")
    assert result.returncode == 0, result.stderr


def test_script_holds_mappings_not_participant_data(tmp_path, monkeypatch):
    source = (REPO / "example_data" / "CH_SIB" / "example_data.csv")
    setup_study(tmp_path, monkeypatch, "CH_SIB", source.read_bytes(), [m("pt", "Participant"), m("sbsmk", "Smoking")])
    script_text = make_script(tmp_path, "CH_SIB").read_text(encoding="utf-8")
    participant_ids = pd.read_csv(source)["pt"].astype(str).tolist()
    assert participant_ids and not any(pid in script_text for pid in participant_ids)


# ---- P3: big file runs in chunks ---------------------------------------------------


def test_p3_big_file_runs_in_chunks(tmp_path):
    rows = 200_000
    source = tmp_path / "big.csv"
    with open(source, "w", encoding="utf-8", newline="") as f:
        f.write("id,sex,wt\n")
        f.writelines(f"{i},{'FM'[i % 2]},{50 + (i % 40)}.5\n" for i in range(rows))
    mappings = [
        m("id", "ID"),
        m("sex", "Sex", "Categorical", "{'F': 'Female', 'M': 'Male'}"),
        m("wt", "Weight lb", "Direct", "x * 2.2046", "float", "float"),
    ]
    script = write_script(tmp_path, "BIG", mappings)
    module = load_script_module(script)

    assert 1_000 <= module.CHUNK_ROWS <= 100_000
    seen_sizes = []
    original = module.read_chunks

    def spy(*args, **kwargs):
        for chunk in original(*args, **kwargs):
            seen_sizes.append(len(chunk))
            yield chunk

    module.read_chunks = spy
    start = time.time()
    code = module.main(["--input", str(source), "--output", str(tmp_path / "big_out.csv")])
    elapsed = time.time() - start

    assert code == 0
    assert elapsed < 30, f"took {elapsed:.1f}s"
    assert max(seen_sizes) <= module.CHUNK_ROWS
    assert len(seen_sizes) >= 3 * (rows // module.CHUNK_ROWS)
    out = pd.read_csv(tmp_path / "big_out.csv", dtype=str)
    assert len(out) == rows
    assert out.loc[1, "Sex"] == "Male"


# ---- P4: edge cases ----------------------------------------------------------------

SIMPLE = [m("name", "Name"), m("code", "Code", "Categorical", "{'a': 'A', 'b': 'B'}")]


def simple_script(tmp_path):
    return write_script(tmp_path, STUDY, SIMPLE)


def test_p4_empty_file(tmp_path):
    source = tmp_path / "empty.csv"
    source.write_bytes(b"")
    result = run_script(simple_script(tmp_path), "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 2
    assert "empty" in result.stderr


def test_p4_header_only(tmp_path):
    source = tmp_path / "h.csv"
    source.write_text("name,code\n", encoding="utf-8")
    result = run_script(simple_script(tmp_path), "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 0, result.stderr
    out = pd.read_csv(tmp_path / "o.csv", dtype=str)
    assert list(out.columns) == ["Name", "Code"] and len(out) == 0


def test_p4_missing_source_column(tmp_path):
    source = tmp_path / "d.csv"
    source.write_text("name,other\nAnn,1\n", encoding="utf-8")
    result = run_script(simple_script(tmp_path), "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 0, result.stderr
    assert list(pd.read_csv(tmp_path / "o.csv").columns) == ["Name"]
    report = json.loads((tmp_path / "o_report.json").read_text(encoding="utf-8"))
    assert report["skipped"] == [{"variable": "code", "reason": "missing_column"}]
    assert "Source column missing: code" in report["warnings"]


def test_p4_no_mapped_column_found(tmp_path):
    source = tmp_path / "d.csv"
    source.write_text("zzz,yyy\n1,2\n", encoding="utf-8")
    result = run_script(simple_script(tmp_path), "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 2
    assert (tmp_path / "o_report.txt").read_text(encoding="utf-8").count("Source column missing") == 2


def test_p4_output_not_writable(tmp_path):
    source = tmp_path / "d.csv"
    source.write_text("name,code\nAnn,a\n", encoding="utf-8")
    result = run_script(simple_script(tmp_path), "--input", source, "--output", tmp_path / "no_such_folder" / "o.csv")
    assert result.returncode == 1
    assert "Cannot write" in result.stderr


def test_p4_missing_input_and_bad_arguments(tmp_path):
    script = simple_script(tmp_path)
    assert run_script(script, "--input", tmp_path / "nope.csv", "--output", tmp_path / "o.csv").returncode == 2
    assert run_script(script, "--output", tmp_path / "o.csv").returncode == 2


def test_p4_output_must_differ_from_input(tmp_path):
    source = tmp_path / "d.csv"
    source.write_text("name,code\nAnn,a\n", encoding="utf-8")
    result = run_script(simple_script(tmp_path), "--input", source, "--output", source)
    assert result.returncode == 2
    assert source.read_text(encoding="utf-8") == "name,code\nAnn,a\n"


@pytest.mark.parametrize("sep", [";", "\t", "|"])
def test_p4_other_separators_are_guessed(tmp_path, sep):
    script = simple_script(tmp_path)
    comma = tmp_path / "c.csv"
    comma.write_text("name,code\nAnn,a\nBo,b\nCy,z\n", encoding="utf-8")
    other = tmp_path / "o.csv"
    other.write_text("name{0}code\nAnn{0}a\nBo{0}b\nCy{0}z\n".format(sep), encoding="utf-8")
    assert run_script(script, "--input", comma, "--output", tmp_path / "out_c.csv").returncode == 0
    result = run_script(script, "--input", other, "--output", tmp_path / "out_o.csv")
    assert result.returncode == 0, result.stderr
    pd.testing.assert_frame_equal(read_cells(tmp_path / "out_c.csv"), read_cells(tmp_path / "out_o.csv"))


def test_p4_latin1_file_with_accents(tmp_path):
    source = tmp_path / "l.csv"
    source.write_bytes("name,code\nZo\u00eb,a\nRen\u00e9,b\n".encode("latin-1"))
    result = run_script(simple_script(tmp_path), "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 0, result.stderr
    assert "latin-1" in result.stdout
    assert read_cells(tmp_path / "o.csv")["Name"].tolist() == ["Zo\u00eb", "Ren\u00e9"]


def test_p4_utf8_with_bom(tmp_path):
    source = tmp_path / "b.csv"
    source.write_bytes("\ufeffname,code\nZo\u00eb,a\n".encode("utf-8"))
    result = run_script(simple_script(tmp_path), "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 0, result.stderr
    out = read_cells(tmp_path / "o.csv")
    assert list(out.columns) == ["Name", "Code"] and out["Name"].tolist() == ["Zo\u00eb"]


def test_p4_wrong_encoding_guess_recovered_with_flag(tmp_path):
    source = tmp_path / "e.csv"
    source.write_bytes("name,code\nEuro \u20ac,a\n".encode("cp1252"))
    script = simple_script(tmp_path)
    guessed = run_script(script, "--input", source, "--output", tmp_path / "o1.csv")
    assert guessed.returncode == 0
    assert "\u20ac" not in read_cells(tmp_path / "o1.csv")["Name"][0]
    fixed = run_script(script, "--input", source, "--output", tmp_path / "o2.csv", "--encoding", "cp1252")
    assert fixed.returncode == 0
    assert read_cells(tmp_path / "o2.csv")["Name"].tolist() == ["Euro \u20ac"]


def test_p4_utf16_is_reported_as_garbled(tmp_path):
    source = tmp_path / "u.csv"
    source.write_bytes("name,code\nAnn,a\n".encode("utf-16"))
    script = simple_script(tmp_path)
    result = run_script(script, "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 2 and "--encoding" in result.stderr
    assert run_script(script, "--input", source, "--output", tmp_path / "o.csv", "--encoding", "utf-16").returncode == 0


def test_p4_wrong_separator_guess_recovered_with_flag(tmp_path):
    source = tmp_path / "colon.csv"
    source.write_text("name:code\nAnn:a\nBo:b\n", encoding="utf-8")
    script = simple_script(tmp_path)
    guessed = run_script(script, "--input", source, "--output", tmp_path / "o.csv")
    assert guessed.returncode == 2 and "--sep" in guessed.stderr
    fixed = run_script(script, "--input", source, "--output", tmp_path / "o.csv", "--sep", ":")
    assert fixed.returncode == 0, fixed.stderr
    assert read_cells(tmp_path / "o.csv")["Code"].tolist() == ["A", "B"]


def test_p4_whole_number_column_with_gaps_matches_the_app(tmp_path, monkeypatch):
    """The app writes 34.0 (not 34) once any cell in the column is empty."""
    data = "age,flag\n34,1\n,0\n51,1\n"
    rows = [m("age", "Age", None, None, "string", "integer"), m("flag", "Flag", None, None, "string", "integer")]
    setup_study(tmp_path, monkeypatch, STUDY, data, rows)
    app_frame, _ = app_output(STUDY)
    script = make_script(tmp_path, STUDY)
    out = tmp_path / "o.csv"
    assert run_script(script, "--input", tmp_path / "input" / STUDY / "example_data.csv", "--output", out).returncode == 0
    pd.testing.assert_frame_equal(app_frame, read_cells(out))
    assert read_cells(out)["Age"].tolist() == ["34.0", "", "51.0"]
    assert read_cells(out)["Flag"].tolist() == ["1", "0", "1"]


def test_p4_column_types_hold_across_chunks(tmp_path):
    """A gap in a late chunk must not change how earlier chunks are written."""
    source = tmp_path / "chunky.csv"
    source.write_text("n,k\n1,a\n2,a\n3,a\n,a\n5,a\n", encoding="utf-8")
    script = write_script(tmp_path, "CH", [m("n", "N", None, None, "string", "integer"), m("k", "K")])
    module = load_script_module(script)
    module.CHUNK_ROWS = 2
    assert module.main(["--input", str(source), "--output", str(tmp_path / "o.csv")]) == 0
    assert read_cells(tmp_path / "o.csv")["N"].tolist() == ["1.0", "2.0", "3.0", "", "5.0"]


# ---- P7: results report ------------------------------------------------------------


def report_study(tmp_path, values, extra_rows=()):
    source = tmp_path / "r.csv"
    pd.DataFrame({"sex": values, "other": range(len(values))}).to_csv(source, index=False)
    rows = [m("sex", "Sex", "Categorical", "{'F': 'Female', 'M': 'Male'}"), m("gone", "Gone")] + list(extra_rows)
    script = write_script(tmp_path, STUDY, rows)
    out = tmp_path / "r_out.csv"
    result = run_script(script, "--input", source, "--output", out)
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "r_out_report.json").read_text(encoding="utf-8"))
    text = (tmp_path / "r_out_report.txt").read_text(encoding="utf-8")
    return out, report, text, result


def test_p7_unseen_values_counted(tmp_path):
    values = ["F"] * 30 + ["M"] * 20 + ["X"] * 42 + ["Y"] + [None] * 7
    out, report, text, result = report_study(tmp_path, values)
    sex = next(v for v in report["variables"] if v["variable"] == "sex")

    assert sex["unseen_values"] == [{"value": "X", "rows": 42}, {"value": "Y", "rows": 1}]
    assert sex["unseen_total_rows"] == 43
    assert sex["converted"] == 50 and sex["rows"] == 100
    assert sex["empty"] == 50 and sex["empty_because_source_empty"] == 7 and sex["empty_not_converted"] == 43
    assert (read_cells(out)["Sex"] == "").sum() == sex["empty"]
    assert '"X" appeared 42 times, not in the rule' in text
    assert '"Y" appeared 1 times, not in the rule' in text
    assert text.startswith("WARNING: this report names raw values")
    assert "participant" in " ".join(text.splitlines()[:2])


def test_p7_missing_column_and_text_json_agree(tmp_path):
    out, report, text, result = report_study(tmp_path, ["F", "M", "Q"])
    assert report["skipped"] == [{"variable": "gone", "reason": "missing_column"}]
    assert "- gone: source column not found in the input file" in text
    for metric in report["metrics"]:
        assert f"- {metric['variable']}: success={metric['successes']}, errors={metric['errors']}" in text
    assert f"Total successes: {report['total_successes']}" in text
    assert f"Total errors: {report['total_errors']}" in text
    assert "Results report" in result.stdout and "Successes:" in result.stdout


def test_p7_unseen_list_is_capped_at_50(tmp_path):
    values = [f"v{i:03d}" for i in range(60) for _ in range(2)] + ["common"] * 5
    out, report, text, _ = report_study(tmp_path, values)
    sex = next(v for v in report["variables"] if v["variable"] == "sex")
    assert len(sex["unseen_values"]) == 50
    assert sex["unseen_values"][0] == {"value": "common", "rows": 5}
    assert sex["unseen_values_not_listed"] == 11 and sex["unseen_rows_not_listed"] == 22
    assert "and 11 more distinct values (22 rows) not listed" in text


def test_p7_math_examples_are_limited_to_five(tmp_path):
    source = tmp_path / "m.csv"
    pd.DataFrame({"w": ["bad%d" % i for i in range(9)] + ["10"]}).to_csv(source, index=False)
    script = write_script(tmp_path, STUDY, [m("w", "W", "Direct", "x * 2", "float", "float")])
    assert run_script(script, "--input", source, "--output", tmp_path / "o.csv").returncode == 0
    report = json.loads((tmp_path / "o_report.json").read_text(encoding="utf-8"))
    w = report["variables"][0]
    assert w["unconvertible_examples"] == ["bad0", "bad1", "bad2", "bad3", "bad4"]
    assert w["empty_not_converted"] == 9 and w["converted"] == 1


def test_p7_report_path_can_be_chosen(tmp_path):
    source = tmp_path / "d.csv"
    source.write_text("name,code\nAnn,a\n", encoding="utf-8")
    script = simple_script(tmp_path)
    result = run_script(script, "--input", source, "--output", tmp_path / "o.csv", "--report", tmp_path / "my_report")
    assert result.returncode == 0
    assert (tmp_path / "my_report.txt").exists() and (tmp_path / "my_report.json").exists()
    assert not re.search(r"o_report", " ".join(p.name for p in tmp_path.iterdir()))
