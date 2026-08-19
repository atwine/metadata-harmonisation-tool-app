"""
Mappings router — the most complex part of the API.

Key invariant: a study's mapping rows are auto-initialised in SQLite on first
touch if the study has been through Initialise. All rows start as "To do".
"""
from __future__ import annotations
import ast
import datetime
import hashlib
import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from core.transformation_utils import (
    categorical_convert,
    direct_convert,
    validate_expression,
)
from models.schemas import (
    MappingRecord,
    MappingUpdateRequest,
    MappingsListResponse,
    PIDRecommendationItem,
    RecommendationItem,
    StudyVariable,
    TransformationPreviewItem,
    TransformationPreviewRequest,
    TransformationPreviewResponse,
    ValidateExpressionRequest,
    ValidateExpressionResponse,
    VariableDetailResponse,
)
from storage import db
from storage.files import sanitise_study_name

router = APIRouter()

MARKING_OPTIONS = [
    "To do",
    "Successfully mapped",
    "Marked to reconsider",
    "Marked unmappable",
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _ensure_initialised(study: str) -> None:
    """Bulk-creates 'To do' rows for every study variable the first time this
    study is touched, from the Initialise pipeline's PID/date recommendations
    file. No-op if the study already has mapping rows."""
    if db.study_has_any_mappings(study):
        return

    pid_date_path = (
        Path("input") / study / "dataset_variables_with_PID_date_recommendations.csv"
    )
    if not pid_date_path.exists():
        raise HTTPException(
            404,
            f"Study '{study}' has not been initialised. "
            "Run the recommendation engine first.",
        )

    vars_df = pd.read_csv(pid_date_path)
    db.init_mappings_for_study(study, vars_df["variable_name"].astype(str).tolist())


def _none(val) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, float) and np.isnan(val):
        return None
    s = str(val).strip()
    return s if s and s not in ("nan", "None") else None


def _parse_list(val) -> list:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        if not val.strip():
            return []
        try:
            return ast.literal_eval(val)
        except Exception:
            return []
    return []


def _row_to_record(row: dict) -> MappingRecord:
    return MappingRecord(
        study_var=str(row.get("study_var", "")),
        codebook_var=_none(row.get("codebook_var")),
        confidence=_none(row.get("confidence")),
        notes=_none(row.get("notes")),
        marked=str(row.get("marked") or "To do"),
        transformation_instructions=_none(row.get("transformation_instructions")),
        transformation_type=_none(row.get("transformation_type")),
        source_dtype=_none(row.get("source_dtype")),
        target_dtype=_none(row.get("target_dtype")),
        patient_id_var=_none(row.get("patient_id_var")),
        patient_id_confidence=_none(row.get("patient_id_confidence")),
        date_var=_none(row.get("date_var")),
        date_confidence=_none(row.get("date_confidence")),
        afpo_values_mapped=_none(row.get("afpo_values_mapped")),
        afpo_values_gaps=_none(row.get("afpo_values_gaps")),
    )


# ── GET /api/mappings/{study} ─────────────────────────────────────────────────

@router.get("/{study_name}", response_model=MappingsListResponse)
async def get_mappings(
    study_name: str, status: Optional[str] = Query(None)
):
    try:
        study_name = sanitise_study_name(study_name)
    except ValueError as e:
        raise HTTPException(400, str(e))

    _ensure_initialised(study_name)

    # Join best_confidence from recommendations file (for client-side difficulty sort)
    best_conf_map: dict[str, int] = {}
    recs_path = (
        Path("input") / study_name
        / "dataset_variables_with_PID_date_recommendations.csv"
    )
    if recs_path.exists():
        try:
            recs_df = pd.read_csv(recs_path)
            for _, row in recs_df.iterrows():
                dists = _parse_list(row.get("target_distances"))
                if dists:
                    best_conf_map[str(row["variable_name"])] = max(
                        0, min(100, round((1 - float(dists[0])) * 100))
                    )
        except Exception:
            pass

    total, mapped = db.count_mappings(study_name)
    status_filter = status if status in MARKING_OPTIONS else None
    rows = db.list_mappings(study_name, status_filter)

    records = [_row_to_record(r) for r in rows]
    for rec in records:
        rec.best_confidence = best_conf_map.get(rec.study_var)

    return MappingsListResponse(
        study=study_name,
        total=total,
        mapped=mapped,
        progress=round(mapped / total, 3) if total else 0.0,
        records=records,
    )


# ── GET /api/mappings/{study}/variable/{name} ─────────────────────────────────

