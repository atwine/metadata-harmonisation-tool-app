import io
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from core.transform_engine import apply_transformations
from models.schemas import TransformedDataRequest
from storage.files import sanitise_study_name

router = APIRouter()

_CORE_MAPPING_COLS = ["study_var", "codebook_var", "confidence", "notes", "marked"]


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
        raise HTTPException(
            404,
            "No results file for this study yet. Map at least one variable in Map Studies first.",
        )

    try:
        df = pd.read_csv(results_path)
    except Exception as e:
        raise HTTPException(500, f"Could not read results file: {e}")

    # Mirror the reference app's export cleaning: drop the '0%' placeholder
    # confidence value, keep core columns first and prune extra columns that
    # are entirely empty, then show most-recently-mapped rows first.
    df = df.replace("0%", None)
    core_present = [c for c in _CORE_MAPPING_COLS if c in df.columns]
    extra = df.drop(columns=core_present).dropna(axis=1, how="all")
    df = pd.concat([df[core_present], extra], axis=1)
    df = df.iloc[::-1]

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={study_name}_mapping_results.csv"},
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
        zip_bytes, results = apply_transformations(safe_studies)
    except Exception as e:
        raise HTTPException(500, f"Transformation failed: {e}")

    if all(r["status"] == "skipped" for r in results):
        reasons = "; ".join(f"{r['study']}: {r['reason']}" for r in results)
        raise HTTPException(422, f"Nothing to export — {reasons}")

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=transformed_data.zip"
        },
    )


@router.api_route("/audit-log", methods=["GET", "HEAD"])
async def download_audit_log():
    """Streams the append-only mapping audit trail (all studies, all writes)."""
    audit_path = Path("logs/mapping_audit.jsonl")
    if not audit_path.exists():
        raise HTTPException(404, "Audit log not found (no mapping writes recorded yet).")

    return FileResponse(
        path=str(audit_path),
        media_type="application/json",
        filename="mapping_audit.jsonl",
    )
