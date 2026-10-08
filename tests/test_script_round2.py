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


# ---- 4. headers that differ from the sample ----

SMOKE_ROWS = [m("id", "Id"), m("SBSMK", "Smoke")]


def run_header(tmp_path, header, *extra):
    script = make(tmp_path, rows=SMOKE_ROWS)
    source = write_input(tmp_path, f"id,{header}\n1,yes\n2,no\n")
    return run_script(script, "--input", source, "--output", tmp_path / "o.csv", *extra)


def both_reports(tmp_path):
    return ((tmp_path / "o_report.txt").read_text(encoding="utf-8"),
            (tmp_path / "o_report.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("header,suggestion", [
    ("sbsmk", "sbsmk"),
    (" SBSMK ", " SBSMK "),
    ("SBSMK2", "SBSMK2"),
])
def test_missing_column_lists_the_close_one_in_both_reports(tmp_path, header, suggestion):
    result = run_header(tmp_path, header)
    assert result.returncode == 0, result.stderr
    expected = f'SBSMK not found; did you mean "{suggestion}"?'
    text, js = both_reports(tmp_path)
    assert expected in text
    assert expected.replace('"', '\\"') in js
    assert expected in result.stdout
    assert "Smoke" not in read_cells(tmp_path / "o.csv").columns


