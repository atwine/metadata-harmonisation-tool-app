#!/usr/bin/env python3
"""Metadata Harmonisation Tool: standalone transform script.

Applies the confirmed mappings and transformations of one study to your own full
dataset, on your own computer. Your data is never sent anywhere.

Needs: Python 3.8 or newer and pandas 1.5 or newer (pip install pandas).
Written against pandas 2.2; the conversion rules copy backend/core/transformation_utils.py
and backend/core/transform_engine.py of the app.

Usage:
    python SCRIPT.py --input my_data.csv --output out.csv
Options:
    --sep ","          column separator (default: guessed)
    --encoding utf-8   text encoding (default: guessed)
    --ignore-case-and-spaces  match columns that differ only in letter case or surrounding spaces
    --overwrite        replace the output and report files if they already exist (default: refuse)
    --decimal ","      read 78,6 as 78.6 (default "."); only changes how the text is read
    --report BASE      report files are BASE.txt and BASE.json (default: <output>_report)

Exit codes: 0 done, 1 the output or report could not be written, 2 bad arguments or unreadable input.

The mappings below are plain data (JSON). They are never run as code.
"""
import sys


def _drop_local_folders_from_path():
    """Python puts the script's own folder (and the current folder) first on the module
    search path, so a stray pandas.py or csv.py there would run instead of the real module.
    Remove them before anything else is imported."""
    import os
    here = set()
    for folder in (os.getcwd(), os.path.dirname(os.path.abspath(globals().get("__file__") or ""))):
        here.add(os.path.normcase(os.path.abspath(folder)))
    sys.path[:] = [p for p in sys.path
                   if p not in ("", ".") and os.path.normcase(os.path.abspath(p)) not in here]


_drop_local_folders_from_path()

import argparse
import ast
import codecs
import collections
import csv
import difflib
import json
import math
import operator as op
import os
import re
import tempfile

CHUNK_ROWS = 50000
MAX_UNSEEN_LISTED = 50
MAX_UNSEEN_TRACKED = 10000
MAX_EXAMPLES = 5
MAX_LOOKUP_RULE_CHARS = 10000
MAX_RESULT_CHARS = 1000000
SEP_CANDIDATES = [",", ";", "\t", "|"]
NAN = float("nan")
DECIMAL_COMMA_LOOKS_LIKE = re.compile(r"^\s*[-+]?\d+,\d+\s*$")
DECIMAL_COMMA_HINT = 'these look like decimal commas: re-run with --decimal ","'
REPORT_WARNING_LINES = [
    "this report names raw values from your data and may contain participant",
    "information. It is saved only on this computer; the app never receives it.",
    "Do not share it unless your data agreement allows it.",
]

_CONFIG_JSON = "\n".join((
# __CONFIG_LINES__
))


# ---- conversion rules (copied from backend/core/transformation_utils.py) ----

class ResultTooLong(ValueError):
    """A rule produced a result longer than MAX_RESULT_CHARS. Script only: the app has no such limit."""


def checked_mul(a, b):
    """a * b, but refuses text repeated to more than MAX_RESULT_CHARS before building it."""
    for text, count in ((a, b), (b, a)):
        if isinstance(text, str) and isinstance(count, int) and len(text) * max(count, 0) > MAX_RESULT_CHARS:
            raise ResultTooLong("result longer than %d characters" % MAX_RESULT_CHARS)
    return op.mul(a, b)


class SafeEvaluator:
    _BINOPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: checked_mul, ast.Div: op.truediv}
    _UNARYOPS = {ast.USub: op.neg}
    _ALLOWED_NAMES = {"x"}

    def eval_node(self, node, context):
        if isinstance(node, ast.BinOp):
            op_fn = self._BINOPS.get(type(node.op))
            if not op_fn:
                raise ValueError("Operator not allowed: %s. Only +, -, *, / are supported." % type(node.op).__name__)
            return op_fn(self.eval_node(node.left, context), self.eval_node(node.right, context))
        if isinstance(node, ast.UnaryOp):
            op_fn = self._UNARYOPS.get(type(node.op))
            if not op_fn:
                raise ValueError("Unary op not allowed: %s" % type(node.op).__name__)
            return op_fn(self.eval_node(node.operand, context))
        if isinstance(node, ast.Name):
            if node.id not in self._ALLOWED_NAMES:
                raise ValueError("Name not allowed: %s. Only 'x' is permitted." % node.id)
            return context[node.id]
        if isinstance(node, ast.Constant):
            return node.value
        raise ValueError("Unsupported expression node: %s" % type(node).__name__)


