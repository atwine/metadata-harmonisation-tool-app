from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import codebook, studies, initialise, mappings, download, ai_config, afpo


@asynccontextmanager
async def lifespan(app: FastAPI):
    for d in ["input", "results", "logs"]:
        Path(d).mkdir(exist_ok=True)
    yield


app = FastAPI(title="Metadata Harmonisation API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",
        "http://localhost:8788",
        "http://localhost:8080",
    ],
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(codebook.router,   prefix="/api/codebook")
app.include_router(studies.router,    prefix="/api/studies")
app.include_router(initialise.router, prefix="/api/initialise")
app.include_router(mappings.router,   prefix="/api/mappings")
app.include_router(download.router,   prefix="/api/download")
app.include_router(ai_config.router,  prefix="/api/ai-config")
app.include_router(afpo.router,       prefix="/api/afpo")
