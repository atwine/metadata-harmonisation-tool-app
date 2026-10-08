import re
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import codebook, studies, initialise, mappings, download, ai_config, afpo
from core.afpo_lookup import refresh_ontology
from storage.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    for d in ["input", "results", "logs"]:
        Path(d).mkdir(exist_ok=True)
    init_db()
    # Best-effort and async — refresh_ontology() already catches network/parse
    # errors and falls back to whatever's already loaded, and awaiting it
    # (rather than a blocking call) keeps the event loop free for other
    # startup work instead of freezing on a slow network for its timeout.
    await refresh_ontology()
    yield


app = FastAPI(title="Metadata Harmonisation API", lifespan=lifespan)

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:4173",
    "http://localhost:8788",
    "http://localhost:8080",
]
ALLOWED_ORIGIN_REGEX = re.compile(r"http://localhost:\d+")
STATE_CHANGING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX.pattern,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def refuse_cross_site_writes(request: Request, call_next):
    # Browsers always send Origin on cross-site POSTs, and CORS only stops the
    # page reading the reply, not the write. Requests with no Origin (curl,
    # scripts, the test client) are not browser cross-site requests and stay allowed.
    origin = request.headers.get("origin")
    if (
        origin is not None
        and request.method in STATE_CHANGING_METHODS
        and origin not in ALLOWED_ORIGINS
        and not ALLOWED_ORIGIN_REGEX.fullmatch(origin)
    ):
        return JSONResponse({"detail": "Cross-site request refused"}, status_code=403)
    return await call_next(request)

app.include_router(codebook.router,   prefix="/api/codebook")
app.include_router(studies.router,    prefix="/api/studies")
app.include_router(initialise.router, prefix="/api/initialise")
app.include_router(mappings.router,   prefix="/api/mappings")
app.include_router(download.router,   prefix="/api/download")
app.include_router(ai_config.router,  prefix="/api/ai-config")
app.include_router(afpo.router,       prefix="/api/afpo")