def dtype_cast(x, dtype):
    try:
        if dtype == "float":
            return float(x)
        if dtype == "integer":
            return int(x)
        if dtype == "string":
            return str(x)
        if dtype == "boolean":
            return bool(x)
        return x
    except (ValueError, TypeError, OverflowError):
        return NAN


def is_empty(v):
    if v is None:
        return True
    try:
        return bool(v != v)
    except Exception:
        return False


class Variable:
    """One mapped variable. Parses its instruction once, then converts cells.
    A bad instruction does not stop the run: it is stored and raised for each
    cell that reaches it, which the app counts as an error for that cell."""

    def __init__(self, spec):
        self.study_var = spec["study_var"]
        self.col_name = spec["col_name"]
        self.source_col = self.study_var
        self.t_type = spec["transformation_type"]
        self.instr = spec["transformation_instructions"]
        self.src_dtype = spec["source_dtype"]
        self.tgt_dtype = spec["target_dtype"]
        self.has_instr = isinstance(self.instr, str) and bool(self.instr.strip())
        self.rule = "copy"
        self.tree = None
        self.mapping = None
        self.compile_error = None
        self.too_long = False
        self.numeric = self.src_dtype in ("float", "integer") or self.tgt_dtype in ("float", "integer")
        if self.has_instr and self.t_type == "Direct":
            self.rule = "math"
            try:
                self.tree = ast.parse(str(self.instr), mode="eval")
            except Exception as e:
                self.compile_error = e
        elif self.has_instr and self.t_type == "Categorical":
            self.rule = "lookup"
            text = str(self.instr)
            if len(text) > MAX_LOOKUP_RULE_CHARS:
                self.too_long = True
            else:
                try:
                    mapping = ast.literal_eval(text)
                    if not isinstance(mapping, dict):
                        raise ValueError("Categorical instructions must be a Python dict literal")
                    self.mapping = {str(k): v for k, v in mapping.items()}
                except Exception as e:
                    self.compile_error = e

    def convert(self, val, stats):
        """Returns the output value for one non-empty source value."""
        if not self.has_instr:
            return dtype_cast(val, self.tgt_dtype)
        if self.rule == "math":
            x = dtype_cast(val, self.src_dtype)
            if isinstance(x, float) and math.isnan(x):
                return NAN
            if self.compile_error is not None:
                raise self.compile_error
            x = SafeEvaluator().eval_node(self.tree.body, {"x": x})
            if isinstance(x, str) and len(x) > MAX_RESULT_CHARS:
                raise ResultTooLong("result longer than %d characters" % MAX_RESULT_CHARS)
            return dtype_cast(x, self.tgt_dtype)
        if self.rule == "lookup":
            if self.too_long:
                return NAN
            if self.compile_error is not None:
                raise self.compile_error
            key = str(val)
            if key in self.mapping:
                return self.mapping[key]
            stats.add_unseen(key)
            return NAN
        return dtype_cast(val, self.tgt_dtype)


class Stats:
    def __init__(self):
        self.rows = 0
        self.source_empty = 0
        self.errors = 0
        self.empty_out = 0
        self.not_converted = 0
        self.examples = []
        self.unseen = collections.Counter()
        self.unseen_untracked_rows = 0
        self.comma_like = 0
        self.too_long = 0

    def add_unseen(self, key):
        if key in self.unseen or len(self.unseen) < MAX_UNSEEN_TRACKED:
            self.unseen[key] += 1
        else:
            self.unseen_untracked_rows += 1


class KindTracker:
    """Works out how the app's table would store an output column, so numbers
    are written the same way (a whole-number column with one empty cell is
    stored as decimals, 1.0, by the app)."""

    def __init__(self):
        self.has_empty = False
        self.has_int = False
        self.has_float = False
        self.has_other = False

    def add(self, v):
        if is_empty(v):
            self.has_empty = True
        elif isinstance(v, bool):
            self.has_other = True
        elif isinstance(v, int):
            self.has_int = True
        elif isinstance(v, float):
            self.has_float = True
        else:
            self.has_other = True

    @property
    def kind(self):
        if self.has_other:
            return "object"
        if self.has_float or (self.has_int and self.has_empty):
            return "float"
        if self.has_int:
            return "int"
        return "object" if not self.has_empty else "float"


