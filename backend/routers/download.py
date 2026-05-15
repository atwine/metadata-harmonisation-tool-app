import io
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from core.transform_engine import apply_transformations
from models.schemas import TransformedDataRequest
from storage.files import sanitise_study_name

router = APIRouter()


@router.get("/{study_name}/mapping-csv")
async def download_mapping_csv(study_name: str):
    try:
        study_name = sanitise_study_name(study_name)
    except ValueError as e:
        raise HTTPException(400, str(e))

    results_path = Path("results") / f"{study_name}.csv"

    # Path traversal guard
    resolved = results_path.resolve()
    allowed  = Path("results").resolve()
    if not str(resolved).startswith(str(allowed)):
        raise HTTPException(400, "Invalid study name")

    if not results_path.exists():
        raise HTTPException(404, "No results file for this study")

    return FileResponse(
        path=str(results_path),
        media_type="text/csv",
        filename=f"{study_name}_mappings.csv",
    )


@router.post("/transformed-data")
async def download_transformed_data(body: TransformedDataRequest):
    if not body.studies:
        raise HTTPException(400, "No studies specified")

    safe_studies: list[str] = []
    for s in body.studies:
        try:
            safe_studies.append(sanitise_study_name(s))
        except ValueError:
            raise HTTPException(400, f"Invalid study name: {s}")

    try:
        zip_bytes, _metrics = apply_transformations(safe_studies)
    except Exception as e:
        raise HTTPException(500, f"Transformation failed: {e}")

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=transformed_data.zip"
        },
    )
