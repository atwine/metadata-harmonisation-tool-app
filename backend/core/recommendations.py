"""
Recommendation engine — Phases 1, 3, 4, 5.
Phase 2 (descriptions) lives in descriptions.py.

All functions are idempotent: they check for existing output files and skip
unless force_rerun=True.
"""
from __future__ import annotations
import ast
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pandas as pd


# ── Phase 1: PDF → Text ──────────────────────────────────────────────────────

def convert_pdf_to_txt():
    from storage.files import list_studies
    from pdfminer.high_level import extract_text

    for study in list_studies():
        pdf_path = Path(f"input/{study}/context.pdf")
        txt_path = Path(f"input/{study}/context.txt")
        if pdf_path.exists() and not txt_path.exists():
            try:
                text = extract_text(str(pdf_path))
                txt_path.write_text(text, encoding="utf-8")
            except Exception as e:
                print(f"[pdf_conversion] Failed for {study}: {e}")


# ── Text chunking helpers (shared with descriptions.py) ─────────────────────

def split_text(text: str, chunk_size: int = 1000) -> list[str]:
    chunks: list[str] = []
    while text:
        if len(text) <= chunk_size:
            chunks.append(text)
            break
        pos = text.rfind(" ", 0, chunk_size)
        if pos == -1:
            pos = chunk_size
        chunks.append(text[:pos])
        text = text[pos:].lstrip()
    return chunks


def get_relevant_context(
    var_name: str,
    chunks: list[str],
    chunk_embeddings: list,
    embed_fn: Callable,
) -> str:
    if not chunks or not chunk_embeddings:
        return "Not available"
    from scipy.spatial.distance import cosine
    var_emb = embed_fn(var_name)
    if not var_emb:
        return "Not available"
    distances = [cosine(var_emb, e) for e in chunk_embeddings]
    return chunks[distances.index(min(distances))]


# ── Phase 3: Embedding generation ────────────────────────────────────────────

def embed_dataframe(df: pd.DataFrame, embed_fn: Callable) -> pd.DataFrame:
    """Embed variable_name and description columns, deduplicating API calls."""
    all_texts = pd.unique(
        pd.concat([df["variable_name"].astype(str), df["description"].astype(str)])
    )
    embed_map = {t: embed_fn(t) for t in all_texts if str(t).strip()}
    df = df.copy()
    df["var_embeddings"]         = df["variable_name"].astype(str).map(embed_map)
    df["description_embeddings"] = df["description"].astype(str).map(embed_map)
    return df


def get_embeddings(
    ai_config,
    force_rerun: bool = False,
    progress_cb: Optional[Callable[[str], None]] = None,
):
    from storage.files import list_studies
    from core.ai_provider import AIProviderWrapper

    wrapper  = AIProviderWrapper(ai_config)
    embed_fn = wrapper.generate_embedding

    # Embed codebook
    cb_emb_path = Path("input/target_variables_with_embeddings.csv")
    if force_rerun or not cb_emb_path.exists():
        cb_path = Path("input/target_variables.csv")
        if cb_path.exists():
            if progress_cb:
                progress_cb("Embedding codebook variables...")
            df = pd.read_csv(cb_path)
            if "description" not in df.columns:
                df["description"] = df.get("variable_name", "")
            df = embed_dataframe(df, embed_fn)
            df.to_csv(cb_emb_path, index=False)

    # Embed each study
    for study in list_studies():
        study_emb_path = Path(f"input/{study}/dataset_variables_with_embeddings.csv")
        if not force_rerun and study_emb_path.exists():
            continue
        auto_path = Path(f"input/{study}/dataset_variables_auto_completed.csv")
        if not auto_path.exists():
            continue
        if progress_cb:
            progress_cb(f"Embedding {study} variables...")
        df = pd.read_csv(auto_path)
        if "description" not in df.columns:
            df["description"] = df.get("variable_name", "")
        df = embed_dataframe(df, embed_fn)
        df.to_csv(study_emb_path, index=False)


# ── Phase 4: Semantic recommendations ────────────────────────────────────────

def get_recommendations(
    force_rerun: bool = False,
    progress_cb: Optional[Callable[[str], None]] = None,
):
    from storage.files import list_studies

    cb_emb_path = Path("input/target_variables_with_embeddings.csv")
    if not cb_emb_path.exists():
        raise FileNotFoundError(
            "Codebook embeddings not found. Run the embedding step first."
        )

    target_df = pd.read_csv(cb_emb_path)

    for study in list_studies():
        recs_path = Path(f"input/{study}/dataset_variables_with_recommendations.csv")
        if not force_rerun and recs_path.exists():
            continue
        study_emb_path = Path(f"input/{study}/dataset_variables_with_embeddings.csv")
        if not study_emb_path.exists():
            continue
        if progress_cb:
            progress_cb(f"Building recommendation index for {study}...")
        study_df = pd.read_csv(study_emb_path)
        study_df = generate_recommendations(study_df, target_df)
        study_df.to_csv(recs_path, index=False)


def _parse_embeddings(series) -> list:
    result: list = []
    for x in series:
        if isinstance(x, list):
            result.append(x)
        elif isinstance(x, str):
            if len(x) > 100_000:
                result.append(None)
                continue
            try:
                result.append(ast.literal_eval(x))
            except Exception:
                result.append(None)
        else:
            result.append(None)
    return result


