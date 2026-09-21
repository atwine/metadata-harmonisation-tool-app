# Metadata Harmonisation Tool

A web application for mapping study dataset variables onto a canonical target codebook, built for the [eLwazi Open Data Science Platform](https://elwazi.org).

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## What it does

Researchers upload one or more study datasets (CSV files of variable names) alongside a target codebook. An AI model generates natural-language descriptions for cryptic variable names, builds semantic embeddings, and recommends the best codebook matches for each variable. A human operator then reviews and approves each mapping, adds transformation rules, and exports the harmonised data.

Variables that look like population/ethnicity data (e.g. mapped to a codebook variable named `ethnicity`) can get an extra step: values found in the study data are looked up against the [AfPO](https://github.com/h3abionet/afpo) (African Population Ontology), with one-click submission of any unmatched terms as a new-term request on the AfPO GitHub repo. This is opt-in — off by default, enabled per session with a toggle on the Initialise page, since not every study needs it.

A first-time visitor to any page gets a short guided tour (spotlight + tooltip) pointing out what's where; it only auto-plays once per browser per page, and can be replayed anytime via the "Take a tour" link.

> **Before you start:** your codebook and study files need specific column names and a CSV format. See [Preparing your input files](docs/input-file-format.md) (includes a quick REDCap conversion), as this is the step that takes most people the longest.

**Workflow:**
1. **Upload Codebook** — the canonical target variable list (CSV)
2. **Upload Studies** — one or more study variable CSVs, with optional example-data CSV and context PDF
3. **Initialise** — AI generates descriptions → embeddings → semantic recommendations (streamed live); also where the AfPO opt-in toggle lives
4. **Map Studies** — operator reviews each variable, picks a codebook match, sets a transformation, marks it done; population/ethnicity variables get an AfPO ontology lookup sub-section when AfPO mapping is enabled
5. **Download Results** — export the mapping table (CSV) or the transformed dataset (ZIP), plus the audit log

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TanStack Start + Router, TanStack Query, Zustand, Tailwind v4, react-joyride (onboarding tour) |
| Backend | FastAPI, Python 3.12, Pydantic v2, Pandas |
| AI providers | Ollama (local), vLLM (self-hosted, OpenAI-compatible), OpenAI, Anthropic, Azure OpenAI — chat and embedding models are configured independently and can each point at a different provider |
| Embeddings | Cosine similarity, weighted 0.8 × description + 0.2 × variable name |
| Ontology matching | Exact → synonym → fuzzy (rapidfuzz) lookup against the AfPO `.obo` ontology file |

## Project structure

```
.
├── backend/                   # FastAPI application
│   ├── core/
│   │   ├── ai_provider.py     # Provider wrapper (Ollama / vLLM / OpenAI / Anthropic / Azure)
│   │   ├── config.py          # Per-slot provider config + client construction
│   │   ├── afpo_lookup.py     # AfPO .obo parser + exact/synonym/fuzzy lookup + auto-refresh from upstream
│   │   ├── afpo_gap_reporter.py  # Pre-filled GitHub issue URL builder
│   │   ├── afpo_github_check.py  # Live GitHub search — the cross-installation duplicate-request guard
│   │   ├── descriptions.py    # Phase 2: AI description generation
│   │   ├── recommendations.py # Phases 1, 3–5: embeddings + semantic search
│   │   ├── transform_engine.py
│   │   └── transformation_utils.py  # SafeEvaluator (no eval())
│   ├── models/schemas.py      # Pydantic request/response models
│   ├── routers/               # FastAPI routers
│   │   ├── afpo.py            # AfPO lookup + gap submission
│   │   ├── ai_config.py       # Providers, connection test, live model listing
│   │   ├── codebook.py
│   │   ├── download.py
│   │   ├── initialise.py      # SSE streaming endpoint
│   │   ├── mappings.py        # Core mapping CRUD + audit trail
│   │   └── studies.py
│   ├── storage/
│   │   ├── db.py              # SQLite (mapping records, audit trail, AfPO gap log)
│   │   └── files.py
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── data/ontologies/           # AfPO ontology data (afpo-base.obo)
├── docs/
│   ├── docker.md               # Docker Compose walkthrough (data location, troubleshooting)
│   ├── input-file-format.md    # Column names, sizes and REDCap conversion for the CSV/PDF inputs
│   └── harmonisation_spec.md   # Rebuild spec / architecture reference
├── example_data/              # Sample codebooks + studies for local testing
├── src/                       # React frontend
│   ├── api/client.ts          # Typed API client + TanStack Query hooks
│   ├── components/
│   │   ├── Sidebar.tsx         # Nav, AI Configuration panel, PageHeader + the workflow step strip
│   │   ├── ProductTour.tsx     # Themed react-joyride wrapper + the "Take a tour" replay button
│   │   └── ui/alert-dialog.tsx # shadcn AlertDialog — used for destructive-action confirmations
│   ├── hooks/useProductTour.ts # Per-page tour seen-state (localStorage) + replay control
│   ├── routes/                # File-based routing (TanStack Router)
│   │   ├── upload-codebook.tsx
│   │   ├── upload-studies.tsx
│   │   ├── initialise.tsx     # Includes the AfPO opt-in toggle and the Danger Zone (Clear Workspace)
│   │   ├── map-studies.tsx    # Includes the AfPO population-mapping sub-section
│   │   └── download-results.tsx
│   ├── stores/                # Zustand stores
│   │   ├── aiConfigStore.ts
│   │   ├── mappingStore.ts
│   │   └── wizardStore.ts     # afpoMappingEnabled, relationalModeEnabled — session-only toggles
│   ├── styles.css             # Design tokens (colors, the text-xs..xl type scale)
│   └── types.ts
├── docker-compose.yml         # Full-stack local packaging — builds the app from source
├── docker-compose.hub.yml     # Same stack from prebuilt images (download this one file and run)
├── Dockerfile.frontend
└── run_backend.py             # Entry point — runs uvicorn from project root
```

## Running via Docker Compose

For non-technical end users, or anyone who'd rather not install Python/Node/Ollama
separately. Everything runs locally on your own computer — no shared or hosted AI
backend, and your data never leaves the machine. There are two ways to start it.
**Most people should use Way 1.**

**Before either way, install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
and make sure it is running** (open it and wait until it says "Docker Desktop is
running"). You need about 8 GB of free RAM and a few GB of free disk space for the AI models.

### Way 1 (recommended): download and run — no cloning, no building

Docker downloads ready-made copies of the app instead of assembling them on your
computer. They are built automatically by GitHub every time the app is updated, and
the same download works on Windows PCs, Intel Macs and Apple-Silicon Macs (Docker
picks the right one for you). You only need **one small file**, not the whole repository.

1. **Make an empty folder** anywhere (for example `mht`) and open a terminal in it.
   On a Mac use *Terminal*; on Windows use *PowerShell*.
   ```bash
   mkdir mht
   cd mht
   ```

2. **Download the one file** that tells Docker what to run.

   Mac or Linux:
   ```bash
   curl -O https://raw.githubusercontent.com/atwine/metadata-harmonisation-tool-app/main/docker-compose.hub.yml
   ```
   Windows (PowerShell) — note it is `curl.exe`, not `curl`:
   ```bash
   curl.exe -O https://raw.githubusercontent.com/atwine/metadata-harmonisation-tool-app/main/docker-compose.hub.yml
   ```

3. **Download the app** (this fetches the ready-made copies):
   ```bash
   docker compose -f docker-compose.hub.yml pull
   ```
   This is the **biggest download: several GB in total**, most of it the Ollama AI engine
   (the AI models themselves come in step 4). Do it on a good connection. If it is
   interrupted, just run the same command again — it skips whatever already finished.

4. **Start it:**
   ```bash
   docker compose -f docker-compose.hub.yml up
   ```
   The **first** time, it also downloads the AI models (several GB), so be patient.
   When you see `[ollama-entrypoint] models ready — serving.` it is ready.

5. **Open the app** in your browser: <http://localhost:8080>

**Your data** is saved in a folder called `harmonisation-data`, created next to the
file you downloaded. It is a normal folder — back it up by copying it. Stopping or
updating the app never deletes it.

**Stopping:** press `Ctrl+C` in the terminal, then run
`docker compose -f docker-compose.hub.yml down`.

**Updating to the newest version:** run steps 3 and 4 again (`pull`, then `up`).

**Which folder do I run these in?** Always the folder that contains
`docker-compose.hub.yml` — Docker looks for the file in the folder you are in.

**Already using Way 2 on this computer?** Stop it first (run `docker compose down` in its
folder), because both ways use ports 8000 and 8080. The two are completely separate: Way 1
keeps its own copy of the AI models (so they download once more) and its own
`harmonisation-data` folder. To bring your existing work across, copy your old
`harmonisation-data` folder into the new folder before you start.

### Way 2: clone the repository and build it yourself

For developers, or anyone who wants to read or change the code. This builds the app
on your own computer, which is slower (it downloads and compiles packages) but needs
nothing from Docker Hub.

```bash
git clone https://github.com/atwine/metadata-harmonisation-tool-app.git
cd metadata-harmonisation-tool-app
docker compose up
```

Run that last command from *inside* the cloned folder — `docker compose` looks for
`docker-compose.yml` in whatever directory you're in, and that file lives at the
top level of this repo. The app is then at <http://localhost:8080>.

See [`docs/docker.md`](docs/docker.md) for the full walkthrough, including where your
data lives, how to back it up, and troubleshooting. It applies to both ways.

## Running locally

### Prerequisites

- Python 3.10+
- Node.js 18+
- An AI provider: [Ollama](https://ollama.com) (free, local), a self-hosted vLLM server, or an OpenAI / Anthropic / Azure OpenAI API key

### Backend

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r backend/requirements.txt

python run_backend.py
# → http://localhost:8000
# → Swagger docs: http://localhost:8000/docs
```

### Frontend

```bash
npm install
npm run dev
# → http://localhost:5173
```

### Environment

Create `.env.local` in the project root (already gitignored):

```
VITE_API_URL=http://localhost:8000
```

Optional backend env var: `GITHUB_TOKEN` — a personal access token to raise the AfPO
duplicate-check's GitHub search rate limit from 10 requests/minute (unauthenticated) to
30/minute. Not required.

## API overview

| Method | Path | Description |
|---|---|---|
| POST | `/api/codebook/upload` | Upload target codebook CSV |
| POST | `/api/studies/upload` | Upload a study (variables CSV + optional files) |
| POST | `/api/initialise/run` | Run AI pipeline (SSE stream) |
| GET | `/api/mappings/{study}` | List variable mappings with progress |
| GET | `/api/mappings/{study}/variable/{name}` | Variable detail + recommendations |
| PUT | `/api/mappings/{study}/variable/{name}` | Save a mapping decision |
| PUT | `/api/mappings/{study}/variable/{name}/reopen` | Reopen a decided variable back to "To do" |
| POST | `/api/mappings/preview-transformation` | Test a transformation expression |
| GET | `/api/ai-config/providers` | List supported AI providers + capabilities |
| POST | `/api/ai-config/test` | Test chat + embedding connection (independently) |
| GET | `/api/ai-config/models` | Live model listing for Ollama / vLLM |
| POST | `/api/afpo/lookup` | Look up population/ethnicity values against AfPO |
| GET | `/api/afpo/check-github` | Live-check GitHub for an existing term-request issue (cached 24h; `?force=true` bypasses the cache) |
| POST | `/api/afpo/gaps/submitted` | Mark an AfPO gap as submitted to GitHub |
| POST | `/api/afpo/gaps/unsubmitted` | Clear a wrongly-set "already submitted" flag, once a live GitHub check confirms no matching issue actually exists |
| GET | `/api/afpo/issue-url` | Build the pre-filled AfPO GitHub issue URL |
| GET | `/api/afpo/ontology-status` | Current AfPO ontology version and last-sync time |
| GET | `/api/download/{study}/mapping-csv` | Download mapping table |
| POST | `/api/download/transformed-data` | Download transformed dataset ZIP |
| GET | `/api/download/audit-log` | Download the append-only mapping audit trail |

Full interactive docs at `http://localhost:8000/docs` when the backend is running.

## Audit trail

Every mapping save is appended to the SQLite database (`db/app.db`, `audit_log` table) with:
- Timestamp, operator name, study, variable
- Before/after state
- SHA-256 hash of transformation instructions

AfPO lookups that don't match any ontology term are logged to the same database's
`afpo_gaps` table (timestamp, study, variable, value, whether it's been submitted to
GitHub yet). Duplicate submissions are guarded two ways: a local flag (this table) for
what this installation has already filed, and a live GitHub issue search — the real
cross-installation check, since every installation points at the same shared AfPO repo —
before a new submission is allowed. If that local flag is ever wrong (e.g. a submission
that never actually reached GitHub), Map Studies has a "Not there? Re-check" action that
live-checks GitHub and clears the flag only once it confirms no matching issue exists.
See `docs/docker.md` for how the AfPO ontology itself stays up to date.

## Branches

- **`main`** — protected; only updated via a reviewed PR from `staging`.
- **`staging`** — pushed to directly from `development`, no PR required.
- **`development`** — active work happens here.

## Security notes

- Transformation expressions are evaluated by a custom AST-walking `SafeEvaluator` — `eval()` is never called.
- All file paths are sanitised against path traversal before use.
- Uploaded PDFs are validated against their magic bytes before processing.
- The `logs/`, `input/`, `results/`, `db/`, and `ontology_cache/` directories are excluded from git — all runtime-generated, not source.
- AfPO GitHub issue submission is always a manual click — the app never submits on the user's behalf. A local flag prevents this installation from re-filing a term it already submitted, and a live GitHub issue search (`GET /api/afpo/check-github`) catches duplicates across installations too, since every installation of this app points at the same shared AfPO repo.
- Both destructive actions in the app (Clear Workspace, deleting a study) require an explicit confirmation dialog rather than a single click — a deliberate defense against accidental data loss.
- ⚠️ A known gap (tracked in [issue #4](../../issues/4)): the API currently has no authentication — don't expose the backend beyond localhost/trusted networks as-is.

## License

MIT
