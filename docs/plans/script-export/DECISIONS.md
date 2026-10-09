# Decisions for the owner

These are the owner's calls. Devin does not choose. Fill in the **Answer** line, or write
"recommended" to accept the suggestion. D1 to D9 are answered as of 2026-10-08, so Phase 1 onward can start.

## D1. What does the researcher download?
- A. One `.py` file with the mappings embedded as a JSON block. One file to move around. *(Recommended)*
- B. A `.py` file plus a separate `mappings.json`. The mappings can be edited by hand, but two files can get out of sync.
- C. A ZIP holding the script, mappings and a short README.

Answer: recommended (owner, 2026-10-08)

## D2. What must be installed on the researcher's machine?
- A. Python 3 only (standard library `csv` module). Nothing to install, but slower and no pandas-style dtype handling; parity has to be matched by hand.
- B. Python 3 plus pandas. Matches the app's behaviour most easily, but one `pip install`. *(Recommended)*

Answer: recommended (owner, 2026-10-08)

## D3. Share code with the in-app engine, or copy it?
- A. Copy the small conversion helpers into the generated script, leave the engine alone. Lowest risk to the app. Parity test guards drift. *(Recommended)*
- B. Move the helpers into one shared module that both use. No drift, but changes shared code the whole app relies on (needs the blast-radius check).

Answer: recommended (owner, 2026-10-08)

## D4. One script per study, or one for all selected studies?
- A. One script per study, with the study's name in the file name. Matches how the data arrives (one file per study). *(Recommended)*
- B. One script holding all selected studies, picked with `--study`.

Answer: recommended (owner, 2026-10-08)

## D5. What do the script's error messages look like?
- A. Same wording as the app's validation report. *(Recommended)*
- B. New, shorter wording for the command line.

Answer: recommended (owner, 2026-10-08)

## D6. Does this go to the testing build too? (not blocking)
- A. Not yet. Decide after testers have used the app. *(Recommended)*
- B. Yes, copy it over with `git cherry-pick -x` once it is merged to development and staging.

Answer: ______

## D7. How much does version 1 do? (answered 2026-10-08)
Replay only: the script repeats exactly what the app does on sample data (math rules and lookup rules). It is a first, rough version meant to prove the whole path end to end. Holes get poked later. No new rule types (dates, "treat 999 as empty", combining columns) and no dry-run mode in this version.

Answer: replay only (owner, 2026-10-08)

## D8. A lookup rule meets a value it has never seen (answered 2026-10-08)
The cell becomes empty, and the script tells the user clearly. After every run it writes a **results report** so the researcher knows how to deal with strange values. Owner's words: once a value isn't known, "it could just inform the end user about the state of the result", and the report should say "what was transformed, what the errors were, what values were left".

The report must contain, per variable:
- the rule used (math or lookup) and the output column name;
- how many rows converted, how many came out empty, how many were errors;
- for lookup rules, every **unseen value with its row count** (for example `sbsmk: "X" appeared 42 times, not in the rule`);
- for math rules, any cells that could not be converted, with a few example input values (first 5), not all of them.
It also lists variables skipped (source column not found, duplicate target column) and a one-line overall summary printed to the screen.

The report is written next to the output file (for example `out_report.txt`, plus a machine-readable `out_report.json`). Because it names raw cell values, it may hold participant data: the script must say so at the top of the report, and the report is never sent anywhere by the app.

Answer: empty cell plus full report (owner, 2026-10-08)

## D9. Different file shapes (answered 2026-10-08)
The script guesses the separator and text encoding, and the researcher can override them with `--sep` and `--encoding`. If the guess looks wrong (one column only, or garbled text), it stops with a clear message that suggests the flags.

Answer: guess, with flags to override (owner, 2026-10-08)
