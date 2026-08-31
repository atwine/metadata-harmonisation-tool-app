# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
