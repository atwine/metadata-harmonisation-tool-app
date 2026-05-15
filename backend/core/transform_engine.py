"""
Applies confirmed mappings + transformations to example data and returns a ZIP of CSVs.
"""
from __future__ import annotations
import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from core.transformation_utils import direct_convert, categorical_convert, dtype_cast


def apply_transformations(studies: list[str]) -> tuple[bytes, list[dict]]:
    """
    Returns (zip_bytes, metrics_list).
    metrics_list contains one dict per study with per-variable success/error counts.
    """
    zip_buffer = io.BytesIO()
    all_metrics: list[dict] = []

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for study in studies:
            metrics, csv_bytes = _transform_study(study)
            all_metrics.append({"study": study, "metrics": metrics})
            if csv_bytes:
                zf.writestr(f"{study}_transformed.csv", csv_bytes)

    zip_buffer.seek(0)
    return zip_buffer.read(), all_metrics


def _transform_study(study: str) -> tuple[list[dict], str | None]:
    example_path = Path("input") / study / "example_data.csv"
    mapping_path = Path("results") / f"{study}.csv"
    metrics: list[dict] = []

    if not example_path.exists() or not mapping_path.exists():
        return metrics, None

    try:
        source_df = pd.read_csv(example_path)
        mapping_df = pd.read_csv(mapping_path)
    except Exception:
        return metrics, None

    mapped_rows = mapping_df[mapping_df["marked"] == "Successfully mapped"]
    output_cols: dict[str, list] = {}

    for _, row in mapped_rows.iterrows():
        study_var    = row.get("study_var")
        codebook_var = row.get("codebook_var")
        t_type       = row.get("transformation_type")
        t_instr      = row.get("transformation_instructions")
        src_dtype    = str(row.get("source_dtype") or "string")
        tgt_dtype    = str(row.get("target_dtype") or "string")

        if not study_var or study_var not in source_df.columns:
            metrics.append({
                "variable": study_var,
                "successes": 0,
                "errors": 1,
                "warning": "Source column not found in example data",
            })
            continue

        results: list = []
        errors = 0

        for val in source_df[study_var]:
            try:
                if pd.isna(val):
                    results.append(np.nan)
                    continue
                if t_type == "Direct" and t_instr:
                    results.append(direct_convert(val, str(t_instr), src_dtype, tgt_dtype))
                elif t_type == "Categorical" and t_instr:
                    results.append(categorical_convert(val, str(t_instr)))
                else:
                    results.append(dtype_cast(val, tgt_dtype))
            except Exception:
                results.append(np.nan)
                errors += 1

        col_name = str(codebook_var) if codebook_var else str(study_var)
        output_cols[col_name] = results
        metrics.append({
            "variable": study_var,
            "successes": len(results) - errors,
            "errors": errors,
        })

    if not output_cols:
        return metrics, None

    out_df = pd.DataFrame(output_cols)
    return metrics, out_df.to_csv(index=False)
