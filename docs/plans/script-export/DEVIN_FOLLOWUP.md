# Follow-up for Devin: three fixes before this branch can merge

Branch: `feature/script-export`, folder `.claude/worktrees/feature-script-export`. Same rules as `DEVIN_PROMPT.md`:
commit locally, no push, no PR, never touch `main`, `staging` or `eval/instrumentation-build`.

An independent review of your work found three real problems and one merge step. Fix them in this order,
one commit each, with a test that fails first and passes after. Keep your running log in `NOTES.md`.

## 1. True/False columns silently flip (blocks merging)

**Where:** `backend/core/script_template.py`, `infer_column_dtypes` (around lines 281-297) and the use at about line 557.

**What goes wrong:** when the app reads the whole CSV, a True/False column with at least one empty cell is stored as
real booleans plus empty values (pandas dtype `object`). The script sees kind `"O"` and reads the column as text, so
the cells become the strings `"True"` and `"False"`. Then `dtype_cast(..., "boolean")` turns the text `"False"` into
**True**, because `bool("False")` is True. The app gives False. With an `integer` target the app gives 0 and 1, the
script gives empty cells and "not converted". The same thing happens when a True/False column spans chunks and only
one chunk has an empty cell (kinds `{"b", "O"}` become text).

**Fix:** make the script give the same answer as the app for True/False columns, with or without empty cells,
within one chunk and across chunks. Do not change the app's engine. Add tests to the parity harness: a boolean column
with no empty cells, with one empty cell, and with an empty cell in only the second chunk, for target types `boolean`,
`integer` and `string`. Compare cell for cell against `transform_engine.py`.

Also check, and add a test for, the related case the review noted: a column the app reads as mixed types
(for example `5` in one place and `5.0` in another, which changes lookup keys). If you cannot match it, say so in
`NOTES.md` and in your final report instead of guessing.

## 2. The input file can be overwritten (blocks merging)

**Where:** `script_template.py` around line 506 (the same-file check) and around line 565 (where the output is opened).

**What goes wrong:** the check uses `os.path.abspath`, which ignores letter case and links. On Windows
`--input data.csv --output DATA.csv` passes the check, then the output is opened for writing, which empties the input
before the second pass reads it. The source data is lost. Related: nothing stops `--report` from pointing at the input
(the report files are written at the end and would overwrite it), or `--output` from pointing at the script itself.

**Fix:** compare with `os.path.samefile` when both files exist, and otherwise `os.path.normcase(os.path.realpath(...))`.
Refuse (exit code 2, a clear message, nothing written) when the output, the `.txt` report or the `.json` report is the
same file as the input or the script. Tests: same name with different letter case (skip only where the file system is
case sensitive), a symbolic link to the input where the platform allows it, and `--report` aimed at the input.

## 3. A failed run can leave a half-written or empty output file

**Where:** the pre-flight `open(target, "a")` at about lines 509-513 creates empty files; later `fail(2, ...)` calls
(bad encoding, garbled text, one column, header read failure) leave them behind; and a read error in the second pass
(`read_chunks` calls `fail`, which raises `SystemExit`, which the `except OSError` at about line 572 does not catch)
leaves a partly written output with a valid header and no report.

**Fix:** write the output and both reports to temporary files in the same folder, and move them into place only
after everything succeeded. On any failure, delete the temporary files and leave nothing behind. If you keep the
writability pre-check, do not let it create files. Tests: a run that fails in the second pass (for example the input
changes between passes, or a late bad byte), a garbled-text failure, and a bad encoding: in each, assert that no output
file and no report file exists afterwards.

## 4. Merge `development` into this branch

`development` has moved on (10 commits: the security work and the final fixes). Merge it into this branch with
`git merge origin/development` (a merge, not a rebase). The only conflict expected is `CHANGELOG.md`: keep both sides,
with your entry under `[Unreleased]`. Re-run the full test suite after the merge. Do not push.

## Small things, do them if they are quick

- The JSON report has `contains_participant_values: true` but no warning text. Add the same warning sentence the text report has.
- Study names in non-Latin scripts (for example Cyrillic) are valid in the app, but the download header cannot encode them
  and the route returns a generic 500. Use an RFC 6266 `filename*=UTF-8''...` header (keep an ASCII fallback name) for the
  script route only, with a test. Do not change the existing mapping-CSV route in this branch; just note it in `NOTES.md`.

## What to hand back

The same report format as before (what changed, test counts before and after, differences between script and app,
anything you could not finish, the commit list from `git log --oneline origin/development..HEAD`), plus:
a table of the three blocking items with the test that proves each, and the result of the merge. Then wait.