def generate_recommendations(
    study_df: pd.DataFrame, target_df: pd.DataFrame
) -> pd.DataFrame:
    """Weighted cosine: 0.8 × description + 0.2 × variable name."""
    T_var_raw  = _parse_embeddings(target_df["var_embeddings"])
    T_desc_raw = _parse_embeddings(target_df["description_embeddings"])

    valid_indices = [
        i for i, (v, d) in enumerate(zip(T_var_raw, T_desc_raw))
        if v is not None and d is not None
    ]
    if not valid_indices:
        return study_df

    T_var  = np.array([T_var_raw[i]  for i in valid_indices], dtype=np.float32)
    T_desc = np.array([T_desc_raw[i] for i in valid_indices], dtype=np.float32)
    valid_target = target_df.iloc[valid_indices].reset_index(drop=True)

    def l2norm(mat: np.ndarray) -> np.ndarray:
        return mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12)

    T_var_n  = l2norm(T_var)
    T_desc_n = l2norm(T_desc)

    study_df   = study_df.copy()
    all_recs:  list = []
    all_dists: list = []

    for i in range(len(study_df)):
        v_var_raw  = _parse_embeddings([study_df["var_embeddings"].iloc[i]])[0]
        v_desc_raw = _parse_embeddings([study_df["description_embeddings"].iloc[i]])[0]

        if v_var_raw is None or v_desc_raw is None:
            all_recs.append([])
            all_dists.append([])
            continue

        v_var  = np.array(v_var_raw,  dtype=np.float32)
        v_desc = np.array(v_desc_raw, dtype=np.float32)
        v_var_n  = v_var  / (np.linalg.norm(v_var)  + 1e-12)
        v_desc_n = v_desc / (np.linalg.norm(v_desc) + 1e-12)

        d_var  = 1.0 - (T_var_n  @ v_var_n)
        d_desc = 1.0 - (T_desc_n @ v_desc_n)
        d      = 0.8 * d_desc + 0.2 * d_var

        idx = np.argsort(d)
        all_recs.append(list(valid_target["description"].iloc[idx]))
        all_dists.append([float(x) for x in d[idx]])

    study_df["target_recommendations"] = all_recs
    study_df["target_distances"]       = all_dists
    return study_df


# ── Phase 5: PID / Date recommendations ─────────────────────────────────────

def get_PID_date_recommendations(
    ai_config,
    force_rerun: bool = False,
    progress_cb: Optional[Callable[[str], None]] = None,
):
    from storage.files import list_studies
    from core.ai_provider import AIProviderWrapper

    wrapper  = AIProviderWrapper(ai_config)
    embed_fn = wrapper.generate_embedding

    for study in list_studies():
        pid_date_path = Path(
            f"input/{study}/dataset_variables_with_PID_date_recommendations.csv"
        )
        if not force_rerun and pid_date_path.exists():
            continue
        recs_path = Path(f"input/{study}/dataset_variables_with_recommendations.csv")
        if not recs_path.exists():
            continue
        if progress_cb:
            progress_cb(f"Generating PID/Date recommendations for {study}...")
        study_df = pd.read_csv(recs_path)
        study_df = _add_pid_date_recommendations(study_df, embed_fn)
        study_df.to_csv(pid_date_path, index=False)


def _add_pid_date_recommendations(
    study_df: pd.DataFrame, embed_fn: Callable
) -> pd.DataFrame:
    from scipy.spatial.distance import cosine

    study_df    = study_df.copy()
    var_embs    = _parse_embeddings(study_df["var_embeddings"])
    descriptions = list(study_df.get("description", study_df["variable_name"]))
    var_names    = list(study_df["variable_name"])

    pid_recs:  list = []
    pid_dists: list = []
    date_recs: list = []
    date_dists: list = []

    for i in range(len(study_df)):
        desc = str(descriptions[i]) if descriptions[i] else str(var_names[i])
        pid_query  = embed_fn(f"Unique Identifier of {desc}")
        date_query = embed_fn(f"Date of {desc}")

        pid_scores:  list[tuple[str, float]] = []
        date_scores: list[tuple[str, float]] = []

        for j, emb in enumerate(var_embs):
            if emb is None:
                pid_scores.append((var_names[j], 1.0))
                date_scores.append((var_names[j], 1.0))
                continue
            pid_d  = cosine(pid_query,  emb) if pid_query  else 1.0
            date_d = cosine(date_query, emb) if date_query else 1.0
            pid_scores.append((var_names[j], pid_d))
            date_scores.append((var_names[j], date_d))

        pid_sorted  = sorted(pid_scores,  key=lambda x: x[1])
        date_sorted = sorted(date_scores, key=lambda x: x[1])

        pid_recs.append([x[0] for x in pid_sorted])
        pid_dists.append([x[1] for x in pid_sorted])
        date_recs.append([x[0] for x in date_sorted])
        date_dists.append([x[1] for x in date_sorted])

    study_df["PID_recommendations"]  = pid_recs
    study_df["PID_distances"]        = pid_dists
    study_df["date_recommendations"] = date_recs
    study_df["date_distances"]       = date_dists
    return study_df
