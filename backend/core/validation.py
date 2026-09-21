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
REQUIRED_CODEBOOK_COLS = ("variable_name", "description")
REQUIRED_STUDY_COLS = ("variable_name",)


def _near_match(name: str, columns) -> str | None:
    """A column that differs from `name` only by case, spacing or a space
    where the underscore belongs (e.g. 'Variable Name') — the usual reason a
    required column looks 'missing' when it's really there."""
    def norm(s) -> str:
        return str(s).strip().lower().replace(" ", "_")
    return next((c for c in columns if c != name and norm(c) == name), None)


def _missing_columns_error(kind: str, missing: list[str], columns) -> str:
    """One message naming exactly which required column(s) are absent."""
    parts = []
    for name in missing:
        near = _near_match(name, columns)
        hint = f" (found '{near}' — names must match exactly, including capitalisation)" if near else ""
        parts.append(f"'{name}'{hint}")
    label = "column" if len(missing) == 1 else "columns"
    return f"{kind} is missing required {label}: {', '.join(parts)}"


def validate_codebook_df(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings). Errors → reject upload; warnings → accept with note."""
    errors: list[str] = []
    warnings: list[str] = []
    cols = set(df.columns)

    missing = [c for c in REQUIRED_CODEBOOK_COLS if c not in cols]
    if missing:
        errors.append(_missing_columns_error("Codebook", missing, df.columns))
        return errors, warnings

    for rec in sorted(RECOMMENDED_CODEBOOK_COLS):
        if rec not in cols:
            warnings.append(f"Recommended column missing: {rec}")

    dupes = df["variable_name"].astype(str).str.strip().str.casefold()
    dupe_vals = dupes[dupes.duplicated(keep=False)].unique().tolist()
    if dupe_vals:
        warnings.append(f"Duplicate variable_name entries: {dupe_vals[:5]}")

    dupes_d = df["description"].astype(str).str.strip().str.casefold()
    dupe_vals_d = dupes_d[dupes_d.duplicated(keep=False)].unique().tolist()
    if dupe_vals_d:
        warnings.append(f"Duplicate description entries: {dupe_vals_d[:5]}")

    return errors, warnings


def validate_study_variables_df(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []
    cols = set(df.columns)

    missing = [c for c in REQUIRED_STUDY_COLS if c not in cols]
    if missing:
        errors.append(_missing_columns_error("Study variables file", missing, df.columns))
        return errors, warnings

    dupes = df["variable_name"].astype(str).str.strip().str.casefold()
    dupe_vals = dupes[dupes.duplicated(keep=False)].unique().tolist()
    if dupe_vals:
        warnings.append(f"Duplicate variable_name entries: {dupe_vals[:5]}")

    return errors, warnings


def sanitise_sql_string(value: str) -> str:
    return str(value).replace("'", "''")
