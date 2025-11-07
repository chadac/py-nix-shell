"""Nix language construct builders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from .core import NixComplexType, NixExpr, dumps


@dataclass
class Raw(NixComplexType):
    """Raw Nix expression text."""

    value: str

    def dumps(self) -> str:
        """Return the raw Nix expression value."""
        return self.value


def raw(value: str | Raw) -> Raw:
    """Create a raw Nix expression."""
    match value:
        case Raw():
            return value
        case str():
            return Raw(value)


@dataclass
class NixVar(Raw):
    """A Nix variable that supports attribute access and function calls."""

    def __getitem__(self, name: str, /) -> NixVar:
        """Access an attribute of this variable."""
        return NixVar(f"{self.value}.{name}")

    def __getattr__(self, name: str, /) -> NixVar:
        """Access an attribute of this variable via dot notation."""
        if name == "value":
            return self.__dict__["value"]
        else:
            return self[name]

    def __call__(self, *args: NixExpr) -> tuple:
        """Call this variable as a function with the given arguments."""
        return (self,) + args

    def __repr__(self) -> str:
        """Return a string representation of this variable."""
        return f"${{{self.value}}}"


def var(name: str) -> NixVar:
    """Create a Nix variable with the given name."""
    return NixVar(name)


def v(name: str) -> NixVar:
    """Create a Nix variable with the given name (short alias for var)."""
    return NixVar(name)


@dataclass(frozen=True)
class ParamWithDefault(NixComplexType):
    """A function parameter with a default value."""

    name: NixVar
    default: NixExpr

    def dumps(self) -> str:
        """Serialize this parameter with its default value."""
        return f"{dumps(self.name)} ? {dumps(self.default)}"


class Dots(NixComplexType):
    """Represents the '...' parameter in Nix function signatures."""

    def dumps(self) -> str:
        """Serialize the dots parameter."""
        return "..."


dots = Dots()


Param = TypeVar("Param", bound=NixVar | ParamWithDefault | Dots)


def param(name: str, default: NixExpr | None) -> NixVar | ParamWithDefault:
    """Create a function parameter, optionally with a default value."""
    if default is None:
        return var(name)
    else:
        return ParamWithDefault(var(name), default)


@dataclass
class Function(NixComplexType, Generic[Param]):
    """A Nix function with parameters and a body expression."""

    params: list[Param]
    expr: NixExpr

    def dumps(self) -> str:
        """Serialize this function to Nix syntax."""
        return f"({{{', '.join(dumps(p) for p in self.params)}}}: {dumps(self.expr)})"


def func(params: list[Param], expr: NixExpr):
    """Create a Nix function with the given parameters and body expression."""
    return Function(params, expr)


def call(func: Raw, *args: NixExpr) -> tuple[(NixExpr, ...)]:
    """Create a function call expression."""
    return (raw(func),) + args


@dataclass
class Let(NixComplexType):
    """Let expression with variable bindings."""

    exprs: dict[str, NixExpr]
    result: NixExpr

    def dumps(self) -> str:
        """Serialize this let expression to Nix syntax."""
        exprs = "\n".join([f"  {key} = {dumps(n)};" for key, n in self.exprs.items()])
        return f"""let {exprs} in {dumps(self.result)}"""


def let(in_: NixExpr, **exprs: NixExpr) -> Let:
    """Create a let expression."""
    return Let(exprs, in_)


@dataclass
class With(NixComplexType):
    """With expression for bringing variables into scope."""

    var: str
    expr: NixExpr

    def dumps(self) -> str:
        """Serialize this with expression to Nix syntax."""
        return f"with {self.var}; {dumps(self.expr)}"


def w(var: str, expr: NixExpr) -> With:
    """Create a with expression."""
    return With(var, expr)


Attrs = dict[str, NixExpr]


def attrs(**kwargs: NixExpr) -> Attrs:
    """Create an attribute set from keyword arguments."""
    return kwargs
