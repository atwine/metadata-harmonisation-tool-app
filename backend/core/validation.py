"""
Pure validation functions — no Streamlit dependency.
"""
from __future__ import annotations
import pandas as pd


MARKING_OPTIONS = [
    "To do",
    "Successfully mapped",
    "Marked to reconsider",
    "Marked unmappable",
]

RECOMMENDED_CODEBOOK_COLS = {"dType", "Categories", "Unit", "Unit Example"}


def validate_codebook_df(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings). Errors → reject upload; warnings → accept with note."""
    errors: list[str] = []
    warnings: list[str] = []
    cols = set(df.columns)

    if "variable_name" not in cols and "description" not in cols:
        errors.append("CSV must contain 'variable_name' or 'description' column")
        return errors, warnings

    for rec in sorted(RECOMMENDED_CODEBOOK_COLS):
        if rec not in cols:
            warnings.append(f"Recommended column missing: {rec}")

    if "variable_name" in cols:
        dupes = (
            df["variable_name"].astype(str).str.strip().str.casefold()
        )
        dupe_vals = dupes[dupes.duplicated(keep=False)].unique().tolist()
        if dupe_vals:
            warnings.append(f"Duplicate variable_name entries: {dupe_vals[:5]}")

    if "description" in cols:
        dupes_d = (
            df["description"].astype(str).str.strip().str.casefold()
        )
        dupe_vals_d = dupes_d[dupes_d.duplicated(keep=False)].unique().tolist()
        if dupe_vals_d:
            warnings.append(f"Duplicate description entries: {dupe_vals_d[:5]}")

    return errors, warnings


def validate_study_variables_df(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []
    cols = set(df.columns)

    if "variable_name" not in cols:
        errors.append("CSV must contain 'variable_name' column")
        return errors, warnings

    dupes = df["variable_name"].astype(str).str.strip().str.casefold()
    dupe_vals = dupes[dupes.duplicated(keep=False)].unique().tolist()
    if dupe_vals:
        warnings.append(f"Duplicate variable_name entries: {dupe_vals[:5]}")

    return errors, warnings


def sanitise_sql_string(value: str) -> str:
    return str(value).replace("'", "''")
