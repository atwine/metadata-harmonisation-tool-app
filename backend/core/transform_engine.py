"""
Applies confirmed mappings + transformations to example data and returns a ZIP of CSVs.
Mirrors the reference Streamlit app's download package (app/components/transform_engine.py
and download.py): per study, the ZIP contains original_data.csv, {study}_transformed.csv,
mapping_summary.csv and validation_report.txt/summary.txt — not just the transformed CSV.
"""
from __future__ import annotations
import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from core.transformation_utils import direct_convert, categorical_convert, dtype_cast
from storage import db


def apply_transformations(studies: list[str]) -> tuple[bytes, list[dict]]:
    """
    Returns (zip_bytes, results_list).
    results_list contains one dict per study: {"study", "status", "reason"?, "metrics"?}.
    status is "ok" or "skipped" (with a human-readable "reason").
    A study is namespaced under its own folder in the ZIP so multiple studies can be
    exported together without filename collisions.
    """
    zip_buffer = io.BytesIO()
    results: list[dict] = []

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for study in studies:
            outcome = _transform_study(study)
            results.append({k: v for k, v in outcome.items() if k != "files"})
            for filename, content in outcome.get("files", {}).items():
                zf.writestr(f"{study}/{filename}", content)

        skipped = [r for r in results if r["status"] == "skipped"]
        if skipped:
            lines = ["Studies skipped from this export:", ""]
            for r in skipped:
                lines.append(f"- {r['study']}: {r['reason']}")
            zf.writestr("SKIPPED.txt", "\n".join(lines))

    zip_buffer.seek(0)
    return zip_buffer.read(), results


def _transform_study(study: str) -> dict:
    example_path = Path("input") / study / "example_data.csv"

    if not db.study_has_any_mappings(study):
        return {"study": study, "status": "skipped", "reason": "No mapping results yet"}
    if not example_path.exists():
        return {
            "study": study,
            "status": "skipped",
            "reason": "No example_data.csv (metadata-only study) — use the mapping CSV export instead",
        }

    try:
        source_df = pd.read_csv(example_path)
        mapping_df = pd.DataFrame(db.list_mappings(study))
    except Exception as e:
        return {"study": study, "status": "skipped", "reason": f"Could not read source/mapping data: {e}"}

    mapped_rows = mapping_df[mapping_df["marked"].astype(str).str.strip() == "Successfully mapped"]
    output_cols: dict[str, list] = {}
    col_owner: dict[str, str] = {}  # codebook column name -> the study_var that claimed it
    metrics: list[dict] = []
    warnings: list[str] = []

    for _, row in mapped_rows.iterrows():
        study_var    = row.get("study_var")
        codebook_var = row.get("codebook_var")
        t_type       = row.get("transformation_type")
        t_instr      = row.get("transformation_instructions")
        src_dtype    = str(row.get("source_dtype") or "string")
        tgt_dtype    = str(row.get("target_dtype") or "string")

        if not study_var or study_var not in source_df.columns:
            warnings.append(f"Source column missing: {study_var}")
            metrics.append({"variable": study_var, "successes": 0, "errors": 1, "warning": "Source column not found in example data"})
            continue

        col_name = str(codebook_var) if codebook_var else str(study_var)
        if col_name in output_cols:
            # Two study variables mapped to the same codebook column would
            # otherwise silently overwrite each other in the output — keep
            # whichever was mapped first and surface the conflict instead.
            warnings.append(
                f"Skipped '{study_var}': codebook column '{col_name}' is already filled by "
                f"'{col_owner[col_name]}' — two variables can't map to the same output column."
            )
            metrics.append({
                "variable": study_var,
                "successes": 0,
                "errors": 1,
                "warning": f"Duplicate mapping to '{col_name}' (kept '{col_owner[col_name]}' instead)",
            })
            continue

        results_col: list = []
        errors = 0
        has_instr = isinstance(t_instr, str) and t_instr.strip()

        if not has_instr:
            warnings.append(f"No transformation for {study_var} -> {codebook_var}; copied through.")

        for val in source_df[study_var]:
            try:
                if pd.isna(val):
                    results_col.append(np.nan)
                    continue
                if not has_instr:
                    results_col.append(dtype_cast(val, tgt_dtype))
                elif t_type == "Direct":
                    results_col.append(direct_convert(val, str(t_instr), src_dtype, tgt_dtype))
                elif t_type == "Categorical":
                    results_col.append(categorical_convert(val, str(t_instr)))
                else:
                    warnings.append(f"Unknown transformation type for {study_var}: {t_type}; copied through.")
                    results_col.append(dtype_cast(val, tgt_dtype))
            except Exception:
                results_col.append(np.nan)
                errors += 1

        output_cols[col_name] = results_col
        col_owner[col_name] = study_var
        metrics.append({
            "variable": study_var,
            "successes": len(results_col) - errors,
            "errors": errors,
        })

    if not output_cols:
        return {"study": study, "status": "skipped", "reason": "No variables marked 'Successfully mapped' with usable data"}

    transformed_df = pd.DataFrame(output_cols)

    total_success = sum(m["successes"] for m in metrics)
    total_errors  = sum(m["errors"] for m in metrics)
    total_records = total_success + total_errors
    success_rate  = (100.0 * total_success / total_records) if total_records else 0.0

    summary_lines = [
        f"Study: {study}",
        f"Variables processed: {len(metrics)}",
        f"Total records processed: {total_records}",
        f"Successes: {total_success}",
        f"Errors: {total_errors}",
        f"Success rate: {success_rate:.2f}%",
    ]
    if warnings:
        summary_lines += ["", "Warnings:"] + [f"- {w}" for w in warnings]

    validation_lines = ["Validation Report", "=================", ""]
    for m in metrics:
        validation_lines.append(f"- {m['variable']}: success={m['successes']}, errors={m['errors']}")
    validation_lines += ["", f"Total successes: {total_success}", f"Total errors: {total_errors}"]
    if warnings:
        validation_lines += ["", "Warnings:"] + [f"- {w}" for w in warnings]

    summary_cols = [c for c in [
        "study_var", "codebook_var", "confidence", "marked",
        "transformation_type", "source_dtype", "target_dtype", "transformation_instructions",
    ] if c in mapping_df.columns]

    files = {
        "original_data.csv": source_df.to_csv(index=False),
        f"{study}_transformed.csv": transformed_df.to_csv(index=False),
        "mapping_summary.csv": mapping_df[summary_cols].to_csv(index=False),
        "validation_report.txt": "\n".join(validation_lines),
        "summary.txt": "\n".join(summary_lines),
    }

    return {"study": study, "status": "ok", "metrics": metrics, "files": files}
