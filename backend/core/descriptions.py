"""
Phase 2: AI description generation for study variables that have blank descriptions.
Variables that already have descriptions are skipped (unless force_rerun=True).
AI-generated descriptions are prefixed with * to distinguish them from human-provided ones.
"""
from __future__ import annotations
from pathlib import Path
from typing import Callable, Optional

import pandas as pd


DEFAULT_INIT_PROMPT = (
    "As an AI, you're given the task of translating short variable names "
    "from a public health study into the most likely full variable name."
)


def build_prompt(
    init_prompt: str,
    variable_name: str,
    context: str,
    examples: dict,
) -> list[dict]:
    """Few-shot prompt builder. examples = {var_name: (context_str, description)}."""
    messages = [
        {"role": "system", "content": init_prompt},
        # Hard-coded few-shot anchors
        {"role": "user",      "content": "variable name: Patient ID, context: 'Not available'"},
        {"role": "assistant", "content": "Patient Identifier (?)"},
        {"role": "user",      "content": "variable name: matdiag, context: 'Not available'"},
        {"role": "assistant", "content": "maternal diagnosis (?)"},
    ]
    for var, (ctx, desc) in list(examples.items())[:3]:
        messages.append({"role": "user",      "content": f"variable name: {var}, context: {ctx}"})
        messages.append({"role": "assistant", "content": desc})
    messages.append({
        "role": "user",
        "content": f"variable name: {variable_name}, context: {context}",
    })
    return messages


def generate_descriptions(
    ai_config,
    init_prompt: str = DEFAULT_INIT_PROMPT,
    force_rerun: bool = False,
    progress_cb: Optional[Callable[[str], None]] = None,
):
    from storage.files import list_studies
    from core.ai_provider import AIProviderWrapper

    wrapper  = AIProviderWrapper(ai_config)
    embed_fn = wrapper.generate_embedding
    chat_fn  = wrapper.generate_chat_response

    for study in list_studies():
        _generate_study_descriptions(
            study=study,
            embed_fn=embed_fn,
            chat_fn=chat_fn,
            init_prompt=init_prompt,
            force_rerun=force_rerun,
            progress_cb=progress_cb,
        )


def _generate_study_descriptions(
    study: str,
    embed_fn: Callable,
    chat_fn: Callable,
    init_prompt: str,
    force_rerun: bool,
    progress_cb: Optional[Callable[[str], None]],
):
    from core.recommendations import split_text, get_relevant_context

    source_path = Path(f"input/{study}/dataset_variables.csv")
    auto_path   = Path(f"input/{study}/dataset_variables_auto_completed.csv")

    if not source_path.exists():
        return

    df = pd.read_csv(source_path)
    if "description" not in df.columns:
        df["description"] = ""

    needs_desc = df["description"].isna() | (
        df["description"].astype(str).str.strip() == ""
    )
    to_do = df.index[needs_desc].tolist()

    if not to_do and not force_rerun:
        # All descriptions present — copy the file so Phase 3 can proceed.
        df.to_csv(auto_path, index=False)
        return

    if force_rerun:
        to_do = df.index.tolist()

    # Build PDF context chunks
    txt_path = Path(f"input/{study}/context.txt")
    chunks: list[str]  = []
    chunk_embeddings: list = []
    if txt_path.exists():
        text   = txt_path.read_text(encoding="utf-8", errors="ignore")
        chunks = split_text(text)
        # Only embed the first 500 chars of each chunk to keep costs down
        chunk_embeddings = [embed_fn(c[:500]) for c in chunks]

    # Seed in-context examples from variables that already have descriptions
    examples: dict = {}
    for idx in df.index:
        if idx not in to_do:
            var_name = str(df.at[idx, "variable_name"])
            desc     = str(df.at[idx, "description"])
            ctx      = (
                get_relevant_context(var_name, chunks, chunk_embeddings, embed_fn)
                if chunks else "Not available"
            )
            examples[var_name] = (ctx, desc)

    total = len(to_do)
    for i, idx in enumerate(to_do):
        var_name = str(df.at[idx, "variable_name"])

        if progress_cb:
            progress_cb(f"Generating descriptions for {study} ({i + 1}/{total})...")

        context  = (
            get_relevant_context(var_name, chunks, chunk_embeddings, embed_fn)
            if chunks else "Not available"
        )
        messages = build_prompt(init_prompt, var_name, context, examples)

        try:
            response = chat_fn(messages)
            if not response.startswith("*"):
                response = f"*{response}"
            df.at[idx, "description"] = response
            examples[var_name] = (context, response)
        except Exception:
            df.at[idx, "description"] = f"*{var_name} (?)"

    df.to_csv(auto_path, index=False)
