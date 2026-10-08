# Plan: export a script that transforms a full dataset

Branch: `feature/script-export` (cut from `origin/development`, the app line).
Status: plan written, nothing built. All owner decisions (D1 to D9) are answered in `DECISIONS.md`. Version 1 is a deliberately rough first pass: prove the path end to end, then poke holes.

## 1. The problem, in plain words

Today the tool applies a researcher's confirmed mappings to the **example data**
only (the small sample CSV uploaded with each study). The Download Results page
returns a ZIP with the transformed sample.

A researcher with the **full dataset** (often too large or too sensitive to upload)
has no way to apply the same mappings. This feature gives them a small Python
script they download from the app and run **on their own machine**, against their
own full CSV. The full data never goes through the app.

Example: Study CH_SIB has `sbsmk` mapped to `Smoking Status` with a categorical
rule `{"F": "Former", "S": "Smoker", "N": "Never"}`. The researcher clicks
"Download script", then runs
`python transform_CH_SIB.py --input my_full_data.csv --output out.csv`,
and gets a CSV with the codebook column names and converted values.

This is a last-resort feature. It must be small and boring, not clever.

## 2. What the current engine does (the behaviour to copy exactly)

Source: `backend/core/transform_engine.py` and `backend/core/transformation_utils.py`.
Read both files fully before starting.

- Only mappings with `marked == "Successfully mapped"` are used.
- Output column name is `codebook_var` (falls back to `study_var`).
- If the source column is missing from the data, that variable is skipped with a warning.
- If two study variables map to the same codebook column, the first one wins and the
  second is skipped with a warning.
- Empty (NaN) cells stay empty.
- No instructions: value is cast to `target_dtype` (`float`, `integer`, `string`, `boolean`).
- `Direct` type: cast to `source_dtype`, evaluate the expression with only `+ - * /`,
  unary minus, constants and the name `x` (AST walker, `eval()` is never used), cast to `target_dtype`.
- `Categorical` type: `instructions` is a Python dict literal (`ast.literal_eval`);
  lookup by `str(value)`; a value not in the dict becomes empty.
- Any per-cell error becomes an empty cell and is counted.
- Output also includes a validation report (successes and errors per variable).

The script must give the **same answers** as the app on the same input. That is the
main success test (section 5, test P1).

## 3. Scope

### In scope
1. A new backend endpoint that returns a ready-to-run script for one study (or all
   studies the user selects), built from the stored mappings.
2. The generated script: standalone, runs with Python 3 and a minimal set of libraries,
   takes `--input` and `--output`, handles files too big for memory (reads in chunks),
   prints a short success/error summary like the in-app validation report.
3. A "Download script" control on the Download Results page.
4. A results report written after every run (see D8): what converted, what errored, every unseen lookup value with counts.
5. Separator and encoding guessing with `--sep` and `--encoding` overrides (see D9).
6. Tests, including the parity test against the in-app engine.
7. Documentation: README section, `docs/script-export.md`, CHANGELOG entry, ACCESS.md rows.

### Out of scope (do not build)
- Transformation-syntax help text or hints in the Map Studies screen (separate, after testing starts).
- Separate PDF slots, any change to the upload pages.
- R, SAS, Stata or other languages. Python only.
- Any new transformation operators (no `%`, `**`, functions, conditionals), and the rule types listed as later work: dates, "treat 999 as empty" codes, combining columns, a dry-run mode.
- Running the script from inside the app, or uploading full data to the app.
- Any change to the testing line (`eval/instrumentation-build`). The owner decides later
  whether to copy this over, with `git cherry-pick -x`.
- Pushing to `main`, or touching `main` at all.

## 4. Tasks

Work in this order. Commit after each task. Run the checks in section 6 before each commit.

### Phase 0: orient (no code)
- T0.1 Read `transform_engine.py`, `transformation_utils.py`, `routers/download.py`,
  `src/routes/download-results.tsx`, `src/api/client.ts`, `ACCESS.md`, `SECURITY.md`.
- T0.2 Run the app's existing tests; record the baseline pass count in `NOTES.md`
  (create it in this folder; keep it as your running log).
- T0.3 Open `DECISIONS.md`. **If D1 to D5 do not have an owner answer, stop and report.**
  Do not pick for the owner. The recommended option is only a suggestion.

### Phase 1: safety net first
- T1.1 Write the parity test harness (test P1 below) against the **existing** engine so it
  runs and passes with a stub generator. It should fail until the generator exists.
- T1.2 Create a small fixture study in the test folder: a mapping set that uses every
  case in section 2 (direct, categorical, no-instruction, missing column, duplicate target,
  empty cells, bad values).

### Phase 2: the generator
- T2.1 New module `backend/core/script_export.py`: builds the script text from a study's
  mappings. Keep it separate from `transform_engine.py` (do not refactor the engine in
  this task; see D3).
- T2.2 **Never paste user text into script source.** Study names, variable names and
  transformation instructions are user-controlled. Put them in a JSON data block that the
  script loads at run time, and have the script parse expressions with the same AST
  whitelist. No `eval`, no `exec`, no f-string building of code from mappings.
