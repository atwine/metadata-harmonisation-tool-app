"""
SQLite-backed storage for the three "hot path" record types that used to be
plain CSV/JSONL files: per-study mapping decisions, the mapping audit trail,
and the AfPO gap log. Everything else (uploaded studies, example data,
generated descriptions/embeddings/recommendations, the AfPO ontology file)
stays as plain files — those are write-once/read-a-few-times, not the thing
that was getting re-read and rewritten in full on every single click.

One file (db/app.db), no separate server process, safe for a single local
instance. WAL mode lets reads proceed while a write is in progress.
"""
from __future__ import annotations
import datetime
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

DB_PATH = Path("db") / "app.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS mappings (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    study                           TEXT NOT NULL,
    study_var                       TEXT NOT NULL,
    codebook_var                    TEXT,
    confidence                      TEXT,
    notes                           TEXT,
    marked                          TEXT NOT NULL DEFAULT 'To do',
    transformation_instructions     TEXT,
    transformation_type             TEXT,
    source_dtype                    TEXT,
    target_dtype                    TEXT,
    patient_id_var                  TEXT,
    patient_id_confidence           TEXT,
    date_var                        TEXT,
    date_confidence                 TEXT,
    afpo_values_mapped              TEXT NOT NULL DEFAULT '{}',
    afpo_values_gaps                TEXT NOT NULL DEFAULT '[]',
    updated_at                      TEXT NOT NULL,
    UNIQUE (study, study_var)
);
CREATE INDEX IF NOT EXISTS idx_mappings_study        ON mappings (study);
CREATE INDEX IF NOT EXISTS idx_mappings_study_marked ON mappings (study, marked);

CREATE TABLE IF NOT EXISTS audit_log (
    id                                   INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp                            TEXT NOT NULL,
    study                                TEXT NOT NULL,
    study_var                            TEXT NOT NULL,
    operator                             TEXT,
    codebook_var                         TEXT,
    marked                               TEXT,
    notes                                TEXT,
    transformation_type                  TEXT,
    transformation_instructions_sha256   TEXT,
    previous                             TEXT,
    new                                  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_study ON audit_log (study, id);

CREATE TABLE IF NOT EXISTS afpo_gaps (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp               TEXT NOT NULL,
    study                    TEXT NOT NULL,
    variable_name            TEXT NOT NULL,
    unmatched_value          TEXT NOT NULL,
    submitted_to_github      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_afpo_gaps_value ON afpo_gaps (unmatched_value, submitted_to_github);
"""


def init_db() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    with get_connection() as conn:
        conn.executescript(_SCHEMA)


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ── Mappings ─────────────────────────────────────────────────────────────────

_MAPPING_COLS = [
    "study_var", "codebook_var", "confidence", "notes", "marked",
    "transformation_instructions", "transformation_type", "source_dtype",
    "target_dtype", "patient_id_var", "patient_id_confidence", "date_var",
    "date_confidence", "afpo_values_mapped", "afpo_values_gaps",
]


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def study_has_any_mappings(study: str) -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT 1 FROM mappings WHERE study = ? LIMIT 1", (study,)).fetchone()
        return row is not None


def study_has_mapped_variable(study: str) -> bool:
    """True if at least one variable is marked 'Successfully mapped' — the one
    thing the transformed-data export actually requires."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM mappings WHERE study = ? AND marked = 'Successfully mapped' LIMIT 1",
            (study,),
        ).fetchone()
        return row is not None


def init_mappings_for_study(study: str, study_vars: list[str]) -> None:
    """Bulk-insert a fresh 'To do' row per variable — mirrors the old
    _load_or_init_results CSV-init path, but only runs once (UNIQUE constraint
    makes re-running a no-op via INSERT OR IGNORE)."""
    now = _now()
    with get_connection() as conn:
        conn.executemany(
            """INSERT OR IGNORE INTO mappings (study, study_var, marked, updated_at)
               VALUES (?, ?, 'To do', ?)""",
            [(study, v, now) for v in study_vars],
        )


def list_mappings(study: str, status: Optional[str] = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM mappings WHERE study = ? AND marked = ? ORDER BY id",
                (study, status),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM mappings WHERE study = ? ORDER BY id", (study,)
            ).fetchall()
        return [row_to_dict(r) for r in rows]


def count_mappings(study: str) -> tuple[int, int]:
    """Returns (total, mapped) where mapped = anything not 'To do'."""
    with get_connection() as conn:
        row = conn.execute(
            """SELECT COUNT(*) AS total,
                      SUM(CASE WHEN marked != 'To do' THEN 1 ELSE 0 END) AS mapped
               FROM mappings WHERE study = ?""",
            (study,),
        ).fetchone()
        return row["total"] or 0, row["mapped"] or 0


def count_todo(study: str) -> tuple[int, int]:
    """Returns (total, todo_count) — used to derive a study's overall status
    (initialised / mapping / complete) without a full-table scan."""
    with get_connection() as conn:
        row = conn.execute(
            """SELECT COUNT(*) AS total,
                      SUM(CASE WHEN marked = 'To do' THEN 1 ELSE 0 END) AS todo
               FROM mappings WHERE study = ?""",
            (study,),
        ).fetchone()
        return row["total"] or 0, row["todo"] or 0


def get_mapping(study: str, study_var: str) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM mappings WHERE study = ? AND study_var = ?",
            (study, study_var),
        ).fetchone()
        return row_to_dict(row) if row else None


