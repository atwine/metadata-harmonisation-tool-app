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
