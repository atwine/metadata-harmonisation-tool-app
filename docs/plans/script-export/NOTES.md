# Running log: script export

## Baseline (Phase 0)
- Branch `feature/script-export`, started from `origin/development` plus the plan commits.
- Baseline: `python -m pytest -q` gave **113 passed** in about 6 seconds.
- Pre-commit hook installed with `python -m pre_commit install` (gitleaks runs on commit).
- Python 3.12.6, pandas 2.2.3 on this machine.
- D1 to D5, D7 to D9 are answered ("recommended" or an explicit answer). D6 is not blocking.

## Choices the plan did not cover (flag for the owner)
Each one below is the smallest, easiest to undo option. Overrule any of them.

1. **The route is a GET**: `GET /api/download/{study_name}/script`. The plan says "a foreign Origin gets 403".
   The app's origin check only covers state-changing requests (POST, PUT, PATCH, DELETE), the same as the existing
   `GET .../mapping-csv`. So a foreign Origin on this GET is not refused by the app; the browser's cross-site rules stop
   the other site reading the reply (the existing `website` case in `test_access.py` checks that). A foreign Host is
   refused with 403. The script holds mappings only, never participant data.
   Option not taken: make it a POST so the origin check applies. More code for the browser side, no extra safety.
2. **The script reads the input file up to three times** (to match the app exactly):
   (a) work out each column's type the way the app's one-shot read does, so `5` stays `5` and `5.0` stays `5.0`;
   (b) run the conversions to count results and find the true output type of each column;
   (c) run them again and write the file. The app turns a whole-number column into decimals (`1.0`) as soon as one cell is
   empty; the script does the same, which needs the full-file answer before the first row is written.
   Cost: about three times the read time. Option not taken: one pass, which would write `1` in some places and `1.0` in others.
3. **Warnings are listed once per variable.** The app adds the "Unknown transformation type" warning once per cell.
   The script adds it once per variable.
4. **No variable usable** (every mapped column missing from the input file): exit code 2, no output file, the report is still written.
5. **Report base name**: `--report` sets the base path; the files are `<base>.txt` and `<base>.json`.
   Default base is the output path without extension plus `_report`.

## Log
- Phase 1: parity harness and fixture study (17 mapped variables covering direct, lookup, no instruction, missing column,
  duplicate target, unknown type, bad expression, injection string, empty cells). Failed with NotImplementedError until the generator existed.
- Phase 2: generator `backend/core/script_export.py` plus fixed template `backend/core/script_template.py`.
  The mappings go in as JSON lines, each written with `repr()` as a quoted string. Parity passed on the first run
  against the fixture and `example_data/CH_SIB`.
- Phase 3: `GET /api/download/{study_name}/script`, `ACCESS.md` rows (classified under `exports`), endpoint tests.
- Phase 4: button added to `download-results.tsx` and `downloadScript` in `client.ts`. Checked in headless Chrome
  against a scratch workspace (backend on 127.0.0.1:8011, vite on 127.0.0.1:5188; both stopped, scratch folder deleted).
  Screenshot: `screenshots/download-script-button.png`. The file the browser downloaded was run on `example_data/CH_SIB`
  and matched the app's output cell for cell.
- Phase 5: `docs/script-export.md`, README link and route row, CHANGELOG entry under `[Unreleased]`.

## Test counts
- Before: 113 passed. After: see the final report (40 new tests in parity 2, behaviour 30, endpoint 8, plus 3 new access-grid cases for the new route = 43 more, 156 total).

## Surprises
- pandas is installed in the user site-packages on this machine, and `python -I` hides user site-packages, so the plan's
  `python -I script.py` could not import pandas. The test helper probes for this and falls back to `python -E`
  (still ignores `PYTHON*` environment variables). On a normal virtualenv it uses `-I`.
- The app turns a whole-number column into decimals as soon as one cell is empty (34 becomes 34.0), and compares lookup
  keys against `str(value)` of a column pandas has read as decimals (a column with empty cells has keys `1.0`, not `1`).
  The script copies both on purpose so the outputs match. The lookup one is an app quirk worth a look: a rule written
  as `{'1': ...}` never matches a numeric column that has any empty cell. Not changed here (out of scope).
- A one-column file cannot hold an empty cell (the blank line is skipped on re-read). Same as the app.
- A single-column input is valid when its column is a mapped one, so the "only one column found" stop applies only
  when none of the mapped columns are in the header.

## Could not do / not verified
- Only tested on pandas 2.2.3 and Python 3.12.6. The script declares pandas 1.5 and Python 3.8 as minimums but these
  were not run.
- Chrome extension was not connected; the browser check used headless Chrome through Playwright.
- A script that exits with code 2 or 1 after the writability pre-check can leave an empty output file behind.

## Follow-up round
### 1. True/False columns (fixed)
- Cause: a True/False column with an empty cell is stored by pandas as Python booleans plus NaN (dtype object); the script
  treated every object column as text, so `"False"` became True under `bool()`. Fix: such columns are now left to pandas'
  own reading, per chunk, which gives the same booleans. Tests: 22 parity cases (no empty, one empty, empty only in the second
  chunk; targets boolean, integer, string; one chunk and tiny chunks), written first and seen failing (6 failures).
- Mixed `5` and `5.0` in one column: matches the app (decimals, lookup keys `5.0`), including across chunks. Numbers and words
  in one column (all text) also match. Not matchable: a very large file where pandas itself splits the read into internal
  blocks and mixes Python ints and strings inside one column. The script cannot reproduce that, and the app's own result there
  depends on file size. Stated in `docs/script-export.md`.

### 2. Input overwritten (fixed)
- Cause: the same-file check used abspath. Now `same_file` uses `os.path.samefile` when both exist, else normcase(realpath).
  Output, .txt report and .json report are each checked against the input and the script itself, before anything is written (exit 2).
- Tests (tests/test_script_file_safety.py), seen failing first: different letter case, hard link, report aimed at the input
  (.txt and .json), output is the script, report is the script. Symbolic-link test is skipped on this machine (needs admin rights
  on Windows); the hard-link test covers the same `samefile` path.

### 3. Half-written or empty files (fixed)
- Cause: the pre-flight `open(target, 'a')` created empty files, and a failure in a later pass left a partial output.
- Fix: new `Staging` class. The output and both reports are written to `.tmp_*.part` files in the destination folder and moved
  into place (`os.replace`) only after everything worked; any exit deletes leftover temp files. The pre-flight check is gone: creating
  the temp files is the writability check (exit 1; an output path that is a folder is also exit 1).
- Kept on purpose: when none of the mapped columns exist in the input, the report files are still written (that is the only
  place the reason is listed), but no output file is.
- If moving the three files into place fails part way (very unlikely), files already moved stay. Documented here only.
- Tests (tests/test_script_no_leftovers.py), seen failing first: garbled text, unknown encoding, one-column guess, empty input,
  input changing between passes (exit 2 in the second pass), existing output kept untouched on failure. Also: output is a folder
  gives exit 1 with nothing left, and a good run leaves exactly the output and two reports.

### Small things (done)
- JSON report now has a `warning` field with the same sentence as the text report (one shared constant).
- Script route sends an RFC 6266 header (ASCII fallback `filename=` plus `filename*=UTF-8''...`), so Cyrillic study names work.
  Not changed: the existing mapping-csv route still builds its header from the raw name, so it will fail the same way for
  non-Latin study names (generic 500). Left alone as asked; worth a separate fix.
