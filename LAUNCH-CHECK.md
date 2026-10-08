# Launch check: Metadata Harmonisation Tool

Run 2026-10-07 on branch `access-audit` (`e129933`), with the `launch-check` skill.
**No owner was available for this run.** Every item below is backed by evidence
(a command and its output, or a file) gathered without asking anyone anything —
anything that needed a person's answer is recorded as an **owner** item instead
of guessed at, and the questions that would have been asked are listed at the
bottom. No app code was changed to produce this report.

## Launch profile

- **What it is**: a researcher's tool for mapping study dataset variables onto a
  canonical codebook, built for the eLwazi Open Data Science Platform. AI model
  generates descriptions/embeddings; a human reviews and approves each mapping.
- **Where it runs**: per the README and `docs/docker.md`, every documented path is
  **local-only** — one researcher runs one copy on their own computer (Docker
  Compose at `localhost:8080`/`:8000`, or a manual Python+Node install). I found
  no live/hosted URL anywhere in the repo. There is unused scaffolding for a
  Cloudflare Workers deployment (`wrangler.jsonc`, `@cloudflare/vite-plugin` in
  `package.json`, and a stale rebuild spec at `docs/harmonisation_spec.md` that
  still says the backend is "NOT YET BUILT") — I could not tell from the code
  alone whether that path is actually used anywhere today. See owner question 1.
- **Who uses it**: a single researcher/operator per installation. No user
  accounts, no login — by design (`ACCESS.md`).
- **Payments**: none in the app.
- **Sensitive data**: yes. Uploaded study CSVs can carry real participant-level
  rows, and the exported mapping/transformed-data files carry the same. Classed
  "sensitive: health" in `ACCESS.md`.
- **Distribution**: public GitHub repo (`atwine/metadata-harmonisation-tool-app`),
  MIT-licensed per the README (no separate `LICENSE` file was found in this
  checkout).

## Checklist

### A. Data and access

| # | Item | Status | Evidence / next step |
|---|---|---|---|
| 1 | Access rules | **missing** | `ACCESS.md` and `tests/test_access.py` exist (added in the last commit, `e129933`). Ran `pytest tests/test_access.py`: **36 failed, 55 passed.** The failures are exactly the three critical gaps `ACCESS-AUDIT.md` already names and has *not yet fixed*: the API still binds `0.0.0.0` (both compose files and `run_backend.py`), there is still no `Origin` check on state-changing routes, and there is still no `Host`-header check, so DNS rebinding still works. Next step: apply the three fixes `ACCESS-AUDIT.md` already proposes, then re-run the tests. |
| 2 | Scanners (secrets/deps/code) run on every push, latest run green | **missing** | `.github/workflows/security-scans.yml` and `.pre-commit-config.yaml` exist but are **untracked** (`git status`: `??`) — never committed, never run. Also, `git remote -v` shows `origin` pointing at a local worktree path, not GitHub, and `gh run list` fails ("none of the git remotes... point to a known GitHub host"), so there is no CI history to check even once these are committed. Next step: commit both files, push to the real GitHub remote (`atwine/metadata-harmonisation-tool-app`), and confirm the first run is green. |
| 3 | `/security-review` run on shipped code, findings fixed/accepted | **missing** | Not run in this pass (out of scope for `launch-check` itself; the skill says to run it as a separate step). `ACCESS-AUDIT.md`'s "other observations" already flag two things worth a security review beyond access control: `GET /api/ai-config/models` takes the vLLM API key as a URL query parameter (`?api_key=`, ends up in logs/history), and the same endpoint plus `POST /api/ai-config/test` will connect to any `base_url` they're given (SSRF-shaped, mitigated once F1/F3 above are fixed). Next step: run `/security-review` on this branch. |
| 4 | Secrets live outside code; dev secrets differ from prod; any committed secret rotated | **done**, with one gap | Searched `git log --all -p` for key/token/password-shaped literals: none found. `.env.local` is covered by the `*.local` rule in `.gitignore`. **Gap**: `docs/docker.md` tells users to put `GITHUB_TOKEN` in "a `.env` file next to `docker-compose.yml`" — a bare `.env` at the repo root is **not** matched by any rule in `.gitignore` (only `*.local` and `.dev.vars` are). It would currently survive a `git add .`. Next step: add a plain `.env` line to `.gitignore`. |
| 5 | Pen test for health/financial/children/ID data, or owner accepts the risk | **owner** | The app handles participant-level health data (see Launch profile). No pen test evidence found. Owner must decide whether to commission one or accept the risk for this release — see owner questions. |

### B. Running in public