@router.get("/{study_name}/variable/{variable_name}", response_model=VariableDetailResponse)
async def get_variable_detail(study_name: str, variable_name: str):
    try:
        study_name = sanitise_study_name(study_name)
    except ValueError as e:
        raise HTTPException(400, str(e))

    recs_path = (
        Path("input") / study_name
        / "dataset_variables_with_PID_date_recommendations.csv"
    )
    if not recs_path.exists():
        raise HTTPException(404, "Study not initialised")

    recs_df  = pd.read_csv(recs_path)
    var_rows = recs_df[recs_df["variable_name"] == variable_name]
    if var_rows.empty:
        raise HTTPException(404, f"Variable '{variable_name}' not found")

    row = var_rows.iloc[0]

    variable = StudyVariable(
        variable_name=str(row["variable_name"]),
        description=_none(row.get("description")),
        target_recommendations=_parse_list(row.get("target_recommendations")),
        target_distances=_parse_list(row.get("target_distances")),
        PID_recommendations=_parse_list(row.get("PID_recommendations")),
        PID_distances=_parse_list(row.get("PID_distances")),
        date_recommendations=_parse_list(row.get("date_recommendations")),
        date_distances=_parse_list(row.get("date_distances")),
    )

    # Example data for this variable
    example_data: list[str] = []
    ex_path = Path("input") / study_name / "example_data.csv"
    if ex_path.exists():
        try:
            ex_df = pd.read_csv(ex_path)
            if variable_name in ex_df.columns:
                example_data = (
                    ex_df[variable_name].dropna().astype(str).head(10).tolist()
                )
        except Exception:
            pass

    # Codebook description → variable_name lookup
    desc_to_var: dict[str, str] = {}
    cb_path = Path("input/target_variables.csv")
    if cb_path.exists():
        try:
            cb_df = pd.read_csv(cb_path)
            for _, cb_row in cb_df.iterrows():
                desc_to_var[str(cb_row.get("description", ""))] = str(
                    cb_row.get("variable_name", "")
                )
        except Exception:
            pass

    # Build recommendations list (top 10)
    target_recs  = _parse_list(row.get("target_recommendations"))
    target_dists = _parse_list(row.get("target_distances"))
    recommendations: list[RecommendationItem] = []
    for desc, dist in zip(target_recs[:10], target_dists[:10]):
        confidence   = max(0, min(100, round((1 - float(dist)) * 100)))
        var_for_rec  = desc_to_var.get(str(desc), str(desc))
        recommendations.append(
            RecommendationItem(
                codebook_var=var_for_rec,
                description=str(desc),
                confidence=confidence,
            )
        )

    # PID recommendations (top 5)
    pid_recs  = _parse_list(row.get("PID_recommendations"))
    pid_dists = _parse_list(row.get("PID_distances"))
    pid_recommendations: list[PIDRecommendationItem] = [
        PIDRecommendationItem(
            variable_name=str(v),
            confidence=max(0, min(100, round((1 - float(d)) * 100))),
        )
        for v, d in zip(pid_recs[:5], pid_dists[:5])
    ]

    # Date recommendations (top 5)
    date_recs  = _parse_list(row.get("date_recommendations"))
    date_dists = _parse_list(row.get("date_distances"))
    date_recommendations: list[PIDRecommendationItem] = [
        PIDRecommendationItem(
            variable_name=str(v),
            confidence=max(0, min(100, round((1 - float(d)) * 100))),
        )
        for v, d in zip(date_recs[:5], date_dists[:5])
    ]

    # Existing mapping from SQLite
    _ensure_initialised(study_name)
    existing_row = db.get_mapping(study_name, variable_name)
    existing_mapping = (
        _row_to_record(existing_row)
        if existing_row is not None
        else MappingRecord(study_var=variable_name)
    )

    # Already-used codebook vars (exclude this variable's own saved value)
    already_used_codebook_vars = db.already_used_codebook_vars(study_name, variable_name)

    return VariableDetailResponse(
        variable=variable,
        example_data=example_data,
        recommendations=recommendations,
        pid_recommendations=pid_recommendations,
        date_recommendations=date_recommendations,
        existing_mapping=existing_mapping,
        already_used_codebook_vars=already_used_codebook_vars,
    )


# ── PUT /api/mappings/{study}/variable/{name} ─────────────────────────────────

