# Round 2 for Devin: fixes from the adversarial test campaign

Branch `feature/script-export`, folder `.claude/worktrees/feature-script-export`. Same rules as before: commit locally, no push,
no PR, never touch `main`, `staging` or `eval/instrumentation-build`, one commit per item, a test that fails first and passes after,
a running log in `NOTES.md`.

An adversarial campaign (about 60 scenarios, naive-user habits and hostile inputs) found the items below. Each has a recipe so you
can reproduce it. Do them in this order. Add the tests to the repository's `tests/` folder, not to a scratch folder.

## Do not change (note in NOTES.md only)

The script copies the app's engine on purpose, and your parity test proves it. These traps are in the app itself, so they are
**out of scope here** and need an owner decision. Do not "fix" them in the script alone, because that would make the script differ from the app:
- A Yes/No column with target type `boolean` and no rule turns every value into True (`bool("No")` is True).
- A float with target type `integer` truncates (78.6 becomes 78).
- Text that pandas reads as empty (`NA`, `N/A`, `null`, `None`) becomes an empty cell, so a rule for `NA` never fires.
- Spreadsheet formulas (cells starting with `=`, `+`, `-`, `@`) are copied unchanged. Excel runs them.

What you can do inside the script without changing results: make the report **explain** these (see item 6).

## 1. A stray `pandas.py` or `csv.py` next to the script runs (security, do first)

Python puts the script's own folder first on the module search path. A folder (for example Downloads) that holds a file named
`pandas.py`, `csv.py`, `json.py` and so on makes the script import that file instead, which runs foreign code. It also shows the
misleading message "pandas is not installed".

Recipe: put the script in a folder with `pandas.py` containing `open('PWNED.txt','w').write('x'); raise ImportError('fake')` and run
`python t.py --input in.csv --output o.csv` from that folder. `PWNED.txt` appears.

Fix: at the very top of the script, before any other import, remove the script's own folder (and the empty string and the current
folder) from `sys.path`. Do not rely on the caller using `python -I`. Keep the message for a truly missing pandas, but when the import fails
for another reason say what the real error was. Tests: a folder with fake `pandas.py`, `csv.py`, `json.py`, `argparse.py` next to the script;
run without `-I`; assert no marker file and a normal run.

## 2. Decimal commas silently give empty cells

A European or francophone file such as `id;wt` with `1;78,6` converts nothing to empty cells and the report does not say why.

Fix: add `--decimal "."` (default) and `--decimal ","`. With a comma, numbers like `78,6` are read as 78.6 for float and integer columns
(also `1.234,5` style thousands separators only when `--thousands` is given; if that is too much, skip `--thousands`). Also, when a
numeric-target variable has unconverted values and most of them look like `digits,digits`, add one line to the text and JSON reports:
`these look like decimal commas: re-run with --decimal ","`. Note in your report whether `--decimal` changes results compared with the app
(it only changes how the script reads text; the app has no such option).

## 3. An existing output file is silently overwritten

`--output results.csv` replaces an existing `results.csv` without a word.

Fix: refuse (exit 2, a clear message naming the file, nothing changed) when the output or either report file already exists, unless
`--overwrite` is given. Keep your same-file protections from round 1. Test: existing output refused; with `--overwrite` it works;
existing report file alone also refused.

## 4. A header that differs from the sample gives no hint

`SBSMK`, ` sbsmk ` or a renamed column ends with "none of the mapped columns were found" and nothing else.

Fix: when a mapped column is missing, list the closest columns in the file (ignore case and surrounding spaces, then `difflib.get_close_matches`)
in the message and in both reports: `sbsmk not found; did you mean SBSMK?`. Add an opt-in `--ignore-case-and-spaces` flag that matches such columns
(off by default; say in the report when it was used and which columns were matched). Tests: upper case, padded, renamed, and a file with two
close candidates.

## 5. UTF-16 files (Excel "Unicode Text") fail

The message is fine but the script can tell by itself: a file starting with the byte-order mark `FF FE` or `FE FF` is UTF-16.

Fix: detect the BOM (UTF-8, UTF-16 LE and BE, UTF-32 if cheap) before the garbled-text check and use it. Say which encoding was chosen.
Tests: a UTF-16 file with BOM, CRLF, a trailing blank line.

## 6. Make the report explain the app-level traps (no change to results)

In the text and JSON reports, for lookup rules: when an unseen value equals a rule key after trimming spaces or ignoring case, say so
(`" F " appeared 12 times, not in the rule; it matches "F" if spaces are trimmed`). For values that pandas treats as empty (`NA`, `N/A`,
`null`, `NaN`, `None`, `n/a`, empty), count them separately from truly empty cells where you can tell them apart, or at minimum add one sentence to the
report stating that such text is read as empty. Same for a boolean or integer target: add one sentence when a variable has `source_dtype`
string and `target_dtype` boolean, or `source_dtype` float and `target_dtype` integer, saying exactly how the conversion treats the values
(any non-empty text becomes True; decimals are cut off). Tests for each sentence.

## 7. Cap runaway rule results (script only)

A math rule such as `x * 100000000` on a text column took 36 seconds, and a larger repeat never finished. The app's engine has the same flaw, which
stays out of scope. In the script only: if a cell's result is longer than 1,000,000 characters, count it as an error for that cell and move on
(report it). Test: `x * 999999999` with source type string finishes in under 10 seconds and reports the errors. Mention in NOTES.md that this makes the
script safer than the app in this one case.

## 8. Small things

- **Beta label.** On the Download Results page, put a small "Beta" badge next to the "Transform script" title, with one line of text
  ("New: tell us what breaks"). Match the existing styling.
- **Not found.** `GET /api/download/<study>/script` for a study that does not exist should answer 404 ("Study not found"), not the
  "no variables marked" 422. Keep 422 for a study that exists but has nothing mapped. Test both.
- **Event loop.** The route builds the script synchronously inside an `async def`, which freezes the whole app for about 7 seconds on a
  2,000-variable study. Run the generation in a thread (`run_in_threadpool` or make the route a plain `def`). Test: a request for a large study does not
  block another request (for example a `GET /api/studies/` completes while it runs).

## What to hand back

The same report as before (what changed, test counts before and after, differences between script and app, anything you could not do, the commit list
from `git log --oneline origin/development..HEAD`), plus a table with one row per item above: item, the test that proves it, and the result of re-running its
recipe. Then wait.
