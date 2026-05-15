"""
Safe expression evaluator and dtype helpers for the transformation engine.
Uses AST walking — eval() is never called.
"""
from __future__ import annotations
import ast
import operator as op

import numpy as np


class SafeEvaluator:
    _BINOPS = {
        ast.Add:  op.add,
        ast.Sub:  op.sub,
        ast.Mult: op.mul,
        ast.Div:  op.truediv,
    }
    _UNARYOPS = {ast.USub: op.neg}
    _ALLOWED_NAMES = {"x"}

    def eval_expression(self, expr: str, context: dict):
        tree = ast.parse(expr, mode="eval")
        return self._eval_node(tree.body, context)

    def _eval_node(self, node, context):
        if isinstance(node, ast.BinOp):
            op_fn = self._BINOPS.get(type(node.op))
            if not op_fn:
                raise ValueError(
                    f"Operator not allowed: {type(node.op).__name__}. Only +, -, *, / are supported."
                )
            return op_fn(
                self._eval_node(node.left, context),
                self._eval_node(node.right, context),
            )
        if isinstance(node, ast.UnaryOp):
            op_fn = self._UNARYOPS.get(type(node.op))
            if not op_fn:
                raise ValueError(f"Unary op not allowed: {type(node.op).__name__}")
            return op_fn(self._eval_node(node.operand, context))
        if isinstance(node, ast.Name):
            if node.id not in self._ALLOWED_NAMES:
                raise ValueError(f"Name not allowed: {node.id}. Only 'x' is permitted.")
            return context[node.id]
        if isinstance(node, ast.Constant):
            return node.value
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def dtype_cast(x, dtype: str):
    try:
        if dtype == "float":   return float(x)
        if dtype == "integer": return int(x)
        if dtype == "string":  return str(x)
        if dtype == "boolean": return bool(x)
        return x
    except (ValueError, TypeError, OverflowError):
        return np.nan


def direct_convert(x, expression: str, source_dtype: str, target_dtype: str):
    x = dtype_cast(x, source_dtype)
    if isinstance(x, float) and np.isnan(x):
        return np.nan
    x = SafeEvaluator().eval_expression(expression, {"x": x})
    return dtype_cast(x, target_dtype)


def categorical_convert(x, mapping_str: str):
    if len(mapping_str) > 10_000:
        return np.nan
    mapping = ast.literal_eval(mapping_str)
    if not isinstance(mapping, dict):
        raise ValueError("Categorical instructions must be a Python dict literal")
    mapping = {str(k): v for k, v in mapping.items()}
    return mapping.get(str(x), np.nan)


def validate_expression(expression: str) -> tuple[bool, str]:
    """Validate a Direct expression without applying it. Returns (valid, message)."""
    try:
        SafeEvaluator().eval_expression(expression, {"x": 1.0})
        return True, "Expression is valid (allowed: +, -, *, /; variable: x)."
    except ValueError as e:
        return False, str(e)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Invalid expression: {e}"
