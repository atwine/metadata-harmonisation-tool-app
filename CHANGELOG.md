# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
