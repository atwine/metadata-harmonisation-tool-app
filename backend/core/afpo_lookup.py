"""
AfPO Lookup Engine
Parses data/ontologies/afpo-base.obo once at module load and provides
exact + fuzzy population-name lookup against the African Population Ontology.

Ported from the reference Streamlit app's app/components/afpo_lookup.py —
same parsing rules and lookup strategy (exact -> fuzzy via rapidfuzz, threshold 85).
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, TypedDict

# OBO file location — resolved relative to the project root (three levels up
# from this file: backend/core/ -> backend/ -> project root).
_OBO_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "ontologies" / "afpo-base.obo"

# Property codes to extract synonyms from
_SYNONYM_PROPS = {"AfPO:0000450", "AfPO:0000458", "AfPO:0000453"}

# Property codes to skip entirely
_SKIP_PROPS = {"AfPO:0000089", "AfPO:0000565", "AfPO:0000233", "AfPO:0000267"}


class AfpoTerm(TypedDict):
    afpo_id: str
    canonical_name: str
    matched_via: str
    matched_term: str
    confidence: int


def _parse_obo(path: Path) -> dict[str, AfpoTerm]:
    """Parse the OBO file into a flat lookup table keyed on normalised
    (lower-stripped) name/synonym strings, each mapping to a base term dict."""
    lookup_table: dict[str, AfpoTerm] = {}

    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return lookup_table

    blocks = content.split("\n[Term]\n")

    for block in blocks[1:]:  # skip the file header before the first [Term]
        lines = block.splitlines()

        afpo_id: Optional[str] = None
        canonical_name: Optional[str] = None
        synonyms: list[str] = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("id: AfPO:"):
                afpo_id = line[len("id: "):].strip()

            elif line.startswith("name: "):
                canonical_name = line[len("name: "):].strip()

            elif line.startswith("property_value: AfPO:"):
                parts = line.split(" ", 2)
                if len(parts) < 3:
                    continue
                prop_code = parts[1]

                if prop_code in _SKIP_PROPS:
                    continue
                if prop_code not in _SYNONYM_PROPS:
                    continue
                if "http" in line or "https" in line:
                    continue

                match = re.search(r'"([^"]+)"', line)
                if match:
                    val = match.group(1)
                    if "\n" in val or len(val) > 60:
                        continue
                    synonyms.append(val)

            elif line.startswith("synonym: "):
                match = re.search(r'synonym: "([^"]+)"', line)
                if match:
                    val = match.group(1)
                    if "\n" in val or len(val) > 60:
                        continue
                    synonyms.append(val)

        if not afpo_id or not canonical_name:
            continue

        base: AfpoTerm = {
            "afpo_id": afpo_id,
            "canonical_name": canonical_name,
            "matched_via": "",
            "matched_term": "",
            "confidence": 0,
        }

        key = canonical_name.lower().strip()
        lookup_table[key] = base

        for syn in synonyms:
            syn_key = syn.lower().strip()
            if syn_key and syn_key not in lookup_table:
                lookup_table[syn_key] = base

    return lookup_table


# Parsed once at module import — the file is ~10k lines, this is fast enough
# to eat on process start rather than re-parse per request.
lookup_table: dict[str, AfpoTerm] = _parse_obo(_OBO_PATH)


def lookup(value: str) -> Optional[AfpoTerm]:
    """Look up a population/ethnicity value against the AfPO ontology.

    Strategy: exact match (case-insensitive) -> fuzzy match via rapidfuzz
    (WRatio, score_cutoff=85) -> None (gap).
    """
    normalised = value.lower().strip()

    if normalised in lookup_table:
        result = dict(lookup_table[normalised])
        result["matched_via"] = "exact" if normalised == result["canonical_name"].lower() else "synonym"
        result["matched_term"] = value
        result["confidence"] = 100
        return result  # type: ignore[return-value]

    try:
        from rapidfuzz import process, fuzz
        best = process.extractOne(
            normalised,
            lookup_table.keys(),
            scorer=fuzz.WRatio,
            score_cutoff=85,
        )
        if best:
            matched_key, score, _ = best
            result = dict(lookup_table[matched_key])
            result["matched_via"] = "fuzzy"
            result["matched_term"] = value
            result["confidence"] = int(score)
            return result  # type: ignore[return-value]
    except ImportError:
        pass

    return None
