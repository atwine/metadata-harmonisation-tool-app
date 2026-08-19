from __future__ import annotations
import io
import os
import re
import shutil
from pathlib import Path


ALLOWED_DELETION_ROOTS = ["input", "results", "logs", "preprocess"]


def list_studies() -> list[str]:
    input_path = Path("input")
    if not input_path.exists():
        return []
    return [
        name for name in os.listdir(input_path)
        if (input_path / name).is_dir()
        and not name.startswith(".")
        and not name.startswith("_")
    ]


def sanitise_study_name(raw: str) -> str:
    clean = re.sub(r"[^\w\s\-]", "", raw).strip()
    clean = re.sub(r"\s+", "_", clean)
    if not clean:
        raise ValueError("Study title is empty after sanitisation")
    resolved = (Path("input") / clean).resolve()
    if not str(resolved).startswith(str(Path("input").resolve())):
        raise ValueError("Invalid study name (path traversal detected)")
    return clean


def validate_pdf_magic(content: bytes) -> bool:
    return content[:4] == b"%PDF"


def safe_delete_dir(path: Path) -> bool:
    resolved = path.resolve()
    for root in ALLOWED_DELETION_ROOTS:
        allowed = Path(root).resolve()
        if str(resolved).startswith(str(allowed)) and resolved.exists() and resolved.is_dir():
            shutil.rmtree(resolved)
            return True
    return False


def safe_delete_file(path: Path) -> bool:
    resolved = path.resolve()
    for root in ALLOWED_DELETION_ROOTS:
        allowed = Path(root).resolve()
        if str(resolved).startswith(str(allowed)) and resolved.exists() and resolved.is_file():
            resolved.unlink()
            return True
    return False


def get_study_status(study_name: str) -> str:
    from storage import db

    study_dir = Path("input") / study_name
    recs_path = study_dir / "dataset_variables_with_PID_date_recommendations.csv"

    if not recs_path.exists():
        return "uploaded"

    try:
        total, todo_count = db.count_todo(study_name)
    except Exception:
        return "initialised"

    if total == 0:
        return "initialised"
    if todo_count == total:
        return "initialised"
    if todo_count == 0:
        return "complete"
    return "mapping"


def read_csv_robust(content: str):
    """Parse CSV with automatic delimiter detection via clevercsv, fallback to pandas."""
    try:
        import clevercsv
        dialect = clevercsv.Sniffer().sniff(content[:4096], verbose=False)
        if dialect and dialect.delimiter:
            import pandas as pd
            return pd.read_csv(io.StringIO(content), sep=dialect.delimiter)
    except Exception:
        pass
    import pandas as pd
    return pd.read_csv(io.StringIO(content))