# ---- reading files ----

def fail(code, message):
    print("ERROR: " + message, file=sys.stderr)
    sys.exit(code)


BYTE_ORDER_MARKS = [  # longest first: the UTF-32 LE mark starts with the UTF-16 LE mark
    (b"\xff\xfe\x00\x00", "utf-32"), (b"\x00\x00\xfe\xff", "utf-32"),
    (b"\xef\xbb\xbf", "utf-8-sig"), (b"\xff\xfe", "utf-16"), (b"\xfe\xff", "utf-16"),
]


def guess_encoding(path):
    """Returns (encoding, is_fallback, found_byte_order_mark)."""
    with open(path, "rb") as f:
        head = f.read(1024 * 1024)
    for mark, name in BYTE_ORDER_MARKS:
        if head.startswith(mark):
            return name, False, True
    try:
        codecs.getincrementaldecoder("utf-8-sig")().decode(head, final=False)
        return "utf-8-sig", False, False
    except UnicodeDecodeError:
        return "latin-1", True, False


def sample_text(path, encoding):
    with open(path, "rb") as f:
        raw = f.read(65536)
    text = codecs.getincrementaldecoder(encoding)(errors="replace").decode(raw, final=False)
    lines = text.splitlines()
    if len(raw) == 65536 and len(lines) > 1:
        lines = lines[:-1]
    return lines


def guess_sep(lines):
    lines = [ln for ln in lines if ln.strip()][:20]
    best, best_score = None, (0.0, 1)
    for cand in SEP_CANDIDATES:
        try:
            counts = [len(r) for r in csv.reader(lines, delimiter=cand)]
        except csv.Error:
            continue
        if not counts or counts[0] < 2:
            continue
        score = (sum(1 for c in counts if c == counts[0]) / float(len(counts)), counts[0])
        if score > best_score:
            best, best_score = cand, score
    return best


def quote(s):
    return json.dumps(s)


def read_header(pd, path, sep, encoding):
    try:
        return list(pd.read_csv(path, nrows=0, sep=sep, encoding=encoding).columns)
    except pd.errors.EmptyDataError:
        fail(2, "The input file is empty.")
    except UnicodeDecodeError:
        fail(2, "The text could not be decoded as %s. Try --encoding latin-1 (or cp1252, utf-16)." % encoding)
    except (OSError, pd.errors.ParserError, ValueError) as e:
        fail(2, "The input file could not be read (%s). Check --sep and --encoding." % type(e).__name__)


def read_chunks(pd, path, sep, encoding, usecols, dtype=None, decimal="."):
    try:
        reader = pd.read_csv(path, sep=sep, encoding=encoding, usecols=usecols, dtype=dtype, decimal=decimal, chunksize=CHUNK_ROWS)
        for chunk in reader:
            yield chunk
    except UnicodeDecodeError:
        fail(2, "The text could not be decoded as %s part way through the file. Try --encoding latin-1 (or cp1252, utf-16)." % encoding)
    except (OSError, pd.errors.ParserError, ValueError) as e:
        fail(2, "The input file could not be read (%s: %s). Check --sep and --encoding." % (type(e).__name__, str(e)[:200]))


def _chunk_label(series):
    """Type of one chunk's column. 'B' is True/False values with empty cells, which
    pandas stores as Python booleans plus NaN (dtype object)."""
    kind = series.dtype.kind
    if kind == "O":
        values = series.dropna()
        if len(values) and all(isinstance(v, bool) for v in values):
            return "B"
    return kind


