"""Nix language construct builders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .core import NixCompoundType, dumps

if TYPE_CHECKING:
    from .core import NixExpr


@dataclass
class Raw(NixCompoundType):
    """Raw Nix expression text."""

    value: str

    def dumps(self) -> str:
        return self.value


NixVar = Raw


def raw(value: str) -> Raw:
    """Create a raw Nix expression."""
    return Raw(value)


@dataclass
class Call(NixCompoundType):
    """Function call expression."""

    func: Raw
    args: tuple[NixExpr, ...]

    def dumps(self) -> str:
        return _call(self)


def call(func: str, *args: NixExpr) -> Call:
    """Create a function call expression."""
    return Call(raw(func), args)


@dataclass
class Let(NixCompoundType):
    """Let expression with variable bindings."""

    exprs: dict[str, NixExpr]
    result: NixExpr

    def dumps(self) -> str:
        return _let(self)


def let(in_: NixExpr, **exprs: NixExpr) -> Let:
    """Create a let expression."""
    return Let(exprs, in_)


@dataclass
class With(NixCompoundType):
    """With expression for bringing variables into scope."""

    var: str
    expr: NixExpr

    def dumps(self) -> str:
        return f"with {self.var}; {dumps(self.expr)}"


def with_(var: str, expr: NixExpr) -> With:
    """Create a with expression."""
    return With(var, expr)


def attrs(**kwargs: NixExpr) -> dict[str, NixExpr]:
    """Create an attribute set from keyword arguments."""
    return kwargs


def _call(c: Call) -> str:
    """Serialize a function call."""
    return "(" + " ".join([dumps(c.func)] + [dumps(arg) for arg in c.args]) + ")"


def _let(let: Let) -> str:
    """Serialize a let expression."""
    exprs = "\n".join([f"  {key} = {dumps(n)};" for key, n in let.exprs.items()])
    return f"""let
{exprs}
in {dumps(let.result)}"""