def already_used_codebook_vars(study: str, exclude_study_var: str) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT DISTINCT codebook_var FROM mappings
               WHERE study = ? AND study_var != ?
                 AND marked IN ('Successfully mapped', 'Marked to reconsider')
                 AND codebook_var IS NOT NULL AND codebook_var != ''""",
            (study, exclude_study_var),
        ).fetchall()
        return [r["codebook_var"] for r in rows]


def upsert_mapping(study: str, study_var: str, values: dict[str, Any]) -> dict[str, Any]:
    now = _now()
    record = {c: values.get(c) for c in _MAPPING_COLS}
    record["study_var"] = study_var
    with get_connection() as conn:
        conn.execute(
            f"""INSERT INTO mappings (study, {", ".join(_MAPPING_COLS)}, updated_at)
                VALUES (:study, {", ".join(":" + c for c in _MAPPING_COLS)}, :updated_at)
                ON CONFLICT (study, study_var) DO UPDATE SET
                    {", ".join(f"{c} = excluded.{c}" for c in _MAPPING_COLS if c != "study_var")},
                    updated_at = excluded.updated_at""",
            {**record, "study": study, "updated_at": now},
        )
    return get_mapping(study, study_var)  # type: ignore[return-value]


def reopen_mapping(study: str, study_var: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE mappings SET marked = 'To do', updated_at = ? WHERE study = ? AND study_var = ?",
            (_now(), study, study_var),
        )
        return cur.rowcount > 0


def all_mappings_for_export(study: str) -> list[dict[str, Any]]:
    """Most-recently-touched first — matches the old CSV's drop+re-append
    upsert behaviour once reversed for display."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM mappings WHERE study = ? ORDER BY updated_at DESC, id DESC",
            (study,),
        ).fetchall()
        return [row_to_dict(r) for r in rows]


# ── Audit log ────────────────────────────────────────────────────────────────

def append_audit(entry: dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO audit_log
               (timestamp, study, study_var, operator, codebook_var, marked, notes,
                transformation_type, transformation_instructions_sha256, previous, new)
               VALUES (:timestamp, :study, :study_var, :operator, :codebook_var, :marked,
                       :notes, :transformation_type, :transformation_instructions_sha256,
                       :previous, :new)""",
            {
                **entry,
                "previous": json.dumps(entry.get("previous")) if entry.get("previous") is not None else None,
                "new": json.dumps(entry["new"]),
            },
        )


def get_all_audit() -> list[dict[str, Any]]:
    """Every audit record, all studies — used for the full audit-log download."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM audit_log ORDER BY id").fetchall()
        records = [row_to_dict(r) for r in rows]
        for r in records:
            r["previous"] = json.loads(r["previous"]) if r["previous"] else None
            r["new"] = json.loads(r["new"])
            del r["id"]
        return records


def get_audit(study: str, n: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_log WHERE study = ? ORDER BY id DESC LIMIT ?",
            (study, n),
        ).fetchall()
        records = [row_to_dict(r) for r in rows]
        for r in records:
            r["previous"] = json.loads(r["previous"]) if r["previous"] else None
            r["new"] = json.loads(r["new"])
            del r["id"]
        records.reverse()  # oldest of the batch first, matching the old file's tail(-n) order
        return records


# ── AfPO gaps ────────────────────────────────────────────────────────────────

def log_afpo_gaps(study: str, variable_name: str, values: list[str]) -> None:
    if not values:
        return
    now = _now()
    with get_connection() as conn:
        conn.executemany(
            """INSERT INTO afpo_gaps (timestamp, study, variable_name, unmatched_value, submitted_to_github)
               VALUES (?, ?, ?, ?, 0)""",
            [(now, study, variable_name, v) for v in values],
        )


def load_submitted_afpo_values() -> dict[str, str]:
    """Returns {normalised_value: latest_timestamp} for every value ever
    marked submitted, across all studies/variables."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT LOWER(TRIM(unmatched_value)) AS key, MAX(timestamp) AS ts
               FROM afpo_gaps WHERE submitted_to_github = 1
               GROUP BY LOWER(TRIM(unmatched_value))"""
        ).fetchall()
        return {r["key"]: r["ts"] for r in rows}


def mark_afpo_gap_submitted(study: str, variable_name: str, value: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            """SELECT id FROM afpo_gaps
               WHERE study = ? AND variable_name = ? AND unmatched_value = ? AND submitted_to_github = 0
               ORDER BY id DESC LIMIT 1""",
            (study, variable_name, value),
        ).fetchone()
        if row is None:
            return False
        conn.execute("UPDATE afpo_gaps SET submitted_to_github = 1 WHERE id = ?", (row["id"],))
        return True
