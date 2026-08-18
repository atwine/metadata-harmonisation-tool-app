import shutil
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from models.schemas import Study, StudyUploadResponse
from storage.files import (
    get_study_status,
    list_studies,
    read_csv_robust,
    sanitise_study_name,
    validate_pdf_magic,
)
from core.validation import validate_study_variables_df

router = APIRouter()


@router.post("/upload", response_model=StudyUploadResponse)
async def upload_study(
    study_title: str = Form(...),
    variables_file: UploadFile = File(...),
    example_data_file: Optional[UploadFile] = File(None),
    context_pdf: Optional[UploadFile] = File(None),
):
    try:
        study_name = sanitise_study_name(study_title)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # Variables CSV
    vars_content = await variables_file.read()
    if len(vars_content) > 10 * 1024 * 1024:
        raise HTTPException(400, "Variables file exceeds 10 MB limit")
    try:
        text = vars_content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(400, "Variables file must be UTF-8 encoded")
    try:
        vars_df = read_csv_robust(text)
    except Exception as e:
        raise HTTPException(400, f"Could not parse variables CSV: {e}")

    errors, warnings = validate_study_variables_df(vars_df)
    if errors:
        raise HTTPException(400, "; ".join(errors))

    # Create study directory and save variables
    study_dir = Path("input") / study_name
    study_dir.mkdir(parents=True, exist_ok=True)
    vars_df.to_csv(study_dir / "dataset_variables.csv", index=False)

    has_example = False
    has_pdf = False

    if example_data_file and example_data_file.filename:
        ex_content = await example_data_file.read()
        if len(ex_content) > 100 * 1024 * 1024:
            raise HTTPException(400, "Example data file exceeds 100 MB limit")
        (study_dir / "example_data.csv").write_bytes(ex_content)
        has_example = True

    if context_pdf and context_pdf.filename:
        pdf_content = await context_pdf.read()
        if len(pdf_content) > 50 * 1024 * 1024:
            raise HTTPException(400, "PDF exceeds 50 MB limit")
        if not validate_pdf_magic(pdf_content):
            raise HTTPException(400, "Uploaded file is not a valid PDF (bad magic bytes)")
        (study_dir / "context.pdf").write_bytes(pdf_content)
        has_pdf = True

    return StudyUploadResponse(
        study_name=study_name,
        variable_count=len(vars_df),
        has_example_data=has_example,
        has_context_pdf=has_pdf,
        warnings=warnings,
    )


@router.get("/", response_model=list[Study])
async def list_studies_endpoint():
    studies: list[Study] = []
    for name in list_studies():
        study_dir = Path("input") / name
        vars_path = study_dir / "dataset_variables.csv"
        var_count = 0
        if vars_path.exists():
            try:
                df = pd.read_csv(vars_path)
                var_count = len(df)
            except Exception:
                pass

        studies.append(
            Study(
                name=name,
                variable_count=var_count,
                has_example_data=(study_dir / "example_data.csv").exists(),
                has_context_pdf=(study_dir / "context.pdf").exists(),
                has_results=(Path("results") / f"{name}.csv").exists(),
                status=get_study_status(name),
            )
        )
    return studies


@router.delete("/{study_name}")
async def delete_study(study_name: str):
    try:
        safe_name = sanitise_study_name(study_name)
    except ValueError as e:
        raise HTTPException(400, str(e))

    allowed_input   = str(Path("input").resolve())
    allowed_results = str(Path("results").resolve())

    study_dir = (Path("input") / safe_name).resolve()
    if not str(study_dir).startswith(allowed_input):
        raise HTTPException(400, "Invalid study name")

    if study_dir.exists():
        shutil.rmtree(study_dir)

    results_file = (Path("results") / f"{safe_name}.csv").resolve()
    if str(results_file).startswith(allowed_results) and results_file.exists():
        results_file.unlink()

    return {"status": "deleted", "study": safe_name}
