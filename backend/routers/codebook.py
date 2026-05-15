from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from models.schemas import CodebookUploadResponse, CodebookVariable
from storage.files import read_csv_robust
from core.validation import validate_codebook_df

router = APIRouter()


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
    df.to_csv("input/target_variables.csv", index=False)

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


@router.get("/", response_model=list[CodebookVariable])
async def get_codebook():
    path = Path("input/target_variables.csv")
    if not path.exists():
        raise HTTPException(404, "No codebook uploaded yet")

    try:
        df = pd.read_csv(path)
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