def test_none_found_message_includes_the_hint(tmp_path):
    script = make(tmp_path, rows=[m("SBSMK", "Smoke")])
    source = write_input(tmp_path, "a,sbsmk\n1,yes\n")
    result = run_script(script, "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 2
    assert 'SBSMK not found; did you mean "sbsmk"?' in result.stderr
    assert 'SBSMK not found; did you mean "sbsmk"?' in both_reports(tmp_path)[0]


def test_two_close_candidates_are_both_listed_and_not_guessed(tmp_path):
    result = run_header(tmp_path, 'sbsmk,"SbSmk"', "--ignore-case-and-spaces")
    assert result.returncode == 0, result.stderr
    text, _ = both_reports(tmp_path)
    assert '"sbsmk" or "SbSmk"' in text
    assert "Smoke" not in read_cells(tmp_path / "o.csv").columns


@pytest.mark.parametrize("header", ["sbsmk", " SBSMK "])
def test_flag_matches_the_column_and_says_so(tmp_path, header):
    result = run_header(tmp_path, header, "--ignore-case-and-spaces")
    assert result.returncode == 0, result.stderr
    assert read_cells(tmp_path / "o.csv")["Smoke"].tolist() == ["yes", "no"]
    text, js = both_reports(tmp_path)
    assert "--ignore-case-and-spaces was used" in text
    assert f'"{header}"' in text
    assert "not found" not in text
    import json
    report = json.loads(js)
    assert report["matched_columns"] == [{"mapped": "SBSMK", "found": header}]


def test_flag_is_off_by_default(tmp_path):
    result = run_header(tmp_path, "sbsmk")
    assert result.returncode == 0, result.stderr
    assert "--ignore-case-and-spaces was used" not in both_reports(tmp_path)[0]
    assert "Smoke" not in read_cells(tmp_path / "o.csv").columns


def test_flag_not_needed_when_names_agree_so_nothing_is_said(tmp_path):
    result = run_header(tmp_path, "SBSMK", "--ignore-case-and-spaces")
    assert result.returncode == 0, result.stderr
    assert "was used" not in both_reports(tmp_path)[0]


# ---- 5. byte-order marks (Excel "Unicode Text") ----

def run_bytes(tmp_path, raw, *extra):
    script = make(tmp_path)
    source = tmp_path / "in.csv"
    source.write_bytes(raw)
    return run_script(script, "--input", source, "--output", tmp_path / "o.csv", *extra)


TEXT_CRLF = "name,code\r\nAnn,a\r\nBo,b\r\n\r\n"


@pytest.mark.parametrize("raw,chosen", [
    (TEXT_CRLF.encode("utf-16"), "utf-16"),
    (b"\xfe\xff" + TEXT_CRLF.encode("utf-16-be"), "utf-16"),
    (TEXT_CRLF.encode("utf-32"), "utf-32"),
    (b"\x00\x00\xfe\xff" + TEXT_CRLF.encode("utf-32-be"), "utf-32"),
    (b"\xef\xbb\xbf" + TEXT_CRLF.encode("utf-8"), "utf-8-sig"),
])
def test_byte_order_mark_picks_the_encoding(tmp_path, raw, chosen):
    result = run_bytes(tmp_path, raw)
    assert result.returncode == 0, result.stdout + result.stderr
    cells = read_cells(tmp_path / "o.csv")
    assert cells["Code"].tolist() == ["A", "B"] and cells["Name"].tolist() == ["Ann", "Bo"]
    assert chosen in result.stdout
    assert f"Encoding: {chosen}" in (tmp_path / "o_report.txt").read_text(encoding="utf-8")


def test_utf16_with_semicolons_and_accents(tmp_path):
    raw = "name;code\r\nÉlodie;a\r\n".encode("utf-16")
    result = run_bytes(tmp_path, raw)
    assert result.returncode == 0, result.stdout + result.stderr
    assert read_cells(tmp_path / "o.csv")["Name"].tolist() == ["Élodie"]


def test_explicit_encoding_beats_the_byte_order_mark(tmp_path):
    result = run_bytes(tmp_path, TEXT_CRLF.encode("utf-16"), "--encoding", "utf-8")
    assert result.returncode == 2
    assert not (tmp_path / "o.csv").exists()


def test_utf16_without_a_mark_is_still_refused_clearly(tmp_path):
    result = run_bytes(tmp_path, TEXT_CRLF.encode("utf-16-le"))
    assert result.returncode == 2
    assert "utf-16" in result.stderr


# ---- 6. the report explains the app-level traps (results unchanged) ----

import json as _json


def reports_for(tmp_path, rows, text):
    script = make(tmp_path, rows=rows)
    source = write_input(tmp_path, text)
    result = run_script(script, "--input", source, "--output", tmp_path / "o.csv")
    assert result.returncode == 0, result.stdout + result.stderr
    report = _json.loads((tmp_path / "o_report.json").read_text(encoding="utf-8"))
    return (tmp_path / "o_report.txt").read_text(encoding="utf-8"), report


def variable(report, name):
    return [v for v in report["variables"] if v["variable"] == name][0]


SEX_ROWS = [m("id", "Id"), m("sex", "Sex", "Categorical", "{'F': 'Female', 'M': 'Male'}")]
SEX_CSV = "id,sex\n" + "".join(f"{i}, F \n" for i in range(3)) + "7,f\n8,f\n9, m \n10,F\n11,Z\n"


def test_unseen_value_that_matches_after_trimming_is_explained(tmp_path):
    text, report = reports_for(tmp_path, SEX_ROWS, SEX_CSV)
    assert '" F " appeared 3 times, not in the rule; it matches "F" if spaces are trimmed' in text
    entry = [u for u in variable(report, "sex")["unseen_values"] if u["value"] == " F "][0]
    assert entry["would_match"] == {"rule_key": "F", "if": ["spaces are trimmed"]}


def test_unseen_value_that_matches_ignoring_case_is_explained(tmp_path):
    text, report = reports_for(tmp_path, SEX_ROWS, SEX_CSV)
    assert '"f" appeared 2 times, not in the rule; it matches "F" if letter case is ignored' in text
    assert '" m " appeared 1 times, not in the rule; it matches "M" if spaces are trimmed and letter case is ignored' in text
    entry = [u for u in variable(report, "sex")["unseen_values"] if u["value"] == " m "][0]
    assert entry["would_match"]["if"] == ["spaces are trimmed", "letter case is ignored"]


def test_unseen_value_with_no_near_match_gets_no_extra_words(tmp_path):
    text, report = reports_for(tmp_path, SEX_ROWS, SEX_CSV)
    assert '"Z" appeared 1 times, not in the rule\n' in text
    entry = [u for u in variable(report, "sex")["unseen_values"] if u["value"] == "Z"][0]
    assert "would_match" not in entry


def test_results_are_unchanged_by_the_explanations(tmp_path):
    reports_for(tmp_path, SEX_ROWS, SEX_CSV)
    assert read_cells(tmp_path / "o.csv")["Sex"].tolist() == [""] * 3 + [""] * 3 + ["Female", ""]


NA_ROWS = [m("id", "Id"), m("v", "V")]


def test_na_like_text_read_as_empty_is_explained(tmp_path):
    text, report = reports_for(tmp_path, NA_ROWS, "id,v\n1,NA\n2,N/A\n3,null\n4,x\n")
    sentence = "text such as NA, N/A, n/a, NaN, null and None is read as empty"
    assert sentence in text
    assert any(sentence in n for n in variable(report, "v")["notes"])
    assert read_cells(tmp_path / "o.csv")["V"].tolist() == ["", "", "", "x"]


def test_no_na_sentence_when_nothing_is_empty(tmp_path):
    text, report = reports_for(tmp_path, NA_ROWS, "id,v\n1,a\n2,b\n")
    assert "read as empty" not in text
    assert variable(report, "v")["notes"] == []


BOOL = "any non-empty text becomes True, including \"No\" and \"False\""
INT = "decimals are cut off, not rounded (78.6 becomes 78)"


def test_boolean_target_on_text_is_explained(tmp_path):
    rows = [m("id", "Id"), m("smoker", "Smoker", src="string", tgt="boolean")]
    text, report = reports_for(tmp_path, rows, "id,smoker\n1,Yes\n2,No\n")
    assert BOOL in text
    assert any(BOOL in n for n in variable(report, "smoker")["notes"])
    assert read_cells(tmp_path / "o.csv")["Smoker"].tolist() == ["True", "True"]


def test_integer_target_on_decimals_is_explained(tmp_path):
    rows = [m("id", "Id"), m("wt", "Weight", src="float", tgt="integer")]
    text, report = reports_for(tmp_path, rows, "id,wt\n1,78.6\n2,80.1\n")
    assert INT in text
    assert any(INT in n for n in variable(report, "wt")["notes"])
    assert read_cells(tmp_path / "o.csv")["Weight"].tolist() == ["78", "80"]


def test_no_conversion_sentences_for_other_type_pairs(tmp_path):
    rows = [m("id", "Id"), m("wt", "Weight", src="float", tgt="float"), m("s", "S", src="string", tgt="string")]
    text, _ = reports_for(tmp_path, rows, "id,wt,s\n1,78.6,a\n")
    assert BOOL not in text and INT not in text


def test_lookup_rule_gets_no_boolean_sentence(tmp_path):
    rows = [m("id", "Id"), m("s", "S", "Categorical", "{'Yes': True}", src="string", tgt="boolean")]
    text, _ = reports_for(tmp_path, rows, "id,s\n1,Yes\n")
    assert BOOL not in text
