# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- **Download a script to transform your full dataset.** The Download Results page has a new "Download script" button for each study. The script (`transform_<study>.py`) applies the study's confirmed mappings and transformations to your own full CSV on your own computer, so the full data never goes through the app. Run `python transform_<study>.py --input my_data.csv --output out.csv` (needs Python and pandas). It reads in chunks, guesses the separator and text encoding (override with `--sep` and `--encoding`), and writes a results report next to the output (`_report.txt` and `_report.json`) listing what was converted, what came out empty, every lookup value the rule had never seen with its row count, and skipped variables. The report may contain participant values, so keep it private. A test requires the script's output to match the app's, cell for cell. New route `GET /api/download/{study}/script` (listed in `ACCESS.md`). See `docs/script-export.md`.

## [0.8.24] — 2026-10-08

### Security
- **Updating the app now tells you to download the compose file again.** The "listen on your own computer only" setting (0.8.12) lives in `docker-compose.hub.yml`, not in the images. Someone who only ran `pull` and `up` kept their old file, which still opens ports 8000 and 8080 to the whole network, even with the newest images. The README's update steps now include re-downloading the file, with a one-line check (`docker compose config` should show `host_ip: 127.0.0.1`). Checked against the real old and new files.
- **Only `main` can publish the public images.** Running the publish workflow by hand from another branch could have tagged that branch's build as `:latest`. It is now refused.

### Fixed
- **Rootless Docker and Podman keep your file ownership.** There, "root" inside the container is you, so the startup script now detects that setup and leaves ownership alone instead of handing your files to a stranger user id.
- **Upgrading from the old root image no longer leaves unwritable files.** After the earlier versions, files created by root could sit inside folders you own. The startup script now hands those over (and only those: files owned by anyone else are left alone), so rewriting a study, deleting a study or Clear Workspace no longer hit "permission denied". Checked with real containers: a fresh start, a restart, and root-owned files inside user-owned folders.
- **A failed restore can no longer leave you without data.** `restore.sh` and `restore.ps1` now unpack the backup into a temporary folder first and only swap it in when that worked. A damaged or truncated archive is refused with your current data untouched. They also refuse archives that hold files outside `harmonisation-data/` (or paths that climb out of it), so a wrong or edited archive cannot overwrite your compose file or scripts. Tested with a good, a foreign, a path-climbing and a truncated archive, in both bash and PowerShell.
- **The backup and restore scripts stop cleanly when Docker fails.** The PowerShell versions now check whether stopping and restarting the backend worked, instead of carrying on, and the bash versions set up the restart before stopping the backend.

## [0.8.23] — 2026-10-08

### Security
- **The backend app no longer runs as root.** The container still starts as root for a moment, only to make the data folders (`harmonisation-data/...`) writable, then hands over to an ordinary user. A folder you already own keeps its owner and the app runs as you, so files stay editable on your computer; a root-owned folder (Docker creates these on Linux) is given to a new user, id 10001. No extra setup for researchers. Checked with real containers in both cases: the app process ran as the expected user and a real upload wrote its files.
- **Raw error text is replaced with fixed messages in more places.** CSV upload failures, Initialise step failures, the AI connection test, the transformation preview and the download step's "could not read data" reason no longer repeat the library's error text, which can hold file paths, URLs, key fragments or participant values. The server log records only the kind of error. AI failures now say the real reason in plain words (server unreachable, key rejected, timed out, model not found).
- **`.env` files and keys can no longer be copied into an image.** `.dockerignore` now excludes `.env`, `.env.*`, `*.pem` and `*.key`.

## [0.8.22] — 2026-10-08

### Fixed
- **Clear Workspace no longer fails in Docker.** In Docker, `input/`, `results/` and `logs/` are folders mounted from your computer, and the old code tried to delete the folder itself, which Docker refuses ("Device or resource busy"). The click returned an error after deleting the files but before clearing the database, so saved mappings stayed behind. It now deletes everything inside each folder and keeps the folder, then clears the database, and the button works as intended. If anything fails, the response is the generic "Something went wrong. Check the server log." message.

