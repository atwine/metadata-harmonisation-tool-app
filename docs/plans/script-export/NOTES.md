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
(filled in as work proceeds)
