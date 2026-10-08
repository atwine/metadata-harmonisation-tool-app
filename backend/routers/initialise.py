import asyncio
import json
import shutil
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from core.errors import log_failure, server_error
from models.schemas import InitialiseRequest, InitialiseStatusResponse, StudyInitStatus
from storage import db
from storage.files import list_studies

router = APIRouter()


# ── SSE streaming endpoint ────────────────────────────────────────────────────

@router.post("/run")
async def run_initialise(body: InitialiseRequest):
    async def event_stream():
        def emit(step: str, status: str, message: str) -> str:
            return f"data: {json.dumps({'step': step, 'status': status, 'message': message})}\n\n"

        # Phase 1 — PDF conversion (no AI required)
        yield emit("pdf_conversion", "running", "Converting PDFs to text...")
        try:
            await asyncio.to_thread(_run_pdf_conversion)
            yield emit("pdf_conversion", "done", "PDFs converted.")
        except Exception as e:
            log_failure("initialise/pdf_conversion", e)
            yield emit("pdf_conversion", "error", "PDF conversion failed. The study will continue without its context document.")
            # Non-fatal — continue

        # Phase 2 — Description generation
        yield emit("descriptions", "running", "Generating variable descriptions...")
        try:
            await asyncio.to_thread(
                _run_descriptions, body.ai_config, body.init_prompt, body.force_rerun
            )
            yield emit("descriptions", "done", "Descriptions generated.")
        except Exception as e:
            log_failure("initialise/descriptions", e)
            yield emit("descriptions", "error", "Description generation failed. Check the AI connection (Test Connection) and that the chat model is running.")
            return  # Fatal — embeddings depend on descriptions

        # Phase 3 — Embeddings
        yield emit("embeddings", "running", "Generating embeddings...")
        try:
            await asyncio.to_thread(_run_embeddings, body.ai_config, body.force_rerun)
            yield emit("embeddings", "done", "Embeddings complete.")
        except Exception as e:
            log_failure("initialise/embeddings", e)
            yield emit("embeddings", "error", "Embedding failed. Check the AI connection (Test Connection) and that the embedding model is running.")
            return

        # Phase 4 — Semantic recommendations
        yield emit("recommendations", "running", "Building semantic recommendations...")
        try:
            await asyncio.to_thread(_run_recommendations, body.force_rerun)
            yield emit("recommendations", "done", "Recommendations ready.")
        except Exception as e:
            log_failure("initialise/recommendations", e)
            yield emit("recommendations", "error", "Recommendation generation failed. Check the server log for details.")
            return

        # Phase 5 — PID / Date recommendations
        yield emit("pid_date", "running", "Generating PID/Date recommendations...")
        try:
            await asyncio.to_thread(_run_pid_date, body.ai_config, body.force_rerun)
            yield emit("pid_date", "done", "PID/Date recommendations ready.")
        except Exception as e:
            log_failure("initialise/pid_date", e)
            yield emit("pid_date", "error", "PID/Date recommendation failed. Check the AI connection and the server log.")
            return

        yield emit("complete", "done", "Recommendation engine finished.")

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Thread-safe wrappers (called via asyncio.to_thread) ──────────────────────

def _run_pdf_conversion():
    from core.recommendations import convert_pdf_to_txt
    convert_pdf_to_txt()


def _run_descriptions(ai_config, init_prompt: str, force_rerun: bool):
    from core.descriptions import generate_descriptions
    generate_descriptions(ai_config, init_prompt, force_rerun)


def _run_embeddings(ai_config, force_rerun: bool):
    from core.recommendations import get_embeddings
    get_embeddings(ai_config, force_rerun)


def _run_recommendations(force_rerun: bool):
    from core.recommendations import get_recommendations
    get_recommendations(force_rerun)


def _run_pid_date(ai_config, force_rerun: bool):
    from core.recommendations import get_PID_date_recommendations
    get_PID_date_recommendations(ai_config, force_rerun)


# ── Status endpoint ───────────────────────────────────────────────────────────

@router.get("/status", response_model=InitialiseStatusResponse)
async def get_status():
    studies_status: list[StudyInitStatus] = []
    for name in list_studies():
        study_dir = Path("input") / name
        studies_status.append(
            StudyInitStatus(
                name=name,
                descriptions_generated=(
                    study_dir / "dataset_variables_auto_completed.csv"
                ).exists(),
                embeddings_ready=(
                    study_dir / "dataset_variables_with_embeddings.csv"
                ).exists(),
                recommendations_ready=(
                    study_dir / "dataset_variables_with_recommendations.csv"
                ).exists(),
                pid_date_ready=(
                    study_dir / "dataset_variables_with_PID_date_recommendations.csv"
                ).exists(),
            )
        )

    return InitialiseStatusResponse(
        codebook_embedded=Path("input/target_variables_with_embeddings.csv").exists(),
        studies=studies_status,
    )


# ── Clear workspace ───────────────────────────────────────────────────────────

@router.post("/clear-workspace")
async def clear_workspace():
    """Delete all runtime files in input/, results/, logs/."""
    project_root = Path(".").resolve()
    cleared: list[str] = []

    try:
        for d in ["input", "results", "logs"]:
            path = Path(d).resolve()
            # Safety: must be a direct child of project root
            if path.parent == project_root and path.exists():
                # Empty the folder but keep it: in Docker these are mounted
                # folders, and removing the mount point itself fails ("Device or resource busy").
                for child in path.iterdir():
                    if child.is_dir() and not child.is_symlink():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
                cleared.append(d)

        db.clear_all()
    except Exception as e:
        raise server_error("/api/initialise/clear-workspace", e)

    return {"status": "cleared", "directories": cleared}
