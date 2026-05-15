import datetime
import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from models.schemas import CodebookUploadResponse, CodebookVariable
from storage.files import read_csv_robust
from core.validation import validate_codebook_df

router = APIRouter()

_META_PATH = Path("input/target_variables_meta.json")
_CSV_PATH  = Path("input/target_variables.csv")


@router.post("/upload", response_model=CodebookUploadResponse)
async def upload_codebook(file: UploadFile = File(...)):
    content = await file.read()

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "File exceeds 10 MB limit")

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(400, "File must be UTF-8 encoded")

    try:
        df = read_csv_robust(text)
    except Exception as e:
        raise HTTPException(400, f"Could not parse CSV: {e}")

    errors, warnings = validate_codebook_df(df)
    if errors:
        raise HTTPException(400, "; ".join(errors))

    Path("input").mkdir(exist_ok=True)
    df.to_csv(_CSV_PATH, index=False)

    # Persist upload metadata for the info banner
    _META_PATH.write_text(
        json.dumps({
            "filename":    file.filename or "codebook.csv",
            "row_count":   len(df),
            "uploaded_at": datetime.datetime.utcnow().isoformat() + "Z",
        }),
        encoding="utf-8",
    )

    # Invalidate embeddings cache so the next Initialise re-embeds
    emb_path = Path("input/target_variables_with_embeddings.csv")
    if emb_path.exists():
        emb_path.unlink()

    return CodebookUploadResponse(
        status="ok",
        row_count=len(df),
        columns=list(df.columns),
        warnings=warnings,
    )


@router.get("/meta")
async def get_codebook_meta():
    if not _CSV_PATH.exists():
        return {"exists": False}
    meta: dict = {"exists": True}
    if _META_PATH.exists():
        try:
            meta.update(json.loads(_META_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
    if "row_count" not in meta:
        try:
            meta["row_count"] = len(pd.read_csv(_CSV_PATH))
        except Exception:
            meta["row_count"] = 0
    if "filename" not in meta:
        meta["filename"] = "target_variables.csv"
    return meta


@router.get("/", response_model=list[CodebookVariable])
async def get_codebook():
    if not _CSV_PATH.exists():
        raise HTTPException(404, "No codebook uploaded yet")

    try:
        df = pd.read_csv(_CSV_PATH)
    except Exception as e:
        raise HTTPException(500, f"Could not read codebook: {e}")

    def _get(row, *keys) -> str | None:
        for k in keys:
            v = row.get(k)
            if v is not None and str(v).strip() not in ("", "nan", "None"):
                return str(v).strip()
        return None

    records: list[CodebookVariable] = []
    for _, row in df.iterrows():
        records.append(
            CodebookVariable(
                variable_name=str(row.get("variable_name", "")),
                description=str(row.get("description", "")),
                dType=_get(row, "dType"),
                unit=_get(row, "Unit", "unit"),
                categories=_get(row, "Categories", "categories"),
                unit_example=_get(row, "Unit Example", "unit_example"),
            )
        )
    return records
