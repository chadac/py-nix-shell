"""Nix language construct builders."""

from __future__ import annotations

from dataclasses import dataclass

from .core import NixCompoundType, NixExpr, dumps


@dataclass
class Raw(NixCompoundType):
    """Raw Nix expression text."""

    value: str

    def dumps(self) -> str:
        return self.value


@dataclass
class NixVar(Raw):
    def __getitem__(self, name: str, /) -> NixVar:
        return NixVar(f"{self.value}.{name}")


def var(name: str) -> NixVar:
    return NixVar(name)


def v(name: str) -> NixVar:
    return NixVar(name)


builtins = NixVar("builtins")


def raw(value: str | Raw) -> Raw:
    """Create a raw Nix expression."""
    match value:
        case Raw():
            return value
        case str():
            return Raw(value)


class ParamWithDefault(NixCompoundType):
    name: NixVar
    default: NixExpr

    def dumps(self) -> str:
        return f"{dumps(self.name)} ? {dumps(self.default)}"


class Dots(NixCompoundType):
    def dumps(self) -> str:
        return "..."


dots = Dots()


Param = NixVar | ParamWithDefault | Dots


@dataclass
class Function(NixCompoundType):
    params: list[Param]
    expr: NixExpr

    def dumps(self) -> str:
        return f"({{{', '.join(dumps(p) for p in self.params)}}}: {dumps(self.expr)})"


def func(params: list[Param], expr: NixExpr):
    return Function(params, expr)


@dataclass
class Call(NixCompoundType):
    """Function call expression."""

    func: Raw
    args: tuple[NixExpr, ...]

    def dumps(self) -> str:
        return _call(self)


def call(func: Raw | str, *args: NixExpr) -> Call:
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


Attrs = dict[str, NixExpr]


def attrs(**kwargs: NixExpr) -> Attrs:
    """Create an attribute set from keyword arguments."""
    return kwargs


def _call(c: Call) -> str:
    """Serialize a function call."""
    return "(" + " ".join([dumps(c.func)] + [dumps(arg) for arg in c.args]) + ")"


def _let(let: Let) -> str:
    """Serialize a let expression."""
    exprs = "\n".join([f"  {key} = {dumps(n)};" for key, n in let.exprs.items()])
    return f"""let {exprs} in {dumps(let.result)}"""
