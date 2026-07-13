# Metadata Harmonisation Tool

A web application for mapping study dataset variables onto a canonical target codebook, built for the [eLwazi Open Data Science Platform](https://elwazi.org).

## What it does

Researchers upload one or more study datasets (CSV files of variable names) alongside a target codebook. An AI model generates natural-language descriptions for cryptic variable names, builds semantic embeddings, and recommends the best codebook matches for each variable. A human operator then reviews and approves each mapping, adds transformation rules, and exports the harmonised data.

**Workflow:**
1. **Upload Codebook** — the canonical target variable list (CSV)
2. **Upload Studies** — one or more study variable CSVs, with optional example-data CSV and context PDF
3. **Initialise** — AI generates descriptions → embeddings → semantic recommendations (streamed live)
4. **Map Studies** — operator reviews each variable, picks a codebook match, sets a transformation, marks it done
5. **Download Results** — export the mapping table (CSV) or the transformed dataset (ZIP)

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TanStack Start + Router, TanStack Query, Zustand, Tailwind v4 |
| Backend | FastAPI, Python 3.12, Pydantic v2, Pandas |
| AI providers | Ollama (local), OpenAI, Anthropic, Azure OpenAI |
| Embeddings | Cosine similarity, weighted 0.8 × description + 0.2 × variable name |

## Project structure

```
.
├── backend/                   # FastAPI application
│   ├── core/
│   │   ├── ai_provider.py     # Provider wrapper (Ollama / OpenAI / Anthropic / Azure)
│   │   ├── descriptions.py    # Phase 2: AI description generation
│   │   ├── recommendations.py # Phases 1, 3–5: embeddings + semantic search
│   │   ├── transform_engine.py
│   │   └── transformation_utils.py  # SafeEvaluator (no eval())
│   ├── models/schemas.py      # Pydantic request/response models
│   ├── routers/               # FastAPI routers
│   │   ├── ai_config.py
│   │   ├── codebook.py
│   │   ├── download.py
│   │   ├── initialise.py      # SSE streaming endpoint
│   │   ├── mappings.py        # Core mapping CRUD + audit trail
│   │   └── studies.py
│   ├── storage/files.py
│   ├── main.py
│   └── requirements.txt
├── src/                       # React frontend
│   ├── api/client.ts          # Typed API client + TanStack Query hooks
│   ├── routes/                # File-based routing (TanStack Router)
│   │   ├── upload-codebook.tsx
│   │   ├── upload-studies.tsx
│   │   ├── initialise.tsx
│   │   ├── map-studies.tsx
│   │   └── download-results.tsx
│   ├── stores/                # Zustand stores
│   │   ├── aiConfigStore.ts
│   │   ├── mappingStore.ts
│   │   └── wizardStore.ts
│   └── types.ts
└── run_backend.py             # Entry point — runs uvicorn from project root
```

## Running locally

### Prerequisites

- Python 3.10+
- Node.js 18+
- An AI provider: [Ollama](https://ollama.com) (free, local) or an OpenAI / Anthropic API key

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

## API overview

| Method | Path | Description |
|---|---|---|
| POST | `/api/codebook/upload` | Upload target codebook CSV |
| POST | `/api/studies/upload` | Upload a study (variables CSV + optional files) |
| POST | `/api/initialise/run` | Run AI pipeline (SSE stream) |
| GET | `/api/mappings/{study}` | List variable mappings with progress |
| GET | `/api/mappings/{study}/variable/{name}` | Variable detail + recommendations |
| PUT | `/api/mappings/{study}/variable/{name}` | Save a mapping decision |
| POST | `/api/mappings/preview-transformation` | Test a transformation expression |
| GET | `/api/download/{study}/mapping-csv` | Download mapping table |
| POST | `/api/download/transformed-data` | Download transformed dataset ZIP |

Full interactive docs at `http://localhost:8000/docs` when the backend is running.

## Audit trail

Every mapping save is appended to `logs/mapping_audit.jsonl` with:
- Timestamp, operator name, study, variable
- Before/after state
- SHA-256 hash of transformation instructions

## Security notes

- Transformation expressions are evaluated by a custom AST-walking `SafeEvaluator` — `eval()` is never called.
- All file paths are sanitised against path traversal before use.
- Uploaded PDFs are validated against their magic bytes before processing.
- The `logs/`, `input/`, and `results/` directories are excluded from git.

See [SECURITY_AUDIT.md](SECURITY_AUDIT.md) for the full audit of the current codebase, including open findings.

## License

MIT
