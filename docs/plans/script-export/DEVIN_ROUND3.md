# Round 3 for Devin: three small gaps left after the re-check

Branch `feature/script-export`, folder `.claude/worktrees/feature-script-export`. Same rules as before: commit locally, no push,
no PR, never touch `main`, `staging` or `eval/instrumentation-build`, one commit per item, a test that fails first and passes after,
a running log in `NOTES.md`. These are all small. Keep the changes small too.

The independent re-check of round 2 passed everything else, so do not change other behaviour.

## 1. When no column looks similar, show what the script saw

If every mapped column is missing and none has a close match (for example the file has `smoking` and `wght` where the rules expect
`sbsmk` and `wt`), the message says only that none of the mapped columns were found. The user cannot tell what the script read.

Fix: in that case, list the columns the script found (the first 30, then "and N more") in the console message, the text report and the
JSON report (a `columns_found` list). Say which separator and encoding were used, since a wrong guess is the usual cause. Keep the
"did you mean" lines when there are close matches. Tests: a file with unrelated column names; a file with 100 columns (list is capped);
a semicolon file read with the wrong `--sep` (the list shows one long column, which makes the cause obvious).

## 2. `--encoding utf-16` on a UTF-16 file without a byte-order mark ends in a traceback

You found this in round 2 and left it. A user who follows our own advice ("Try --encoding utf-16") hits a Python traceback.

Fix: catch the decoding failure and exit 2 with a clear message: `The file could not be read as utf-16 (it has no byte-order mark).
Try --encoding utf-16-le or --encoding utf-16-be.` (and the same idea for utf-32). Also change the garbled-text message so it
suggests `utf-16-le` and `utf-16-be`, not bare `utf-16`. Tests: UTF-16 without a mark with `--encoding utf-16`, with `utf-16-le`
(works), and the garbled-text message wording.

## 3. A short safety net for anything unexpected, plus one line of documentation

- Wrap `main()` so an unexpected error prints one plain line (`Something unexpected went wrong (<ErrorType>). Nothing was written.
  Re-run with --debug and send us the details.`), exits 1, and leaves no temporary files. Add a `--debug` flag that prints the
  full traceback instead. Do not hide the traceback by default for expected errors that already have clear messages. Test: force an
  unexpected error inside the run (for example a monkeypatched function that raises `RuntimeError`) and check the message, the exit
  code, that no files are left, and that `--debug` shows the traceback.
- In `docs/script-export.md`, add one line: a run that is force-closed (closing the window, killing the process, power loss) can leave
  a file named `.tmp_<random>.part` next to the output. It is safe to delete.

## What to hand back

The same report as before, with a row per item: the test that proves it and the result of re-running its recipe. Then wait.