@router.put("/{study_name}/variable/{variable_name}", response_model=MappingRecord)
async def save_mapping(
    study_name: str, variable_name: str, body: MappingUpdateRequest
):
    try:
        study_name = sanitise_study_name(study_name)
    except ValueError as e:
        raise HTTPException(400, str(e))

    _ensure_initialised(study_name)

    prev_row = db.get_mapping(study_name, variable_name)
    previous = _row_to_record(prev_row).model_dump() if prev_row is not None else None

    # AfPO results are only recomputed when the frontend actually re-ran the
    # lookup in this request. If the field is omitted (e.g. the user reopened
    # an already-mapped variable and resubmitted after only touching Notes,
    # without re-running "Look up in AfPO"), keep whatever was saved before
    # instead of silently wiping it back to empty.
    afpo_values_mapped = (
        json.dumps(body.afpo_values_mapped) if body.afpo_values_mapped is not None
        else (previous["afpo_values_mapped"] if previous and previous.get("afpo_values_mapped") else json.dumps({}))
    )
    afpo_values_gaps = (
        json.dumps(body.afpo_values_gaps) if body.afpo_values_gaps is not None
        else (previous["afpo_values_gaps"] if previous and previous.get("afpo_values_gaps") else json.dumps([]))
    )

    new_record = {
        "study_var":                   variable_name,
        "codebook_var":                body.codebook_var,
        "confidence":                  None,
        "notes":                       body.notes[:500] if body.notes else None,
        "marked":                      body.marked,
        "transformation_instructions": (
            body.transformation_instructions[:500]
            if body.transformation_instructions
            else None
        ),
        "transformation_type":         body.transformation_type,
        "source_dtype":                body.source_dtype,
        "target_dtype":                body.target_dtype,
        "patient_id_var":              body.patient_id_var,
        "patient_id_confidence":       None,
        "date_var":                    body.date_var,
        "date_confidence":             None,
        "afpo_values_mapped":          afpo_values_mapped,
        "afpo_values_gaps":            afpo_values_gaps,
    }

    db.upsert_mapping(study_name, variable_name, new_record)
    _write_audit(study_name, variable_name, body, new_record, previous)

    return MappingRecord(**new_record)


def _write_audit(
    study_name: str,
    variable_name: str,
    body: MappingUpdateRequest,
    new_record: dict,
    previous,
):
    t_instr = body.transformation_instructions or ""
    t_hash  = hashlib.sha256(t_instr.encode()).hexdigest() if t_instr else None

    db.append_audit({
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
        "study":     study_name,
        "study_var": variable_name,
        "operator":  body.operator_name,
        "codebook_var":        body.codebook_var,
        "marked":              body.marked,
        "notes":               body.notes,
        "transformation_type": body.transformation_type,
        "transformation_instructions_sha256": t_hash,
        "previous": previous,
        "new":      new_record,
    })


# ── PUT /api/mappings/{study}/variable/{name}/reopen ─────────────────────────

@router.put("/{study_name}/variable/{variable_name}/reopen")
async def reopen_mapping(study_name: str, variable_name: str):
    try:
        study_name = sanitise_study_name(study_name)
    except ValueError as e:
        raise HTTPException(400, str(e))

    _ensure_initialised(study_name)
    if not db.reopen_mapping(study_name, variable_name):
        raise HTTPException(404, f"Variable '{variable_name}' not found in results")
    return {"status": "reopened", "study_var": variable_name}


# ── GET /api/mappings/{study}/audit ──────────────────────────────────────────

@router.get("/{study_name}/audit")
async def get_audit(study_name: str, n: int = Query(10, ge=1, le=100)):
    try:
        study_name = sanitise_study_name(study_name)
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {"records": db.get_audit(study_name, n)}


# ── POST /api/mappings/preview-transformation ─────────────────────────────────

@router.post("/preview-transformation", response_model=TransformationPreviewResponse)
async def preview_transformation(body: TransformationPreviewRequest):
    preview:     list[TransformationPreviewItem] = []
    blank_count: int = 0

    try:
        for val in body.example_data:
            try:
                if body.transformation_type == "Direct":
                    result = direct_convert(
                        val,
                        body.transformation_instructions,
                        body.source_dtype,
                        body.target_dtype,
                    )
                else:
                    result = categorical_convert(val, body.transformation_instructions)

                if result is None or (isinstance(result, float) and np.isnan(result)):
                    preview.append(TransformationPreviewItem(original=str(val), transformed=""))
                    blank_count += 1
                else:
                    preview.append(
                        TransformationPreviewItem(
                            original=str(val), transformed=str(result)
                        )
                    )
            except Exception:
                preview.append(TransformationPreviewItem(original=str(val), transformed=""))
                blank_count += 1

        return TransformationPreviewResponse(
            preview=preview,
            transformed_count=len(preview) - blank_count,
            blank_count=blank_count,
            valid=True,
            error=None,
        )
    except Exception as e:
        return TransformationPreviewResponse(
            preview=[],
            transformed_count=0,
            blank_count=0,
            valid=False,
            error=str(e),
        )


# ── POST /api/mappings/validate-expression ────────────────────────────────────

@router.post("/validate-expression", response_model=ValidateExpressionResponse)
async def validate_expr(body: ValidateExpressionRequest):
    valid, message = validate_expression(body.expression)
    return ValidateExpressionResponse(valid=valid, message=message)