| # | Item | Status | Evidence / next step |
|---|---|---|---|
| 6 | HTTPS-only (live URL redirects http→https) | **n/a** | No live/hosted URL exists for this app (see Launch profile) — everything runs on a researcher's own `localhost`. Revisit if owner question 1 turns up a real hosted deployment. |
| 7 | Security headers on the live site | **n/a** | Same reason as #6. |
| 8 | Login: maintained library, reset expires, sessions expire, admin 2FA | **n/a** | The app has no user accounts or login by design — one researcher, one machine (`ACCESS.md` §2). This is a deliberate design choice, not an oversight, but it's exactly what makes items A1 (origin/Host checks) load-bearing instead. |
| 9 | Rate limits on login/signup/reset/paid-AI endpoints | **n/a**, with a caveat | No login/signup/paid endpoints exist. The one place a request budget matters — the app's own calls *out* to a configured AI provider — already throttles itself (`backend/core/ai_provider.py`, 60 requests/60s). There is **no** rate limit on the FastAPI endpoints themselves; this only becomes a real exposure if the API is ever bound beyond `127.0.0.1` (tracked by A1/F1). |
| 10 | Production shows generic errors, debug off | **missing**, minor | No Flask/FastAPI debug mode and no `--reload` in the packaged Docker image (`backend/Dockerfile` CMD has no `--reload`; confirmed only `run_backend.py`, the dev entry point, uses it). However several routes do `raise HTTPException(500, f"...: {e}")` (e.g. `backend/routers/codebook.py:93`, `backend/routers/download.py:66`), which echoes the raw Python exception text to the caller. Severity is lower than usual here since the only "caller" is meant to be the researcher themselves, but it's still worth tightening if network exposure (A1) is ever turned on. Next step: return a generic message and log the exception server-side instead. |

### C. When things go wrong

