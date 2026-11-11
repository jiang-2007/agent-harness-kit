"""Built-in tools shipped with the harness."""
from __future__ import annotations

import ast
import operator
import time
from typing import Any

from .base import Tool, ToolResult


class CalculatorTool(Tool):
    """Evaluate a restricted arithmetic expression without ``eval``."""

    name = "calculator"
    description = "Evaluate a safe arithmetic expression, e.g. 2 * (3 + 4)."
    parameters = {
        "expression": {
            "type": "string",
            "description": "Arithmetic expression to evaluate.",
        }
    }

    _OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    def _eval(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp):
            return self._OPS[type(node.op)](self._eval(node.left), self._eval(node.right))
        if isinstance(node, ast.UnaryOp):
            return self._OPS[type(node.op)](self._eval(node.operand))
        raise ValueError("unsupported expression node")

    def run(self, expression: str = "", **_: Any) -> ToolResult:
        try:
            value = self._eval(ast.parse(expression, mode="eval").body)
            return ToolResult(content=str(value))
        except Exception as exc:  # noqa: BLE001 - surfaced to the model as an error
            return ToolResult(content="", ok=False, error=str(exc))


class ClockTool(Tool):
    name = "clock"
    description = "Return the current local time as a readable string."
    parameters: dict = {}

    def run(self, **_: Any) -> ToolResult:
        return ToolResult(content=time.strftime("%Y-%m-%d %H:%M:%S"))


class EchoTool(Tool):
    name = "echo"
    description = "Echo the provided text back (debug tool)."
    parameters = {"text": {"type": "string", "description": "Text to echo."}}

    def run(self, text: str = "", **_: Any) -> ToolResult:
        return ToolResult(content=text)
