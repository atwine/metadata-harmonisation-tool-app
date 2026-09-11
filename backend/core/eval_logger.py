"""
Automated benchmark logging for the evaluation testing build only.

Gated entirely by the EVAL_BUILD env var — every function here is a no-op
when it's unset, so this module is harmless even if it ever ends up outside
the eval branch. Implements the automated-logging design from
docs/Metadata_Harmonisation_Tool_evaluation_plan.md section 3.2.4.

Captures performance numbers only (timings, hardware, memory, file sizes,
model names) — never the content of a participant's data. No variable
names, no data values, no PDF text ever get written here.

Output: one JSON object per line, appended to logs/benchmark_log.jsonl.
"""
from __future__ import annotations
import datetime
import json
import os
import platform
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

LOG_PATH = Path("logs") / "benchmark_log.jsonl"


def is_eval_build() -> bool:
    return os.environ.get("EVAL_BUILD", "").strip().lower() in ("1", "true", "yes")


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def log_event(event: str, **fields: Any) -> None:
    """Append one event to the benchmark log. No-op unless EVAL_BUILD is set."""
    if not is_eval_build():
        return
    LOG_PATH.parent.mkdir(exist_ok=True)
    record = {"event": event, "timestamp": _now(), **fields}
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _peak_memory_mb() -> Optional[float]:
    """Current RSS, sampled at the point this is called — an approximation of
    peak, not a true high-water mark (matches the doc's stated approach)."""
    try:
        import psutil
        return round(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024), 1)
    except Exception:
        return None


def log_hardware_profile() -> None:
    """Logged once at backend startup — CPU, RAM, GPU (best-effort), OS, Python version."""
    if not is_eval_build():
        return

    ram_gb = None
    try:
        import psutil
        ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 1)
    except Exception:
        pass

    gpu = None
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=3,
        )
        if out.returncode == 0 and out.stdout.strip():
            gpu = out.stdout.strip().splitlines()[0]
    except Exception:
        pass  # no NVIDIA GPU, or nvidia-smi not on PATH — leave as None

    log_event(
        "hardware_profile",
        cpu=platform.processor() or platform.machine() or "unknown",
        cores=os.cpu_count(),
        ram_gb=ram_gb,
        gpu=gpu,
        os=f"{platform.system()} {platform.release()}",
        python=platform.python_version(),
    )


def log_ai_config(ai_config) -> None:
    """Logs which provider/model was selected for a pipeline run — never the
    api_key. ai_config is the AIConfig pydantic model from a request body."""
    if not is_eval_build():
        return
    log_event(
        "ai_config",
        chat_provider=ai_config.chat.provider,
        chat_model=ai_config.chat.model,
        embedding_provider=ai_config.embedding.provider if ai_config.embedding else None,
        embedding_model=ai_config.embedding.model if ai_config.embedding else None,
    )


def log_variable_counts(study: str, n_study_vars: int, n_codebook_vars: int) -> None:
    if not is_eval_build():
        return
    log_event(
        "variable_counts",
        study=study,
        n_study_vars=n_study_vars,
        n_codebook_vars=n_codebook_vars,
    )


@contextmanager
def stage_timer(stage: str, **context: Any) -> Iterator[None]:
    """Wraps one pipeline stage. Logs stage_start, then stage_end with
    duration + memory on success, or stage_error with the exception message
    on failure (re-raised either way). A plain no-op pass-through when
    EVAL_BUILD is unset — costs nothing in the production build."""
    if not is_eval_build():
        yield
        return

    log_event("stage_start", stage=stage, **context)
    start = time.perf_counter()
    try:
        yield
    except Exception as e:
        log_event("stage_error", stage=stage, error=str(e))
        raise
    else:
        log_event(
            "stage_end",
            stage=stage,
            duration_seconds=round(time.perf_counter() - start, 3),
            peak_memory_mb=_peak_memory_mb(),
        )