## [0.8.21] — 2026-10-08

### Added
- **Incident plan draft (`SECURITY.md`).** One page covering how to report a problem, who decides, the first steps in an incident (take the app offline with `docker compose down`, keep the evidence, make a backup), where each key lives and how to rotate it (AI provider keys, the optional `GITHUB_TOKEN`, the maintainers' `DOCKERHUB_TOKEN`), and how and when data owners and regulators are told. The names, contact details and notification deadlines are deliberately left as clearly marked **[OWNER TO FILL]** blanks; nothing was invented. Also notes that GitHub's private vulnerability reporting is not enabled on the repository yet.

## [0.8.20] — 2026-10-08

### Added
- **Backup and restore scripts** (`scripts/backup.sh`, `restore.sh`, `backup.ps1`, `restore.ps1`). The only backup advice was "copy the folder", but the database runs in SQLite WAL mode, so a copy made while the app is running can be inconsistent. The scripts stop the backend, write a dated `.tar.gz` to `harmonisation-backups/`, and start it again; restore keeps the current data in `harmonisation-data.before-restore-<date>` instead of deleting it. Tested with a real cycle on the running Docker app (back up, Clear Workspace, restore) from both bash and PowerShell. Documented in `docs/docker.md`, including that Windows needs `-ExecutionPolicy Bypass` for the `.ps1` files. `harmonisation-backups/` is git-ignored because it holds participant data.

## [0.8.19] — 2026-10-08

### Security
- **Server errors no longer show raw Python error text.** When reading the codebook or building the transformed-data download failed, the API sent the exception text back to the caller (for example `Could not read codebook: <file path or data fragment>`). Both now answer a fixed message, "Something went wrong. Check the server log.", and the server log records only the route and the exception class (never the message text or request data, which can hold file paths or participant values). Helpful validation messages (400 errors such as "No studies specified", file-size and column-name problems) are unchanged.

## [0.8.18] — 2026-10-08

### Security
- **The AI provider API key is no longer sent in the web address.** Listing models for a vLLM server used `GET /api/ai-config/models?api_key=...`, so the key could end up in server logs, proxy logs and browser history. The key now travels in an `X-Api-Key` request header; the server no longer reads an `api_key` in the URL (such a request is treated as having no key). The AI Configuration panel sends the header automatically. Found by the access audit's "other observations".

## [0.8.17] — 2026-10-08

### Added
- **Automatic security scanners.** Every `git commit` is checked for leaked keys and tokens (gitleaks, via `.pre-commit-config.yaml`; run `python -m pip install pre-commit` then `python -m pre_commit install` once per clone). GitHub runs `.github/workflows/security-scans.yml` on every push and pull request, and every Monday: gitleaks over the whole history, `pip-audit` on `backend/requirements.txt`, `npm audit --omit=dev` on the JavaScript libraries, and Semgrep on the code. Actions are pinned to exact commits. The first local run found no leaked secrets and no vulnerable Python libraries, but 22 JavaScript findings (1 critical, 16 high) in build tooling (vite, TanStack Start, wrangler, undici, ws). By the owner's decision the npm job reports them without failing the run, and the exception is written in the workflow file; updating those packages is a separate follow-up.

## [0.8.16] — 2026-10-08

### Security
- **A plain `.env` file can no longer be committed by accident.** `docs/docker.md` tells people to put `GITHUB_TOKEN` in a `.env` file next to `docker-compose.yml`, but `.gitignore` did not list it, so a careless `git add .` would have committed the token. `.gitignore` now ignores `.env` and `.env.*`, and still allows a future `.env.example`.

## [0.8.15] — 2026-10-08

### Changed
- **Access audit closed out.** `pytest tests` is fully green (103 passed, no expected failures left), every one of the 28 API routes has a row in `ACCESS.md`, and the three findings in `ACCESS-AUDIT.md` are marked fixed. The output after the fixes is saved in `docs/access-audit-after.txt`. `ACCESS.md` now says both request checks answer 403 and that PATCH is covered like the other write methods. No app behaviour changes.

## [0.8.14] — 2026-10-08

### Security
- **A malicious website can no longer read your data through DNS rebinding.** A website could point its own domain name at your computer, and your browser would then let that page call the API and read the replies, including participant data (finding F3 in `ACCESS-AUDIT.md`). The backend now refuses (403) any request whose `Host` is not `localhost`, `127.0.0.1` or `::1`. Extra names for the opt-in network mode go in the new `MHT_ALLOWED_HOSTS` setting (documented in `docs/docker.md`, passed through both compose files). Starlette's stock host check cannot read IPv6 addresses like `[::1]:8000`, so the app uses a thin wrapper around it. All access tests are now green with no expected failures left; `tests/test_host_check.py` adds checks for IPv6, look-alike names and the setting.

## [0.8.13] — 2026-10-08

### Security
- **Other websites can no longer send hidden writes to the app.** A web page open in your browser could send a background form post to `localhost:8000` that wiped the workspace, replaced the codebook or planted a study (finding F2 in `ACCESS-AUDIT.md`). Browsers always label such requests with the page they came from (the `Origin` header). The backend now answers `403` to any POST, PUT, PATCH or DELETE whose `Origin` is not one of the tool's own localhost addresses, using the same list as the CORS settings. Requests with no `Origin` (curl, scripts) are still allowed, because only browsers can be tricked this way. The F2 tests, plus 14 DNS-rebinding write tests that the same check also closes, are off the expected-failure list; only the F3 read tests remain.

## [0.8.12] — 2026-10-08

### Security
- **The app now listens on your own computer only.** Before, both Docker setups published ports 8080 and 8000 on every network card, and `python run_backend.py` listened on `0.0.0.0`, so anyone on the same Wi-Fi or lab network could open the API and download or delete participant data (finding F1 in `ACCESS-AUDIT.md`). Ports are now published on `127.0.0.1`, and `run_backend.py` defaults to `127.0.0.1`. To open the app to a network on purpose, set `MHT_BIND_ADDRESS=0.0.0.0` (documented in `docs/docker.md` and the README); only do that on a trusted network. The three F1 tests in `tests/test_access.py` now pass and are off the expected-failure list.

## [0.8.11] — 2026-10-08

### Added
- **Access rules and the tests that prove them.** `ACCESS.md` says who may do what (only the researcher on the computer running the tool), `ACCESS-AUDIT.md` lists the three critical gaps found on 2026-10-07 (the API listens on the whole network, any website can send hidden writes, DNS rebinding), and `LAUNCH-CHECK.md` records the launch-readiness check. `tests/test_access.py` proves each rule; run it with `pytest tests/test_access.py`. The 36 tests that fail today because of those gaps are marked as expected failures in `tests/conftest.py`, so the build stays green, and each fix removes its own entries. The output before any fix is saved in `docs/access-audit-before.txt`. No app behaviour changes in this release.

## [0.8.10] — 2026-09-21

### Fixed
- **Initialise no longer stops with "Rate limit exceeded (60 req/min)" on real-sized data.** A built-in cap of 60 AI requests per minute, inherited from the original Streamlit app, aborted the run with an error instead of slowing down. A local Ollama or vLLM server answers in milliseconds, so the cap tripped within seconds and made real projects impossible: the 43-variable sample codebook needs about 109 embedding requests on its own, and the same cap hit any study over roughly 30 variables and any large PDF (which the AI reads in many pieces). It surfaced only at the end, after minutes of description writing. Servers you run yourself (Ollama, vLLM) now have no cap. Paid online services (OpenAI, Anthropic, Azure OpenAI) keep a 60-per-minute brake, but it now waits for a free slot and continues instead of failing the run. Found by running the full download-and-run flow with the real Ollama models on the sample data.

### Changed
- README: the download step of "Way 1" now says plainly that it is a large download (several GB, mostly the Ollama AI engine) and that re-running it resumes.

## [0.8.9] — 2026-09-21

### Added
- **Download-and-run install (no cloning, no building).** A new single file, `docker-compose.hub.yml`, starts the whole app from ready-made images on Docker Hub instead of building it on your own computer. GitHub now builds those images automatically every time `main` changes, for both PCs and Apple-Silicon Macs (Docker picks the right one), and publishes them as `atwine/mht-frontend` and `atwine/mht-backend` with the tag `latest` plus a permanent per-release tag (`main-<commit>`) for rolling back. The README's Docker section now has step-by-step instructions for Windows and Mac, and `docs/docker.md` explains how to pin an older version. The existing build-from-source `docker-compose.yml` is unchanged. The images contain the normal app only, none of the evaluation-build code.

## [0.8.8] — 2026-09-21

### Changed
- **The AI connection now survives a page reload.** Previously the AI settings and the connection test lived only in memory, so any full reload meant redoing Test Connection and re-entering custom provider settings. Provider, model, address and timeout are now kept for the browser session (cleared when the tab is closed), and if the connection was working, a reload re-checks it automatically ("Reconnecting to your AI provider…") before showing connected or not connected. **API keys are never stored** — providers that need one (OpenAI, Anthropic, Azure OpenAI) ask for it again after a reload.

### Fixed
- **The codebook upload now enforces what the screen says.** The Upload Codebook help lists `variable_name` and `description` as required, but the server only rejected a file missing *both*, so a file with just one was accepted and matched poorly. It now rejects a file missing either, and the message names exactly which column is missing. If a column is present but spelled differently (e.g. `Variable Name`), the message points to what it found, since names must match exactly. Study variables files use the same wording for their one required column (`variable_name`).

## [0.8.7] — 2026-09-21

### Added
- **"Preparing your input files" guide** ([`docs/input-file-format.md`](docs/input-file-format.md), linked from the README) — the exact column names, size limits and CSV rules for the codebook, study variables, example data and context PDF, plus a quick REDCap data-dictionary conversion. Getting files into shape was the step that took first-time testers longest, and until now the format was only visible after opening the app.
- Hover tooltips on the Upload Studies drop zones and the Upload Codebook drop zone, explaining what belongs in each.

### Changed
- **Map Studies:** the match score is now labelled "Codebook Confidence Match" — testers weren't sure what the percentage measured.
- **Context Document PDF:** the label, hint and tooltip now say what to upload (protocol, case report forms or a data dictionary), that only one PDF is used per study (merge several first), and that larger files make Initialise slower.
- **Test Connection is now stated as required** on the Initialise banner and in the AI Configuration panel — testers didn't realise the model isn't linked until the test is run.
- The in-app codebook format help no longer says a study variables file needs a `description` column (only `variable_name` is required; missing descriptions are generated during Initialise), and states that optional codebook columns can be left out entirely.

### Fixed
- **Leaving the Initialise page mid-run hid the run.** The progress log and result lived inside the page, so navigating away and back showed "Waiting to start" with the Run button enabled even though the run was still going — inviting a second, overlapping run. The run now lives in an app-wide store: coming back shows the live log or finished result, the prompt and "Force re-run" tick are kept, and starting a second run while one is active is refused. Clear Workspace also clears the previous run's log. (A full browser reload still resets everything, including the connection test — that's a separate change.)