def infer_column_dtypes(pd, path, sep, encoding, usecols, decimal="."):
    """Same column types the app gets from reading the whole file at once.
    Columns left out of the result keep pandas' own guess for each chunk, which
    is right for True/False columns (booleans stay booleans, empties stay empty)."""
    seen = {}
    for chunk in read_chunks(pd, path, sep, encoding, usecols, decimal=decimal):
        for col in chunk.columns:
            seen.setdefault(col, set()).add(_chunk_label(chunk[col]))
    dtypes = {}
    for col, kinds in seen.items():
        if kinds == {"i"}:
            dtypes[col] = "int64"
        elif kinds <= {"i", "f"}:
            dtypes[col] = "float64"
        elif kinds <= {"b", "B", "f"} and kinds & {"b", "B"}:
            continue
        else:
            dtypes[col] = str
    return dtypes


# ---- running the conversions ----

def transform_chunk(pd, chunk, variables, stats_by_var, kinds_by_col):
    out = {}
    for var in variables:
        stats = stats_by_var[var.study_var]
        tracker = kinds_by_col[var.col_name]
        values = []
        for val in chunk[var.source_col]:
            stats.rows += 1
            if is_empty(val):
                stats.source_empty += 1
                stats.empty_out += 1
                tracker.add(NAN)
                values.append(NAN)
                continue
            try:
                result = var.convert(val, stats)
            except ResultTooLong:
                stats.errors += 1
                stats.too_long += 1
                result = NAN
            except Exception:
                stats.errors += 1
                result = NAN
            if is_empty(result):
                stats.empty_out += 1
                stats.not_converted += 1
                if var.rule != "lookup":
                    if len(stats.examples) < MAX_EXAMPLES:
                        stats.examples.append(str(val)[:100])
                    if var.numeric and DECIMAL_COMMA_LOOKS_LIKE.match(str(val)):
                        stats.comma_like += 1
            tracker.add(result)
            values.append(result)
        out[var.col_name] = values
    return out


def to_frame(pd, out, kinds_by_col):
    cols = {}
    for name, values in out.items():
        kind = kinds_by_col[name].kind
        if kind == "float":
            cols[name] = pd.Series(values, dtype="float64")
        elif kind == "object":
            cols[name] = pd.Series(values, dtype=object)
        else:
            cols[name] = pd.Series(values)
    return pd.DataFrame(cols)


def normalised(name):
    return str(name).strip().casefold()


def close_columns(name, header):
    """Columns of the file that look like the mapped column: same name apart from letter case
    and surrounding spaces first, else the closest spellings."""
    key = normalised(name)
    same = [h for h in header if normalised(h) == key]
    if same:
        return same
    by_key = {}
    for h in header:
        by_key.setdefault(normalised(h), []).append(h)
    close = difflib.get_close_matches(key, list(by_key), n=3, cutoff=0.7)
    return [h for c in close for h in by_key[c]][:3]


def did_you_mean(name, candidates):
    return "%s not found; did you mean %s?" % (name, " or ".join(quote(c) for c in candidates))


def plan_variables(config, header, ignore_case_and_spaces=False):
    variables, warnings, metrics, owner, matched = [], [], [], {}, []
    for spec in config["variables"]:
        study_var = spec["study_var"]
        source_col = study_var
        if study_var and study_var not in header:
            candidates = close_columns(study_var, header)
            same = [h for h in candidates if normalised(h) == normalised(study_var)]
            if ignore_case_and_spaces and len(same) == 1:
                source_col = same[0]
                matched.append({"mapped": study_var, "found": source_col})
        if not study_var or source_col not in header:
            warnings.append("Source column missing: %s" % study_var)
            metric = {"variable": study_var, "successes": 0, "errors": 1,
                      "warning": "Source column not found in input data", "skipped": "missing_column"}
            if study_var and candidates:
                metric["hint"] = did_you_mean(study_var, candidates)
                warnings.append(metric["hint"])
            metrics.append(metric)
            continue
        col_name = spec["col_name"]
        if col_name in owner:
            warnings.append(
                "Skipped '%s': codebook column '%s' is already filled by '%s' - "
                "two variables can't map to the same output column." % (study_var, col_name, owner[col_name]))
            metrics.append({"variable": study_var, "successes": 0, "errors": 1,
                            "warning": "Duplicate mapping to '%s' (kept '%s' instead)" % (col_name, owner[col_name]),
                            "skipped": "duplicate_target"})
            continue
        var = Variable(spec)
        var.source_col = source_col
        if not var.has_instr:
            warnings.append("No transformation for %s -> %s; copied through." % (study_var, spec["codebook_var"]))
        elif var.rule == "copy":
            warnings.append("Unknown transformation type for %s: %s; copied through." % (study_var, var.t_type))
        if var.rule == "lookup" and var.too_long:
            warnings.append("The lookup rule for %s is longer than %d characters; every value is left empty." % (study_var, MAX_LOOKUP_RULE_CHARS))
        owner[col_name] = study_var
        variables.append(var)
    return variables, warnings, metrics, matched


