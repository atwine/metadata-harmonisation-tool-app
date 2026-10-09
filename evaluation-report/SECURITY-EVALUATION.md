# Metadata Harmonisation Tool security evaluation

Evaluated 2026-10-07 on `main` (c298838). No app code was changed. The owner
chose "report only" at the time, so this folder records the findings to act
on later.

## The short version

The tool is meant for one researcher on their own computer, and its file
handling is careful: study names are cleaned so no request can reach files
outside the app's folders. But the default setup lets far more than that
researcher reach the API, which has no login and holds real participant-level
study data.

| Area | Result |
|---|---|
| Access rules (who can reach the API) | 3 findings, all critical |
| Secrets in code and history | clean (78 commits, gitleaks) |
| Python libraries | clean (pip-audit) |
| JavaScript libraries | 22 problems (1 critical, 16 high); a non-breaking update leaves 4 |
| Code-level review | 4 smaller issues |
| Launch readiness | not ready: the access tests fail (details in `LAUNCH-CHECK.md`) |

## Access findings

Full detail, causes and fixes are in [`ACCESS-AUDIT.md`](ACCESS-AUDIT.md);
the rules are in [`ACCESS.md`](ACCESS.md). The proof is
[`test_access.py`](test_access.py): 36 of 91 cases fail on `main` (see
[`access-audit-before.txt`](access-audit-before.txt)).

1. **F1, critical: anyone on the same network can use the API.**
   `docker-compose.yml` and `docker-compose.hub.yml` publish `"8000:8000"`,
   which Docker binds on every network, and `run_backend.py` runs uvicorn on
   `0.0.0.0`. On café, conference or university Wi-Fi, anyone can download
   the transformed participant dataset and delete studies. The README warns
   against this, but the default does it.
2. **F2, critical: any website the researcher visits can wipe the workspace,
   overwrite the codebook or plant studies.** `POST
   /api/initialise/clear-workspace` needs no body, and the two upload routes
   accept ordinary HTML forms, so a hidden form on any page can trigger them.
3. **F3, critical: DNS rebinding lets a website read every reply.** The API
   doesn't check the `Host` header, so a malicious site can make the browser
   treat `localhost:8000` as its own and read study data.

Already safe: routes that take JSON can't be triggered by other websites,
and PUT and DELETE are blocked by the CORS allow-list.

## Library holes

`npm audit` (production dependencies): 22 problems, 1 critical (`seroval`,
through TanStack Start) and 16 high. In a test copy, `npm audit fix`
(non-breaking) cleared all but 4 high ones, which all come from Cloudflare's
build and deploy tooling (`wrangler`, `miniflare`, `sharp`,
`@cloudflare/vite-plugin`); their suggested fix is a breaking downgrade, an
owner decision. The non-breaking fix wasn't applied to the repo and needs a
build and click-through check when it is.

Python (`backend/requirements.txt`): no known holes.

## Code-level observations

- **`.env` isn't gitignored.** `docs/docker.md` tells users to put
  `GITHUB_TOKEN` in a `.env` file next to `docker-compose.yml`, but
  `.gitignore` only covers `*.local` and `.dev.vars`, so `git add .` would
  commit it.
- **Raw error text in two 500 responses.** `backend/routers/codebook.py:93`
  and `backend/routers/download.py:66` return the Python exception message
  to the caller.
- **An API key in a URL.** `GET /api/ai-config/models` takes the vLLM key as
  `?api_key=`, so it can land in logs and browser history. Send it in a
  header or POST body.
- **Requests to any address.** `/api/ai-config/models` and
  `/api/ai-config/test` connect to whatever `base_url` they receive. Once F1
  and F3 are fixed only the researcher can call them, which removes most of
  the risk.

## Launch readiness

`LAUNCH-CHECK.md` holds the full 20-item check. It marks the tool not ready
for users because the access tests fail, and lists owner questions on
backups, an incident plan, data agreements for the studies, whether study
text may go to cloud AI providers, and retention. Its item A2 and question 8
came from the scratch copy it ran on; a note at its end explains.
