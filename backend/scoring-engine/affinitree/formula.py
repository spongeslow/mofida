"""A constrained arithmetic evaluator for the formula strings stored in the
Affinitree JSON configs (e.g. ``trl_normalised * 0.5 + ip_score * 0.35``).

Only a whitelisted subset of Python's grammar is permitted: names bound in the
provided namespace, numeric literals, ``+ - * /``, parentheses, unary minus, and
the single function ``ln``. Anything else raises ``FormulaError``. This keeps the
"formulas live in config, not code" property without exposing ``eval``.
"""

from __future__ import annotations

import ast
import math
import operator
from typing import Mapping

FUNCTIONS = {"ln": lambda x: math.log(x)}

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


class FormulaError(ValueError):
    pass


def evaluate(expression: str, namespace: Mapping[str, float]) -> float:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:  # pragma: no cover - config authoring error
        raise FormulaError(f"cannot parse formula {expression!r}: {exc}") from exc
    return float(_eval(tree.body, namespace))


def _eval(node: ast.AST, ns: Mapping[str, float]) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise FormulaError(f"non-numeric constant: {node.value!r}")
    if isinstance(node, ast.Name):
        if node.id not in ns:
            raise FormulaError(f"unknown variable in formula: {node.id!r}")
        return float(ns[node.id])
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval(node.left, ns), _eval(node.right, ns))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        val = _eval(node.operand, ns)
        return val if isinstance(node.op, ast.UAdd) else -val
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        fn = FUNCTIONS.get(node.func.id)
        if fn is None:
            raise FormulaError(f"unknown function: {node.func.id!r}")
        args = [_eval(a, ns) for a in node.args]
        return float(fn(*args))
    raise FormulaError(f"unsupported expression node: {type(node).__name__}")