def variable_notes(var, s, args):
    notes = []
    if (var.rule != "lookup" and var.numeric and args.decimal == "." and s.not_converted
            and s.comma_like * 2 > s.not_converted):
        notes.append(DECIMAL_COMMA_HINT)
    if s.too_long:
        notes.append("%d cells gave a result longer than %d characters and were counted as errors and left empty "
                     "(the script stops these; the app would try to build them)." % (s.too_long, MAX_RESULT_CHARS))
    if s.source_empty:
        notes.append("This variable has empty cells. Remember that text such as NA, N/A, n/a, NaN, null and None is read as empty "
                     "(the app does the same), so a rule for those words never applies.")
    if var.rule != "lookup" and var.src_dtype == "string" and var.tgt_dtype == "boolean":
        notes.append('Target type is boolean and the source is text: any non-empty text becomes True, including "No" and "False".')
    if var.rule != "lookup" and var.src_dtype == "float" and var.tgt_dtype == "integer":
        notes.append("Target type is integer and the source has decimals: decimals are cut off, not rounded (78.6 becomes 78).")
    return notes


def near_rule_match(var, value):
    """Why an unseen value was not found in a lookup rule, if only spaces or letter case differ."""
    for key in sorted(var.mapping):
        if value.strip() == key:
            return {"rule_key": key, "if": ["spaces are trimmed"]}
        if value.casefold() == key.casefold():
            return {"rule_key": key, "if": ["letter case is ignored"]}
        if value.strip().casefold() == key.strip().casefold():
            return {"rule_key": key, "if": ["spaces are trimmed", "letter case is ignored"]}
    return None


def build_report(config, args, variables, stats_by_var, kinds_by_col, warnings, skipped_metrics, total_rows, matched=()):
    per_var = []
    metrics = list(skipped_metrics)
    for var in variables:
        s = stats_by_var[var.study_var]
        converted = s.rows - s.empty_out
        unseen_sorted = sorted(s.unseen.items(), key=lambda kv: (-kv[1], kv[0]))
        listed = unseen_sorted[:MAX_UNSEEN_LISTED]
        more = unseen_sorted[MAX_UNSEEN_LISTED:]
        entry = {
            "variable": var.study_var,
            "output_column": var.col_name,
            "rule": "none" if var.rule == "copy" else var.rule,
            "rows": s.rows,
            "converted": converted,
            "empty": s.empty_out,
            "empty_because_source_empty": s.source_empty,
            "empty_not_converted": s.not_converted,
            "errors": s.errors,
            "results_too_long": s.too_long,
            "notes": variable_notes(var, s, args),
        }
        if var.rule == "lookup":
            entry["unseen_values"] = []
            for k, n in listed:
                item = {"value": k, "rows": n}
                near = near_rule_match(var, k)
                if near:
                    item["would_match"] = near
                entry["unseen_values"].append(item)
            entry["unseen_values_not_listed"] = len(more)
            entry["unseen_rows_not_listed"] = sum(n for _, n in more) + s.unseen_untracked_rows
            entry["unseen_total_rows"] = sum(s.unseen.values()) + s.unseen_untracked_rows
        else:
            entry["unconvertible_examples"] = list(s.examples)
        per_var.append(entry)
        metrics.append({"variable": var.study_var, "successes": s.rows - s.errors, "errors": s.errors})
    skipped = [dict({"variable": m["variable"], "reason": m["skipped"]}, **({"hint": m["hint"]} if m.get("hint") else {}))
               for m in skipped_metrics]
    total_success = sum(m["successes"] for m in metrics)
    total_errors = sum(m["errors"] for m in metrics)
    return {
        "study": config["study"],
        "input_rows": total_rows,
        "input_file": os.path.basename(args.input),
        "output_file": os.path.basename(args.output),
        "encoding": getattr(args, "encoding_used", None),
        "contains_participant_values": True,
        "warning": "WARNING: " + " ".join(REPORT_WARNING_LINES),
        "variables": per_var,
        "skipped": skipped,
        "metrics": metrics,
        "total_successes": total_success,
        "total_errors": total_errors,
        "ignore_case_and_spaces_used": bool(matched),
        "matched_columns": list(matched),
        "warnings": warnings,
    }


