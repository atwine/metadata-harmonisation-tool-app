# Security evaluation: brief for the agent fixing it

A security evaluation of the Metadata Harmonisation Tool ran on 2026-10-07
against `main` at `c298838`. The owner chose to fix it later, so this folder
holds the results and everything needed to act on them. Read this file
first, then `SECURITY-EVALUATION.md`.

| File | What it is |
|---|---|
| `SECURITY-EVALUATION.md` | The full report in plain language: access findings, library holes, smaller issues |
| `ACCESS-AUDIT.md` | The three access findings, each with cause, fix and the tests that prove it |
| `ACCESS.md` | The access rules, to live at the repo root |
| `test_access.py` | 91 tests proving the rules; 36 failed on `main` |
| `access-audit-before.txt` | Test output before any fix |
| `LAUNCH-CHECK.md` | The 20-item launch-readiness check and owner questions |

## The rule being enforced

The tool has no logins. One researcher runs it on their own computer, so
only that computer may reach the API. Other devices on the network, other
websites open in the browser, and DNS-rebinding sites get nothing. Opening
the API to a trusted network is an opt-in setting, never the default.
`ACCESS.md` explains how each kind of caller is kept out.

## Before you start

1. Work in a new worktree off `development`, per the owner's global
   workflow: review the diff (`code-review` and `/security-review`), ask the
   owner before pushing to `staging`, and open a PR from `staging` to `main`
   that waits for the owner's go-ahead.
2. This folder is untracked in the main checkout
   (`C:\Users\ic\OneDrive\Desktop\instruction-follower\evaluation-report`),
   so a new worktree won't contain it. Copy the files from there, then put
   them in place:
   - `ACCESS.md` to the repo root
   - `test_access.py` to `tests/test_access.py`
3. Run `python -m pytest tests/test_access.py -q`. On `main`, 36 failed (see
   `access-audit-before.txt`). `development` may differ; record what fails
   there before changing anything. That run is your "before" evidence. The
   two Docker Compose tests need the `docker` command (not the running
   engine) and skip without it.

The owner's Claude Code setup has a hook that refuses new API routes or data
models in a project with no `ACCESS.md` at the root. Step 2 satisfies it.

## Work order

Fix one finding at a time, rerun `tests/test_access.py` after each, and
commit each separately. Never change a test's expectation to make it pass
without the owner's yes.

**1. F1, network exposure.**
- `docker-compose.yml` and `docker-compose.hub.yml`: publish ports as
  `"${MHT_BIND_ADDRESS:-127.0.0.1}:8000:8000"` and the same for `8080`.
- `run_backend.py`: `host=os.environ.get("MHT_BIND_ADDRESS", "127.0.0.1")`.
- Leave `backend/Dockerfile`'s `--host 0.0.0.0`; inside the container that's
  required for Docker's port mapping, and the compose change controls who
  reaches it.
- Document `MHT_BIND_ADDRESS` in `README.md` and `docs/docker.md` with the
  warning that network mode gives everyone on that network full access.
- Tests: `test_run_backend_listens_on_localhost_by_default`,
  `test_compose_publishes_on_localhost_by_default[...]`.

**2. F2, other websites triggering changes.** Add a middleware in
`backend/main.py` that refuses POST, PUT and DELETE with 403 when an
`Origin` header is present and isn't one of the tool's own local origins
(the same list the CORS middleware allows). Requests with no `Origin` (curl,
scripts) pass. Tests: the three `website POST ...` cases and
`test_website_cannot_wipe_the_workspace`.

**3. F3, DNS rebinding.** Add a middleware that refuses, with 403, any
request whose `Host` isn't `localhost` or `127.0.0.1` (any port), extendable
through an `MHT_ALLOWED_HOSTS` setting for network mode. Write it as a small
custom middleware: Starlette's `TrustedHostMiddleware` answers 400, which
the tests don't count as a refusal. Tests: the 28 `rebinding ...` cases and
`test_rebinding_site_cannot_read_studies`.

After 2 and 3, check by hand that the app still works: `docker compose up`,
open `http://localhost:8080`, upload a codebook and a study, run Initialise,
map a variable, download results.

**4. Smaller items** (details in `SECURITY-EVALUATION.md`):
- add `.env` to `.gitignore`;
- replace the raw exception text in `backend/routers/codebook.py:93` and
  `backend/routers/download.py:66` with a generic message, logging the
  detail server-side;
- move the vLLM API key out of the `?api_key=` query string on
  `GET /api/ai-config/models`, updating `src/api/client.ts` to match;
- run `npm audit fix` (non-breaking) in the repo root, then `npm run build`
  and click through every page.

## Decisions that belong to the owner

Ask; don't decide:

- Whether network mode should also require a shared access token.
- The 4 remaining npm problems in Cloudflare's tooling, whose fix is a
  breaking downgrade, and whether the Cloudflare deployment scaffolding
  (`wrangler.jsonc`) is used at all.
- The questions in `ACCESS.md` section 6 and `LAUNCH-CHECK.md`: data
  agreements and retention for participant data, disk encryption, sending
  study text to cloud AI providers, backups and an incident plan.

## When it's done

- All of `tests/test_access.py` passes, with the before and after output in
  the PR description.
- The hand check above works.
- From a second device on the same network, `http://<laptop-ip>:8000` no
  longer connects.
- Run the `launch-check` skill to update `LAUNCH-CHECK.md`, and consider the
  `security-scans` skill so secrets and library holes are caught on every
  push.
