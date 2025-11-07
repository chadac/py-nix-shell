"""Core Nix expression types and serialization."""

from __future__ import annotations

import abc
import textwrap
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    pass

_indent = "  "


class NixComplexType(abc.ABC):
    """
    A more complex Nix expression type.
    """

    def dumps(self) -> str:
        """Serialize this complex type to a Nix expression string."""
        raise NotImplementedError()


class NixExprType(NixComplexType):
    """Base class for complex types that can be converted to simple Nix expressions."""

    def expr(self) -> NixExpr:
        """Convert this complex type to a simple Nix expression."""
        return NotImplemented

    def dumps(self) -> str:
        """Serialize this expression type to a Nix expression string."""
        # Default implementation: call expr() and return as string if it's a string,
        # otherwise serialize it normally
        expr_result = self.expr()
        if isinstance(expr_result, str):
            return expr_result
        return dumps(expr_result)


# Type definition for all valid Nix expressions
NixExpr = (
    bool
    | str
    | int
    | float
    | dict[str, "NixExpr"]
    | list["NixExpr"]
    | Tuple
    | NixComplexType
    | None
)


def dumps(n: NixExpr) -> str:
    """Serialize a Nix expression to its string representation."""
    match n:
        case True:
            return "true"
        case False:
            return "false"
        case None:
            return "null"
        case int() | float():
            return str(n)
        case str():
            return _str(n)
        case dict():
            return _attrset(n)
        case list():
            return "[ " + " ".join([dumps(x) for x in n]) + " ]"
        case tuple():
            return "(" + " ".join([dumps(n[0])] + [dumps(arg) for arg in n[1:]]) + ")"
        case NixComplexType():
            return n.dumps()


def _attrset(d: dict[str, NixExpr]) -> str:
    """Serialize a dictionary to a Nix attribute set."""
    return (
        "{ " + " ".join([f"{key} = {dumps(value)};" for key, value in d.items()]) + " }"
    )


def _str(s: str) -> str:
    """Serialize a string with appropriate Nix quoting."""
    if "\n" in s or '"' in s:
        wrapped = f"''\n{textwrap.indent(s, _indent)}\n''"
    else:
        wrapped = f'"{s}"'
    return wrapped