def report_text(report):
    L = []
    L.append("WARNING: " + REPORT_WARNING_LINES[0])
    L += REPORT_WARNING_LINES[1:]
    L.append("")
    L.append("Results report for study: %s" % report["study"])
    L.append("Input file: %s (%d rows)" % (report["input_file"], report["input_rows"]))
    L.append("Output file: %s" % report["output_file"])
    if report["encoding"]:
        L.append("Encoding: %s" % report["encoding"])
    L.append("")
    L.append("Validation Report")
    L.append("=================")
    L.append("")
    for m in report["metrics"]:
        L.append("- %s: success=%d, errors=%d" % (m["variable"], m["successes"], m["errors"]))
    L.append("")
    L.append("Total successes: %d" % report["total_successes"])
    L.append("Total errors: %d" % report["total_errors"])
    if report["warnings"]:
        L += ["", "Warnings:"] + ["- %s" % w for w in report["warnings"]]
    if report["matched_columns"]:
        L += ["", "--ignore-case-and-spaces was used; these columns were matched:"]
        L += ["- mapped %s -> column in the file %s" % (quote(c["mapped"]), quote(c["found"])) for c in report["matched_columns"]]
    L += ["", "Per variable", "------------"]
    for v in report["variables"]:
        rule = {"math": "math rule", "lookup": "lookup rule", "none": "no rule, type change only"}[v["rule"]]
        L.append("")
        L.append("%s -> %s (%s)" % (v["variable"], v["output_column"], rule))
        L.append("  rows: %d, converted: %d, empty: %d, errors: %d" % (v["rows"], v["converted"], v["empty"], v["errors"]))
        L.append("  empty because the source cell was empty: %d; empty because it could not be converted: %d"
                 % (v["empty_because_source_empty"], v["empty_not_converted"]))
        for note in v["notes"]:
            L.append("  note: " + note)
        if v["rule"] == "lookup":
            if v["unseen_values"]:
                L.append("  values not in the rule (left empty), %d rows in total:" % v["unseen_total_rows"])
                for u in v["unseen_values"]:
                    line = "    %s appeared %d times, not in the rule" % (json.dumps(u["value"]), u["rows"])
                    if "would_match" in u:
                        line += "; it matches %s if %s" % (json.dumps(u["would_match"]["rule_key"]), " and ".join(u["would_match"]["if"]))
                    L.append(line)
                if v["unseen_values_not_listed"] or v["unseen_rows_not_listed"]:
                    L.append("    ... and %d more distinct values (%d rows) not listed"
                             % (v["unseen_values_not_listed"], v["unseen_rows_not_listed"]))
            else:
                L.append("  every value was found in the rule")
        elif v["unconvertible_examples"]:
            L.append("  example input values that could not be converted (first %d): %s"
                     % (MAX_EXAMPLES, ", ".join(json.dumps(e) for e in v["unconvertible_examples"])))
    if report["skipped"]:
        L += ["", "Skipped variables", "-----------------"]
        for s in report["skipped"]:
            why = {"missing_column": "source column not found in the input file",
                   "duplicate_target": "another variable already fills the same output column"}[s["reason"]]
            L.append("- %s: %s" % (s["variable"], why))
    return "\n".join(L) + "\n"


def same_file(a, b):
    """True when both names point at one file: letter case, links and relative paths are looked through."""
    try:
        if os.path.exists(a) and os.path.exists(b):
            return os.path.samefile(a, b)
    except OSError:
        pass
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