| # | Item | Status | Evidence / next step |
|---|---|---|---|
| 11 | Backups exist and a restore has been tried in the last 3 months | **missing** | There is no automated backup. `docs/docker.md` documents the data folder (`./harmonisation-data/`) and says to "back it up by copying it" — that's a manual step the researcher has to remember to do themselves, and no restore of a copy has been demonstrated. Next step: owner decides whether this is acceptable for a single-researcher, locally-run tool, or whether a documented/scripted backup step belongs in the Docker Compose walkthrough. |
| 12 | Errors/downtime reach a person within minutes | **n/a** | No hosted service exists to monitor. In the local-only model, the researcher is already looking at the terminal/browser when something breaks, so a separate alerting pipeline doesn't obviously apply. Revisit if owner question 1 surfaces a hosted deployment. |
| 13 | Logs carry no personal data | **done** | Searched all application-level `logger.*`/`logging.*` calls in `backend/`: every one of them is in `afpo_lookup.py`/`afpo_github_check.py` and logs ontology-sync status only (versions, counts, network errors) — never study, variable, or participant content. There is no other application logging. (Caveat: uvicorn's own default access log will show request *paths*, which can include a study name the researcher chose — not participant data itself.) |
| 14 | Someone is notified about library holes weekly, and knows who updates | **missing** | Same root cause as A2: the weekly-cron scanner workflow exists on disk but isn't committed or pushed, so it has never run and nobody is being notified yet. |
| 15 | One-page incident plan (who decides, how to revoke keys/sessions, how to take the app offline, how/when users and regulators are told) | **missing** | No `SECURITY.md` or incident-plan file found. The README notes the no-auth gap is tracked as "issue #4" but that's a code-gap tracker, not an incident plan. Next step: owner writes or commissions a one-pager; for a single-researcher local tool this can be short, but "how and when affected study participants/data owners are told" still needs a real answer given the data involved. |

### D. Money and law (owner items)

| # | Item | Status | Evidence / next step |
|---|---|---|---|
| 16 | Payments: hosted checkout, verified webhooks, server-side prices | **n/a** | The app takes no payments. |
| 17 | Privacy policy and terms, matching what's actually collected | **owner** | None found in the repo. The app can be configured to send variable names and PDF-context text to a third-party AI API (OpenAI, Anthropic, Azure OpenAI) — see `backend/core/descriptions.py`'s `build_prompt` — rather than only the local Ollama model. Whether that needs a published policy, and what it should say, is an owner call. |
| 18 | Consent and data-rights (export/delete on request) | **owner** | No consent flow exists; not obviously meaningful for a tool with no accounts, but the underlying *study* data this tool processes may carry its own consent/ethics-approval obligations from the original cohorts. Owner call. |
| 19 | Data location, cross-border transfer, data-processing agreements (incl. AI APIs) | **owner** | `ACCESS.md` §6 already raises this (which data-protection laws/agreements apply — Uganda/Kenya Data Protection Acts, POPIA, GDPR for European cohorts) and leaves it to the owner with legal/ethics-office input. Also flagging concretely: if an operator points the AI Configuration at OpenAI/Anthropic/Azure instead of local Ollama, variable names and PDF-context text leave the researcher's machine to that provider — whether that's permitted under the source studies' data agreements is a legal call, not a code one. |
| 20 | Retention: how long each kind of data is kept, what deletes it | **owner** | `ACCESS.md` §6 already asks whether participant-level data in `input/`/`results/` needs disk encryption or deletion after harmonisation — unanswered. Today the only deletion paths are the manual "delete study" and "Clear Workspace" actions; there's no retention schedule or automatic expiry. |

## Missing items, in order (data/money exposure first)

1. **A1 — Access rules fail their own proving tests.** `pytest tests/test_access.py` is 36/91 red right now: the API still listens on every network interface, still has no `Origin` check, and still has no `Host`-header check, so any device on the same network, any website open in the researcher's browser, and any DNS-rebinding site can reach participant data today. `ACCESS-AUDIT.md` already has the three fixes written up — they just haven't been applied.
2. **A2 / C14 — Scanners were installed but never turned on.** `.github/workflows/security-scans.yml` and `.pre-commit-config.yaml` are sitting uncommitted, and `origin` isn't even a GitHub remote, so there's no CI to go green yet.
3. **D-adjacent / A4 — `.gitignore` doesn't cover a bare `.env`,** even though `docs/docker.md` tells users to create exactly that file for `GITHUB_TOKEN`.
4. **C11 — No tested backup/restore** for `harmonisation-data/`, only a "copy the folder yourself" instruction.
5. **C15 — No incident plan** for this data-handling tool.
6. **A3 — `/security-review` hasn't been run** on this branch; two leads already exist (API key in a URL query string, SSRF-shaped `base_url` trust) for it to dig into.
7. **B10 — A handful of 500 responses echo raw exception text** back to the caller; low severity given the single-local-user model, but easy to tighten.

Given A1 alone — the proving tests for the one thing this app explicitly promises ("only the researcher on their own computer can reach this data") are currently failing — **this is not launch-ready as-is.**

## Owner items

- **A5.** Commission a penetration test for this participant-level health data, or formally accept launching without one.
- **D17.** Decide on a privacy policy / terms, and whether use of a cloud AI provider (vs. local Ollama) needs disclosure in it.
- **D18.** Decide what "export/delete my data on request" means here, given there are no user accounts — likely maps to the *source study's* data-subject rights, not this tool's.
- **D19.** Which data-protection laws and data-sharing/ethics agreements govern the studies loaded into this tool (Uganda/Kenya Data Protection Acts, POPIA, GDPR, others), and whether those agreements permit sending variable names/context text to a third-party AI API.
- **D20.** A retention policy: how long participant-level data stays in `input/`/`results/`, and whether disk encryption is required by any study's ethics approval.
- **ACCESS.md open question.** Should opening the API to a network (`MHT_BIND_ADDRESS=0.0.0.0`) require a shared access token, once that setting exists, rather than being all-or-nothing?

## Questions I would have asked

Since no owner was reachable for this run, here is exactly what I would have asked them, instead of guessing:

1. **Is this tool ever deployed anywhere other than a researcher's own laptop?** The repo has unused-looking Cloudflare Workers deployment scaffolding (`wrangler.jsonc`, a Cloudflare Vite plugin) and a stale rebuild spec that describes a different, half-built architecture. If there's a real hosted instance somewhere, the whole "B. Running in public" section (HTTPS, headers, rate limits) needs to be re-scored against it instead of marked n/a.
2. **Who are the actual end users right now** — is it still just you, or have other researchers/institutions already started running their own copies? That changes how urgent A1 (the failing access tests) really is.
3. **For the studies currently loaded or expected**, do the original data-sharing/ethics agreements say anything about: disk encryption, deletion deadlines after harmonisation, or which countries the data may pass through (including to a cloud AI API)?
4. **Are you comfortable with variable names and PDF-context text leaving the machine** when someone configures OpenAI/Anthropic/Azure instead of local Ollama — and should that be louder in the UI than the current AI Configuration panel, given it's opt-in per provider but not obviously flagged as "this leaves your machine"?
5. **Do you want `MHT_BIND_ADDRESS=0.0.0.0` (network mode) to require a shared token** before it's usable, now that there's a documented use case (lab LAN) for turning it on at all?
6. **Is a penetration test in budget/scope for this release**, given the data is health-related, or should launch proceed on the access-audit + automated-scanner evidence alone?
7. **Who is the "person" backups and incident response should name** — is it just you, or is there a technical contact at eLwazi/the hosting institution who should also be listed?
8. **Should the GitHub repo move to a real GitHub remote before launch** — right now `origin` points at a local worktree path, which is why the CI scanners can't actually run yet.

## Note added after the run

This check ran on a scratch clone, so item A2 and question 8 are side
effects of the test setup: the real repository's `origin` is
`https://github.com/atwine/metadata-harmonisation-tool-app.git`. The scanner
files it found untracked are the `security-scans` templates, added to the
clone for testing and not committed to this repository.
