# Prompt for Devin

Copy everything below the line into Devin.

---

You are building one feature for the Metadata Harmonisation Tool (FastAPI backend, React frontend, SQLite). The owner is not a trained front-end or infrastructure developer, so explain choices in plain language and say why.

## Where you work
- Folder: `C:\Users\ic\OneDrive\Desktop\instruction-follower\.claude\worktrees\feature-script-export`
- Branch: `feature/script-export` (already created from `origin/development`). Stay on it.
- Work only inside that folder. Do not touch other worktrees or branches.

## The feature
This is a deliberately rough first version. The point is to prove the whole path works end to end so the owner can poke holes in it later. Do not add features beyond the plan; do make what is there correct and tested.

Let a researcher download a small Python script from the Download Results page. They run it on their own machine against their own full dataset, and it applies the study's confirmed mappings and transformations, producing the same output the app produces for the sample data. The full data never goes through the app.

## Read first, in this order
1. `docs/plans/script-export/PLAN.md` (scope, tasks, tests, risks). This is your spec.
2. `docs/plans/script-export/DECISIONS.md` (owner decisions D1 to D9). Pay special attention to D8: the results report is the heart of this version.
3. `backend/core/transform_engine.py` and `backend/core/transformation_utils.py` (the behaviour to copy exactly).
4. `ACCESS.md` and `SECURITY.md`.

## Hard rules
1. **Decisions.** D1 to D9 are answered in `DECISIONS.md`; where the owner wrote "recommended", use the option marked Recommended. Do not change an answer. If you hit a new choice the plan does not cover, write it in `NOTES.md` with the options and your reasoning, pick the smallest and most reversible one so work can continue, and flag it clearly in your final report so the owner can overrule it.
2. **Scope.** Build only what `PLAN.md` lists under "In scope". Anything in "Out of scope" stays out. If you think scope should change, say so in your report and do not do it.
3. **No code injection.** Study names, variable names and transformation instructions are user-controlled. Never paste them into script source text. Store them as JSON data and parse expressions with the same restricted AST evaluator. No `eval`, no `exec`. Test P2 in the plan proves this.
4. **Branches.** Commit locally. Do not push. Do not open a pull request. Do not merge. Never touch `main`, `staging`, or `eval/instrumentation-build`. The owner decides about those.
5. **Do not refactor the existing engine** unless D3 says option B, and then say so up front.
6. **Secrets and data.** Never put real credentials, API keys, or participant data in code, tests, or logs. Test data is `example_data/` or small data you generate.
7. **Commits.** Small commits, one per task. Plain commit messages with no filler words and no em dashes. The pre-commit hook must be installed first: run `python -m pre_commit install` as its own command, then commit separately.
8. **Dev servers** listen on `127.0.0.1` only. Stop any server you start when done. Delete scratch scripts you created.
9. **Do not change the access rules loosely.** The new route gets rows in `ACCESS.md` and a test (the existing `test_every_route_has_rules` fails until you do).

## How to work
- Follow the phases in `PLAN.md` in order. Build the safety net (parity test, fixture) before the generator.
- After every task run: `python -m pytest -q`, `npx tsc --noEmit`, and (when the frontend changed) `npm run build`.
- Keep a running log in `docs/plans/script-export/NOTES.md`: baseline test count, what you did, what surprised you, what you could not do.
- For the frontend button, run the dev server on `127.0.0.1`, use it in a browser, and keep a screenshot.
- Prove behaviour with output, not statements: paste the passing test summary and one real run of the generated script on `example_data/CH_SIB` with the app's own output beside it.

## What to hand back (final report, plain language)
1. What you built, in five lines.
2. Test results: the pass counts before and after, and the parity test result.
3. Anything that differs between the script and the app, even slightly, with an example.
4. Anything you could not finish or were unsure about.
5. The exact commit list (`git log --oneline origin/development..HEAD`).
6. Any change you made outside the files the plan lists, and why.

When finished, do not push. Say you are done and wait for the owner or the reviewing assistant to assess the branch.
