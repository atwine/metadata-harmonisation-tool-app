"""P1 parity: the generated script must give the same answers as the in-app engine.

The fixture study uses every case in the plan (section 2): direct, categorical,
no instruction, missing column, duplicate target, empty cells, bad values.
"""

import json

import pandas as pd
import pytest

from script_export_helpers import (
    REPO, app_output, m, make_script, read_cells, run_script, setup_study,
)

STUDY = "FIX_STUDY"

FIXTURE_DATA = (
    "pid,sex,wt_lb,age,visit,grade,height,flag,bad_expr,evil,note,smk,dupe_a,dupe_b,weird,spaced,todo_col\n"
    "P1,F,150.5,34,1,1,1.80,1,5,6,hello,N,a,b,w,7,x\n"
    "P2,M,abc,,2,2,1.65,0,6,7,,S,c,d,v,8,y\n"
    "P3,X,200,51,1,3,,1,7,8,tab\tbed,F,e,f,u,9,z\n"
    "P4,,,abc,,,1.75,,8,9,\"quo,te\",N,g,h,t,,w\n"
    "P5,F,99.9,40,2,1,1.50,0,9,1,plain,S,i,j,s,10,v\n"
)

FIXTURE_MAPPINGS = [
    m("pid", "Participant ID"),
    m("sex", "Sex", "Categorical", "{'F': 'Female', 'M': 'Male'}"),
    m("wt_lb", "Weight kg", "Direct", "x * 0.4536", "float", "float"),
    m("age", "Age years", None, None, "string", "integer"),
    m("visit", "Visit code", "Categorical", "{'1': 10, '2': 20}", "string", "integer"),
    m("grade", "Grade", "Categorical", "{'1': 10, '2': 20, '3': 30}", "string", "integer"),
    m("height", "Height cm", "Direct", "x * 100", "float", "integer"),
    m("flag", "Flag", None, None, "string", "boolean"),
    m("bad_expr", "Bad expression", "Direct", "x +", "float", "float"),
    m("evil", "Evil expression", "Direct", "__import__('os').system('echo hi')", "float", "float"),
    m("note", "Note", None, None, "string", "string"),
    m("smk", "Smoking", "Categorical", "{'N': 'Never', 'S': 'Smoker', 'F': 'Former'}"),
    m("gone", "Missing column var", "Direct", "x + 1", "float", "float"),
    m("dupe_a", "Dupe target"),
    m("dupe_b", "Dupe target"),
    m("weird", "Weird type", "Surprise", "x", "string", "string"),
    m("spaced", "Leading space", "Direct", " x + 1", "float", "float"),
    m("todo_col", "Not mapped", None, None, marked="To do"),
]


def compare(app_frame, app_counts, script_frame, script_json):
    assert list(app_frame.columns) == list(script_frame.columns)
    assert len(app_frame) == len(script_frame)
    pd.testing.assert_frame_equal(app_frame, script_frame)
    script_counts = {x["variable"]: (x["successes"], x["errors"]) for x in script_json["metrics"]}
    assert script_counts == app_counts


@pytest.fixture
def fixture_study(tmp_path, monkeypatch):
    setup_study(tmp_path, monkeypatch, STUDY, FIXTURE_DATA, FIXTURE_MAPPINGS)
    return tmp_path


def test_fixture_study_parity(fixture_study):
    tmp = fixture_study
    app_frame, app_counts = app_output(STUDY)
    script = make_script(tmp, STUDY)
    data = tmp / "input" / STUDY / "example_data.csv"
    out = tmp / "out.csv"

    result = run_script(script, "--input", data, "--output", out)

    assert result.returncode == 0, result.stderr
    script_json = json.loads((tmp / "out_report.json").read_text(encoding="utf-8"))
    compare(app_frame, app_counts, read_cells(out), script_json)


def test_ch_sib_parity(tmp_path, monkeypatch):
    source = REPO / "example_data" / "CH_SIB" / "example_data.csv"
    rows = [m(c, f"CB_{c}") for c in ("pt", "phyact", "alcfrq", "ethori_self", "jobtyp", "lvpl", "cafuse")]
    rows += [
        m("sbsmk", "Smoking Status", "Categorical", "{'F': 'Former', 'S': 'Smoker', 'N': 'Never'}"),
        m("SBP", "Systolic", "Direct", "x * 1", "float", "float"),
        m("wt", "Weight lb", "Direct", "x * 2.2046", "float", "float"),
        m("age", "Age", None, None, "string", "integer"),
        m("mrtsts2", "Married", None, None, "float", "integer"),
        m("gender", "Gender", "Categorical", "{'0': 'Male', '1': 'Female'}"),
    ]
    setup_study(tmp_path, monkeypatch, "CH_SIB", source.read_bytes(), rows)

    app_frame, app_counts = app_output("CH_SIB")
    script = make_script(tmp_path, "CH_SIB")
    out = tmp_path / "ch_out.csv"
    result = run_script(script, "--input", tmp_path / "input" / "CH_SIB" / "example_data.csv", "--output", out)

    assert result.returncode == 0, result.stderr
    script_json = json.loads((tmp_path / "ch_out_report.json").read_text(encoding="utf-8"))
    compare(app_frame, app_counts, read_cells(out), script_json)
