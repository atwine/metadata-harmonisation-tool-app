import io
import json
from urllib.parse import quote

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from core.errors import server_error
from core.script_export import NoMappedVariables, generate_script
from core.transform_engine import apply_transformations
from models.schemas import TransformedDataRequest
from storage import db
from storage.files import sanitise_study_name

router = APIRouter()

_CORE_MAPPING_COLS = ["study_var", "codebook_var", "confidence", "notes", "marked"]


@router.get("/{study_name}/mapping-csv")
async def download_mapping_csv(study_name: str):
    try:
        study_name = sanitise_study_name(study_name)
    except ValueError as e:
        raise HTTPException(400, str(e))

    rows = db.all_mappings_for_export(study_name)
    if not rows:
        raise HTTPException(
            404,
            "No results file for this study yet. Map at least one variable in Map Studies first.",
        )

    df = pd.DataFrame(rows).drop(columns=["id", "study", "updated_at"], errors="ignore")

    # Mirror the reference app's export cleaning: drop the '0%' placeholder
    # confidence value, keep core columns first and prune extra columns that
    # are entirely empty. Rows are already most-recently-touched first
    # (all_mappings_for_export orders by updated_at DESC).
    df = df.replace("0%", None)
    core_present = [c for c in _CORE_MAPPING_COLS if c in df.columns]
    extra = df.drop(columns=core_present).dropna(axis=1, how="all")
    df = pd.concat([df[core_present], extra], axis=1)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={study_name}_mapping_results.csv"},
    )


def _script_disposition(study_name: str) -> str:
    """RFC 6266: plain ASCII name for old clients plus filename* with the real UTF-8 name,
    because study names may use non-Latin scripts and headers must be ASCII."""
    ascii_name = "".join(c if c.isascii() else "_" for c in study_name)
    return (
        f'attachment; filename="transform_{ascii_name}.py"; '
        f"filename*=UTF-8''transform_{quote(study_name)}.py"
    )


@router.get("/{study_name}/script")
async def download_transform_script(study_name: str):
    """A standalone Python script holding this study's confirmed mappings (no participant data)."""
    try:
        study_name = sanitise_study_name(study_name)
    except ValueError as e:
        raise HTTPException(400, str(e))

    try:
        script = generate_script(study_name)
    except NoMappedVariables:
        raise HTTPException(
            422,
            'No variables marked "Successfully mapped" yet - nothing to put in a script.',
        )
    except Exception as e:
        raise server_error("/api/download/{study_name}/script", e)

    return StreamingResponse(
        io.BytesIO(script.encode("utf-8")),
        media_type="text/x-python",
        headers={"Content-Disposition": _script_disposition(study_name)},
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
        raise server_error("/api/download/transformed-data", e)

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
    """Streams the append-only mapping audit trail (all studies, all writes) as JSONL."""
    records = db.get_all_audit()
    if not records:
        raise HTTPException(404, "Audit log not found (no mapping writes recorded yet).")

    jsonl_bytes = ("\n".join(json.dumps(r) for r in records) + "\n").encode("utf-8")
    return StreamingResponse(
        io.BytesIO(jsonl_bytes),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=mapping_audit.jsonl"},
    )