class Staging:
    """Files are written under temporary names in the destination folder and moved to
    their real names only after the whole run worked, so a failed run leaves nothing
    behind and an existing output file is never half replaced."""

    def __init__(self):
        self.temp_of = {}

    def add(self, final):
        if os.path.isdir(final):
            fail(1, "Cannot write %s (it is a folder)." % final)
        try:
            fd, temp = tempfile.mkstemp(prefix=".tmp_", suffix=".part", dir=os.path.dirname(os.path.abspath(final)))
            os.close(fd)
        except OSError as e:
            fail(1, "Cannot write %s (%s)." % (final, e.strerror or type(e).__name__))
        self.temp_of[final] = temp
        return temp

    def write_text(self, final, text):
        with open(self.temp_of[final], "w", encoding="utf-8", newline="") as f:
            f.write(text)

    def commit(self, finals):
        try:
            for final in finals:
                os.replace(self.temp_of.pop(final), final)
        except OSError as e:
            fail(1, "Could not write %s (%s)." % (final, e.strerror or type(e).__name__))

    def discard(self):
        for temp in self.temp_of.values():
            try:
                os.remove(temp)
            except OSError:
                pass
        self.temp_of = {}


def main(argv=None):
    try:
        sys.stdout.reconfigure(errors="replace")
        sys.stderr.reconfigure(errors="replace")
    except Exception:
        pass
    config = json.loads(_CONFIG_JSON)
    parser = argparse.ArgumentParser(
        description="Apply the confirmed mappings of study %s to your own data." % config["study"].replace("%", "%%"))
    parser.add_argument("--input", required=True, help="your full data file (CSV)")
    parser.add_argument("--output", required=True, help="where to write the transformed CSV")
    parser.add_argument("--report", help="base name for the report files (default: <output>_report)")
    parser.add_argument("--sep", help="column separator (default: guessed)")
    parser.add_argument("--encoding", help="text encoding (default: guessed)")
    parser.add_argument("--ignore-case-and-spaces", action="store_true", dest="ignore_case_and_spaces",
                        help="match mapped columns to file columns that differ only in letter case or surrounding spaces")
    parser.add_argument("--overwrite", action="store_true", help="replace the output and report files if they already exist")
    parser.add_argument("--decimal", choices=[".", ","], default=".",
                        help='decimal mark in the numbers of your file (default: "."); only changes how the text is read')
    args = parser.parse_args(argv)

    try:
        import pandas as pd
    except ModuleNotFoundError as e:
        if e.name == "pandas":
            fail(2, "pandas is not installed. Run: pip install pandas")
        fail(2, "pandas could not be loaded (%s: %s)." % (type(e).__name__, e))
    except Exception as e:
        fail(2, "pandas could not be loaded (%s: %s)." % (type(e).__name__, e))
    try:
        major, minor = [int(p) for p in pd.__version__.split(".")[:2]]
        if (major, minor) < (1, 5):
            fail(2, "pandas %s is too old; version 1.5 or newer is needed. Run: pip install --upgrade pandas" % pd.__version__)
    except ValueError:
        pass

    if not os.path.isfile(args.input):
        fail(2, "Input file not found: %s" % args.input)
    report_base = args.report or (os.path.splitext(args.output)[0] + "_report")
    protected = [("the input file", args.input)]
    if globals().get("__file__"):
        protected.append(("this script", __file__))
    for label, target in (("--output", args.output), ("the .txt report", report_base + ".txt"),
                          ("the .json report", report_base + ".json")):
        for what, existing in protected:
            if same_file(target, existing):
                fail(2, "%s (%s) is the same file as %s. Nothing was written. Choose a different name." % (label, target, what))
    if not args.overwrite:
        for target in (args.output, report_base + ".txt", report_base + ".json"):
            if os.path.lexists(target) and not os.path.isdir(target):
                fail(2, "%s already exists. Nothing was changed. Choose a different name, or add --overwrite to replace it." % target)
    staging = Staging()
    try:
        return run(args, config, pd, report_base, staging)
    finally:
        staging.discard()