## [0.8.6] — 2026-08-31

### Added
- **Onboarding tour** — every page (Home, Upload Codebook, Upload Studies, Initialise, Map Studies, Download Results) now shows a short guided tour (spotlight + tooltip, Next/Back/Skip) on a visitor's first visit to that page, tracked per-browser via localStorage so it never auto-plays again after Skip/Finish. Each page also has a "Take a tour" link to replay it anytime. Every step targets an element that's always present regardless of app/data state — pages with deeper, state-dependent content (Map Studies' mapping form, Download Results' per-study export cards) describe that content in a closing centered step instead of pointing at something that might not exist yet. Themed to the app's own palette rather than the `react-joyride` library's default black/white.

### Fixed
- `react-joyride` defaults clicking the dimmed tour backdrop to silently advancing to the next step instead of doing nothing — easy to trigger by accident since the overlay covers the whole viewport. Disabled (`overlayClickAction: false`).

## [0.8.5] — 2026-08-31

### Added
- **Opt-in toggle for AfPO population/ethnicity mapping** (closes #18) — the AfPO section on Map Studies previously triggered automatically for any variable whose matched codebook column name contained an ethnicity keyword, with no way to turn it off. Now gated behind an explicit toggle on the Initialise page, off by default. When it's off but a variable still looks like ethnicity data, a hint on Map Studies points the user to Initialise instead of the section silently not appearing.

## [0.8.4] — 2026-08-31

### Changed
- **Destructive-action confirmations are now real modal dialogs** (closes #19) — both "Clear Workspace" and deleting a study previously used an inline swap (the trigger button was replaced in place by confirm/cancel buttons occupying nearly the same screen position), making an accidental second click plausible for an irreversible action. Both now use the project's shadcn `AlertDialog` component, which was already installed but unused — gives focus trap and Esc-to-cancel for free. Each dialog also states exactly what will be deleted (study names, or a specific study's variable count) instead of a generic warning.

## [0.8.3] — 2026-08-24

### Added
- **Typography scale** — the ~180 arbitrary one-off `text-[Npx]` sizes scattered across every page (13-20px, 8 near-random increments) are replaced with 6 named tokens (`text-xs/sm/base/md/lg/xl`, defined once in `src/styles.css`). Two rare, near-duplicate sizes were folded into their nearest neighbor (a 1px shift, visually unnoticeable).
- **Workflow step strip** — every workflow page (Upload Codebook, Upload Studies, Initialise, Map Studies, Download Results) now shows where it sits in that 5-step flow, derived from the current route rather than hardcoded per page. Home's "Getting started" cards read from the same shared list, so the two surfaces can't drift apart.

### Changed
- The AI Configuration sidebar panel now collapses by default instead of always being expanded, freeing space for the actual workflow nav.

### Fixed
- Buttons not responding when clicked directly on their label text. `<button>` elements had no `user-select` override, so a real mouse's natural jitter between mousedown/mouseup on the label text could be interpreted as a text-selection drag instead of a click — clicking the same button's padding worked fine since there was nothing to select there. Fixed globally (`button { user-select: none }`), not just on the one button it was first reported on.

## [0.8.2] — 2026-08-20

### Fixed
- `mapping_summary.csv` inside the transformed-data ZIP export was silently missing AfPO population/ethnicity mapping data (`afpo_values_mapped`, `afpo_values_gaps`) for any variable that had it — present in the separate mapping-CSV download, but omitted from this file's column allowlist since it had never been added there.

## [0.8.1] — 2026-08-20

### Added
- Logo swap (eLwazi icon mark), and a page-by-page UI/UX pass: a "ghost grid" empty state on Upload Studies, a two-column Initialise layout, a Download Results grid with an empty-state nudge, and a Home page rework (justified welcome text, equal-height step cards).

### Fixed
- **AfPO "Submit to AfPO" opening a permanently blank tab.** `window.open(..., "noopener,noreferrer")` makes modern browsers return `null` from the call, severing the reference the code needed to navigate the tab once the backend-built issue URL resolved — so the tab was left on `about:blank` forever. Fixed by dropping `noopener`/`noreferrer` from that specific call (the destination is always our own backend-built `github.com` URL, so there's no reverse-tabnabbing risk).
- **A wrongly-set local "already submitted" AfPO flag had no recovery path**, permanently blocking resubmission of a term even when it was never actually filed (e.g. every term submitted while the bug above was active). Added a `POST /api/afpo/gaps/unsubmitted` endpoint and a "Not there? Re-check" UI action that live-checks GitHub and clears the flag only once it's confirmed no matching issue exists. Also fixed the unmark logic itself — it originally cleared only the single most-recent database row, but the "already submitted" read path checks globally across every historical row for that value, so an older row could keep reporting "submitted" even after the fix.

## [0.8.0] — 2026-08-20

### Added
- **Live GitHub duplicate check for AfPO term requests** — before letting a user file a new "New term request" issue, the backend live-queries the `h3abionet/afpo` repo's GitHub issue search for an existing open or closed issue with that exact term. This is the real cross-installation guard: every installation of this app, anywhere, points at the same shared repo, so a live check there catches duplicates a purely local flag never could (two different organisations independently hitting the same missing tribe name, or someone filing an issue manually outside the app). An open match blocks submission with a link to the existing issue; a closed match shows the link with a "Submit anyway" override since closed could mean merged, declined, or superseded. Results are cached 24h per term — GitHub's search API is capped at 10 requests/minute unauthenticated (30/minute with an optional `GITHUB_TOKEN`).
- **Auto-refreshing AfPO ontology** — the backend checks the upstream `.obo` file's `data-version` against what's loaded on every startup and hot-swaps the in-memory lookup table if there's a newer release, so a population/ethnicity term added upstream stops showing as a local "gap" without needing a rebuild or redeploy. Refreshed copies persist to a bind-mounted cache (`ontology_cache/`, `./harmonisation-data/ontology-cache` in Docker) so an offline restart still uses the last successful fetch instead of reverting to the version baked into the image. Never blocks or fails startup — falls back to whatever's already loaded on any network/parse error, and falls back further to the shipped file if a cached copy turns out corrupted.
- Ontology freshness (`data-version`, last synced) now shown directly in the Map Studies AfPO section.

### Fixed
- `clear-workspace` was wiping the entire AfPO submission history (`afpo_gaps`) along with mapping data — resetting the local duplicate-submission guard on every workspace reset and risking a real duplicate GitHub issue on the next encounter with the same term. It now only clears un-submitted gap rows; submitted history and the GitHub check cache are facts about the outside world, not local mapping progress, so clearing them wouldn't undo the GitHub submission — only make the app forget it happened.

## [0.7.0] — 2026-08-19

### Added
- **Docker Compose packaging** (closes #11) — `docker compose up` runs the full stack (frontend, backend, and a bundled Ollama) locally with no separate Python/Node/Ollama install. First run pulls a smaller default model (`llama3.2:3b`) into a persistent volume; every run after that is fast since the model cache survives `docker compose down`/`up`. Uploaded studies, mapping results, the audit trail, and the SQLite database are bind-mounted to `./harmonisation-data/` on the host — a normal folder, not a Docker-managed volume, so `docker compose down -v` can't silently wipe them. See `docs/docker.md`.
- Ollama's base URL and default chat/embedding models are now overridable via env vars (`OLLAMA_BASE_URL`, `OLLAMA_DEFAULT_CHAT_MODEL`, `OLLAMA_DEFAULT_EMBEDDING_MODEL` backend-side; `VITE_OLLAMA_*` frontend-side) instead of being hardcoded in six-plus places — what the Docker default-value change above needed, generalized to a single source of truth on each side.

### Changed
- **Mapping records, the audit trail, and the AfPO gap log now live in SQLite** (`db/app.db`) instead of `results/*.csv` / `logs/mapping_audit.jsonl` / `logs/afpo_gaps.csv`. Fixes the O(n) full-file-read-and-rewrite pattern on every mapping save, AfPO dedup check, and studies-list status lookup identified in a scale audit — the app now scales to many studies/variables without slowing down. No migration of old CSV/JSONL data (confirmed as synthetic test data, safe to leave behind untouched on disk).

### Fixed
- `DELETE /api/studies/{name}` and `POST /api/initialise/clear-workspace` now also clear the study's SQLite rows — previously they only touched `input/`/`results/`/`logs/`, so deleting a study or clearing the workspace could leave stale mapping data behind under a reused study name.

## [0.6.0] — 2026-08-18

### Added
- **vLLM provider** — chat and embedding models can now point at a self-hosted, OpenAI-compatible vLLM server, alongside Ollama, OpenAI, Anthropic, and Azure OpenAI.
- **Independent chat/embedding provider slots** — chat and embeddings can each use a different provider and server (e.g. chat via vLLM, embeddings via Ollama) instead of one shared config for both.
- **AfPO population/ethnicity ontology mapping** — a full port of the reference Streamlit app's AfPO integration: an ontology lookup engine (exact → synonym → fuzzy match against the African Population Ontology), a population-mapping sub-section on Map Studies triggered automatically by ethnicity-related codebook variables, gap logging, and one-click GitHub issue submission to the AfPO repo with a server-side guard against submitting the same term twice.
- **"Reopen for edit"** — variables outside the "To do" filter are now shown read-only with an explicit reopen step, instead of a live, editable Submit button sitting under every status.
- Audit-log download endpoint and UI section (`GET /api/download/audit-log`).
- `has_results` / `has_mapped_variable` fields on the Study model, so Download Results can gate its buttons on real backend state instead of guessing client-side.
- `docs/harmonisation_spec.md`, `example_data/` (ACE_Uganda, CH_SIB), and `assets/` brought into the repo for reference and end-to-end testing.

### Changed
- Download Results' mapping-CSV export and transformed-data ZIP now match the Streamlit reference exactly: the `0%` placeholder confidence value is stripped, empty columns are pruned, rows show most-recently-mapped first, and the ZIP is a full 5-file package (original data, transformed CSV, mapping summary, validation report, run summary) instead of just the transformed CSV.
- Map Studies: the codebook-match dropdown auto-selects the top recommendation for a fresh variable (matching the reference app's default-select behaviour); the confidence badge now tracks whichever match is actually selected, not just the top one; the status filter shows a live count and an explanatory caption instead of silently swapping the variable list.
- Initialise: a clear pass/fail banner appears once the recommendation engine finishes, and re-running an already-fully-initialised set of studies is blocked unless "Force re-run" is checked.
- Sidebar widened with larger, more readable fonts throughout the AI configuration panel.

### Fixed
- Ollama model-list parsing (`KeyError: 'name'`) on newer Ollama client versions.
- Study upload silently failing 422s because the form field names didn't match what the backend expected.
- Example-data card overflowing its container on Map Studies.
- Two study variables mapped to the same codebook column silently overwriting each other in the transformed export, with no indication the second one had been dropped.
- AfPO ontology mapping data getting wiped when a mapping was resubmitted without re-running the lookup (e.g. after reopening a variable to fix a typo).
- OpenAI/Anthropic "Test Connection" reporting success even when the configured model name doesn't exist, only failing later mid-pipeline.
- A stale-dependency bug that could leave a model dropdown unresolved when switching providers.
- Raw, unparsed JSON error bodies surfacing verbatim in the UI instead of a clean message (fixed client-wide, 7 call sites shared the same bug).
- `HEAD` requests 405ing on the audit-log route, which silently hid its "Download audit log" button.
- Duplicated logic (Ollama model-name parsing, the AfPO GitHub issue template) consolidated to a single source of truth on the backend.

## [0.5.0] — 2026-05-15
- Initial FastAPI backend + full React (TanStack Start) frontend port of the Streamlit app, covering Upload Codebook, Upload Studies, Initialise, Map Studies, and Download Results.
- Ollama connection handling, model dropdowns, wider sidebar with larger fonts.
