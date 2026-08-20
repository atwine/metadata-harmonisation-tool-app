"""
AfPO Lookup Engine
Parses an AfPO .obo file into an in-memory lookup table and provides
exact + fuzzy population-name lookup against the African Population Ontology.

Ported from the reference Streamlit app's app/components/afpo_lookup.py —
same parsing rules and lookup strategy (exact -> fuzzy via rapidfuzz, threshold 85).

The table is refreshable at runtime (see refresh_ontology()) — checked once on
backend startup so a term that's been added upstream since this file was last
shipped stops showing up as a "gap" without needing a rebuild/redeploy.
"""
from __future__ import annotations
import datetime
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional, TypedDict

logger = logging.getLogger(__name__)

# The file baked into the image/repo at build time — never overwritten at
# runtime, so there's always a known-good fallback even if a refresh fails
# and no cached copy exists yet (e.g. very first run, no network).
_SHIPPED_OBO_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "ontologies" / "afpo-base.obo"

# Where a successfully-fetched refresh gets written. Deliberately outside
# data/ (a tracked source path) — this is runtime-generated, like input/,
# results/, logs/, db/. Bind-mounted in Docker so a later *offline* restart
# still uses the last-known-good fetch instead of reverting to the
# image-baked version.
_CACHE_DIR = Path("ontology_cache")
_CACHE_OBO_PATH = _CACHE_DIR / "afpo-base.obo"
_CACHE_META_PATH = _CACHE_DIR / "meta.json"

_SOURCE_URL = os.environ.get(
    "AFPO_ONTOLOGY_URL", "https://raw.githubusercontent.com/h3abionet/afpo/main/afpo-base.obo"
)

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


def _parse_obo(content: str) -> dict[str, AfpoTerm]:
    """Parse .obo file content into a flat lookup table keyed on normalised
    (lower-stripped) name/synonym strings, each mapping to a base term dict."""
    lookup_table: dict[str, AfpoTerm] = {}

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


def _extract_data_version(content: str) -> Optional[str]:
    for line in content.splitlines()[:20]:
        if line.startswith("data-version:"):
            return line[len("data-version:"):].strip()
    return None


def _load_initial() -> tuple[dict[str, AfpoTerm], Optional[str], Optional[str], str]:
    """Loads the table at import time: prefer a previously-cached refresh
    (last known-good fetch, survives an offline restart via the bind mount)
    over the file baked into the image/repo. Returns
    (table, data_version, fetched_at, source)."""
    if _CACHE_OBO_PATH.exists():
        content = _CACHE_OBO_PATH.read_text(encoding="utf-8")
        fetched_at = None
        if _CACHE_META_PATH.exists():
            try:
                fetched_at = json.loads(_CACHE_META_PATH.read_text(encoding="utf-8")).get("fetched_at")
            except (json.JSONDecodeError, OSError):
                pass
        return _parse_obo(content), _extract_data_version(content), fetched_at, "cache"

    try:
        content = _SHIPPED_OBO_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}, None, None, "missing"
    return _parse_obo(content), _extract_data_version(content), None, "shipped"


# Loaded once at module import — the file is ~10k lines, fast enough to eat
# on process start rather than re-parse per request. Refreshable afterwards
# via refresh_ontology() without needing a process restart.
lookup_table: dict[str, AfpoTerm]
_current_data_version: Optional[str]
_current_fetched_at: Optional[str]
_current_source: str
lookup_table, _current_data_version, _current_fetched_at, _current_source = _load_initial()


def refresh_ontology(timeout: float = 10.0) -> dict:
    """Fetches the latest .obo from upstream; if its data-version differs
    from what's currently loaded, swaps the in-memory table and persists the
    new file to the (bind-mounted, in Docker) cache path. Never raises —
    called from the startup lifespan, so a slow/offline network must degrade
    to 'keep what we have', not block or crash startup."""
    global lookup_table, _current_data_version, _current_fetched_at, _current_source

    try:
        import httpx
        resp = httpx.get(_SOURCE_URL, timeout=timeout)
        resp.raise_for_status()
        content = resp.text
    except Exception as e:
        logger.warning("AfPO ontology refresh failed (%s) — keeping %s copy", e, _current_source)
        return {"status": "unavailable", "data_version": _current_data_version, "source": _current_source}

    new_version = _extract_data_version(content)
    if new_version is not None and new_version == _current_data_version:
        return {"status": "up_to_date", "data_version": _current_data_version, "source": _current_source}

    new_table = _parse_obo(content)
    if not new_table:
        logger.warning("AfPO ontology refresh fetched unparseable content — keeping %s copy", _current_source)
        return {"status": "unavailable", "data_version": _current_data_version, "source": _current_source}

    _CACHE_DIR.mkdir(exist_ok=True)
    _CACHE_OBO_PATH.write_text(content, encoding="utf-8")
    fetched_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    _CACHE_META_PATH.write_text(
        json.dumps({"data_version": new_version, "fetched_at": fetched_at, "source_url": _SOURCE_URL}),
        encoding="utf-8",
    )

    old_version = _current_data_version
    lookup_table = new_table
    _current_data_version = new_version
    _current_fetched_at = fetched_at
    _current_source = "cache"
    logger.info("AfPO ontology updated: %s -> %s", old_version, new_version)
    return {"status": "updated", "data_version": new_version, "previous_data_version": old_version, "source": "cache"}


def ontology_status() -> dict:
    return {
        "data_version": _current_data_version,
        "fetched_at": _current_fetched_at,
        "source_url": _SOURCE_URL,
        "using_cache": _current_source == "cache",
    }


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