def run(args, config, pd, report_base, staging):
    out_final, txt_final, json_final = args.output, report_base + ".txt", report_base + ".json"
    for target in (out_final, txt_final, json_final):
        staging.add(target)
    encoding = args.encoding
    if not encoding:
        try:
            encoding, guessed_fallback, from_mark = guess_encoding(args.input)
        except OSError as e:
            fail(2, "The input file could not be read (%s)." % (e.strerror or type(e).__name__))
        if from_mark and encoding != "utf-8-sig":
            print("Notice: the file starts with a byte-order mark, so it is read as %s." % encoding)
        if guessed_fallback:
            print("Notice: the file is not UTF-8, so it is being read as latin-1. If accents look wrong, "
                  "re-run with --encoding cp1252 (or another encoding).")
    try:
        codecs.lookup(encoding)
    except LookupError:
        fail(2, "Unknown encoding: %s" % encoding)
    args.encoding_used = encoding
    sep = args.sep
    if not sep:
        sep = guess_sep(sample_text(args.input, encoding))
        if sep is None:
            sep = ","
        print("Using separator %s and encoding %s." % (quote(sep), encoding))
    if sep == args.decimal:
        fail(2, "--decimal %s is the same character as the column separator. Use --sep with a different character." % quote(args.decimal))
    sample_head = "".join(sample_text(args.input, encoding)[:5])
    if "\x00" in sample_head or "\ufffd" in sample_head:
        fail(2, "The text looks garbled with encoding %s. Try --encoding utf-16 or cp1252." % encoding)

    header = read_header(pd, args.input, sep, encoding)
    mapped_cols = [spec["study_var"] for spec in config["variables"]]
    if len(header) < 2 and not args.sep and not any(c in header for c in mapped_cols):
        fail(2, "Only one column was found with separator %s. Re-run with --sep (for example --sep \";\") "
                "and check --encoding." % quote(sep))

    variables, warnings, skipped_metrics, matched = plan_variables(config, header, args.ignore_case_and_spaces)
    if not variables:
        report = build_report(config, args, [], {}, {}, warnings, skipped_metrics, 0, matched)
        staging.write_text(txt_final, report_text(report))
        staging.write_text(json_final, json.dumps(report, indent=2))
        staging.commit([txt_final, json_final])
        hints = [m["hint"] for m in skipped_metrics if m.get("hint")]
        fail(2, "None of the mapped columns were found in the input file, so nothing was written. See %s.txt%s"
                % (report_base, "".join("\n  " + h for h in hints[:10])))

    usecols = [v.source_col for v in variables]
    dtypes = infer_column_dtypes(pd, args.input, sep, encoding, usecols, args.decimal)

    stats_by_var = {v.study_var: Stats() for v in variables}
    kinds_by_col = {v.col_name: KindTracker() for v in variables}
    total_rows = 0
    for chunk in read_chunks(pd, args.input, sep, encoding, usecols, dtypes, args.decimal):
        total_rows += len(chunk)
        transform_chunk(pd, chunk, variables, stats_by_var, kinds_by_col)

    scratch_stats = {v.study_var: Stats() for v in variables}
    scratch_kinds = {v.col_name: KindTracker() for v in variables}
    columns = [v.col_name for v in variables]
    temp_out = staging.temp_of[out_final]
    try:
        pd.DataFrame(columns=columns).to_csv(temp_out, index=False, encoding="utf-8")
        for chunk in read_chunks(pd, args.input, sep, encoding, usecols, dtypes, args.decimal):
            out = transform_chunk(pd, chunk, variables, scratch_stats, scratch_kinds)
            to_frame(pd, out, kinds_by_col).to_csv(temp_out, mode="a", header=False, index=False, encoding="utf-8")
        report = build_report(config, args, variables, stats_by_var, kinds_by_col, warnings, skipped_metrics, total_rows, matched)
        staging.write_text(txt_final, report_text(report))
        staging.write_text(json_final, json.dumps(report, indent=2))
    except OSError as e:
        fail(1, "Could not write the output or report (%s)." % (e.strerror or type(e).__name__))
    staging.commit([out_final, txt_final, json_final])

    n_not = sum(v["empty_not_converted"] for v in report["variables"])
    print("Study %s: %d rows, %d variables written to %s" % (config["study"], total_rows, len(variables), args.output))
    print("Successes: %d, errors: %d, cells left empty because they could not be converted: %d, variables skipped: %d"
          % (report["total_successes"], report["total_errors"], n_not, len(report["skipped"])))
    for w in warnings:
        print("Warning: " + w)
    print("Results report (may contain participant values, keep it private): %s.txt and %s.json" % (report_base, report_base))
    return 0


if __name__ == "__main__":
    sys.exit(main())