- T2.3 The script: argument parsing (`--input`, `--output`, optional `--report`), chunked
  read, same cast and convert rules as section 2, same duplicate/missing handling, clear
  exit codes (0 ok, 2 bad arguments or unreadable file, 1 if the output could not be written).
- T2.4 The results report from D8: printed summary on screen, plus `<output>_report.txt` and
  `<output>_report.json` next to the output. Keep the in-app `validation_report.txt` wording for the
  overlapping lines. Unseen lookup values are counted per value (cap the list at the 50 most frequent
  per variable and say how many more there were). Put a warning at the top that the report can
  contain participant values.
- T2.5 Separator and encoding detection (D9): try UTF-8 (with BOM), then fall back to latin-1
  with a printed notice; detect the separator from the first lines (comma, semicolon, tab, pipe);
  `--sep` and `--encoding` override. Stop with a clear message if the result is one column or garbled.

### Phase 3: endpoint
- T3.1 New route in `backend/routers/download.py`: returns the script as a file download.
  Study names go through `sanitise_study_name`. Errors use `core.errors.server_error`
  (no raw error text to the browser). A study with no "Successfully mapped" rows returns
  a clear 422, like `/transformed-data`.
- T3.2 Update `ACCESS.md`: add the route to the grid and rules (the script contains the
  researcher's mappings but no participant data; classify it under `mappings` or `exports`
  and say which). `tests/test_every_route_has_rules` must pass.
- T3.3 Add an access test like the existing ones: a foreign Origin gets 403, a foreign Host gets 403.

### Phase 4: frontend
- T4.1 Add the API client function in `src/api/client.ts`.
- T4.2 Add a "Download script" button to `src/routes/download-results.tsx` beside the
  existing downloads, with a one-line explanation in plain words and one example command.
  Follow the existing page's styling; no new components unless needed.
- T4.3 Run the dev server on `127.0.0.1` and check it in a browser (Chrome extension if
  connected). Capture a screenshot.

### Phase 5: docs and wrap-up
- T5.1 `docs/script-export.md`: what it is, requirements, one worked example with the
  `example_data/CH_SIB` files, what the output looks like, how errors show up.
- T5.2 README link, CHANGELOG entry (under unreleased), `ACCESS.md` already done.
- T5.3 Final self-review of the diff (see `DEVIN_PROMPT.md` for the report format).

## 5. Tests that must exist

- **P1 parity:** for the fixture study and for `example_data/CH_SIB`, run the in-app engine
  and run the generated script (as a separate process, `python -I script.py ...`) on the
  same input. The two output CSVs must match cell for cell. Also compare success/error counts.
- **P2 malicious input:** a variable name, study name or instruction containing quotes,
  newlines, `__import__('os').system('echo hi')`, `"""`, and a very long string. The
  script must still be valid, must not run the injected text, and must report the bad
  instruction as an error for that variable.
- **P3 big file:** a generated CSV of at least 200,000 rows runs in chunks without loading
  everything at once (assert on the chunk setting, and that memory use stays flat enough
  to finish; do not make the test slow, under 30 seconds).
- **P4 edge cases:** empty file, header only, missing source column, output path not writable
  (exit code 1), semicolon-separated file, tab-separated file, latin-1 file with accents,
  UTF-8 file with a BOM, a wrong guess recovered with `--sep` or `--encoding`.
- **P7 report:** a file with values the lookup never saw (`X` 42 times, `Y` once) produces a
  report listing both with the right counts; empty output cells match the report's empty count;
  a variable skipped for a missing column appears in the report; the JSON and text reports agree.
- **P5 endpoint:** 200 with a script body; 422 for no mappings; 400 for a bad study name;
  403 for foreign Origin or Host.
- **P6 frontend:** type-check and production build pass.

## 6. Checks before every commit

Backend tests: `python -m pytest -q` from the repo root. Frontend:
`npx tsc --noEmit` and `npm run build`. Lint: `ruff check --fix` if the project uses it.
The pre-commit hook must be installed (`python -m pre_commit install`, a separate command
from the commit); the secrets scan runs on commit.

## 7. Risks to watch

| Risk | Why it matters | Mitigation |
|---|---|---|
| Code injection through mappings | variable names and instructions come from user files and the AI | T2.2 and test P2 |
| Script and app drift apart | someone edits the engine and forgets the script | test P1 runs on every test run; D3 decides whether code is shared |
| Pandas version differences on the researcher's machine | cast and CSV reading can differ | D2 decides the dependency; pin a minimum version in the script header |
| Huge files | researchers have full datasets | chunked reading, test P3 |
| Researcher expects it to transform categories the AI never saw | silent empty cells | the report lists every value that mapped to empty, per variable |
| Leaking participant data | the script is generated by the app | the script holds only mappings, never data; assert this in a test |

## 8. Effort

About one to two days of work for one developer. The generator and parity test are the bulk.
