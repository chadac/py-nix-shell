"""Deserializer for Nix language constructs."""

from __future__ import annotations

import abc
from dataclasses import dataclass


class NixType(abc.ABC):
    def dumps(self) -> str:
        raise NotImplementedError()


@dataclass
class Let(NixType):
    exprs: dict[str, NixValue]
    result: NixValue

    def dumps(self) -> str:
        return _let(self)


def let(in_: NixValue, **exprs: NixValue) -> Let:
    return Let(exprs, in_)


@dataclass
class Raw(NixType):
    value: str

    def dumps(self) -> str:
        return self.value


def raw(value: str) -> Raw:
    return Raw(value)


@dataclass
class Call(NixType):
    func: Raw
    args: tuple[NixValue, ...]

    def dumps(self) -> str:
        return _call(self)


def call(func: str, *args: NixValue) -> Call:
    return Call(raw(func), args)


def attrs(**kwargs: NixValue) -> dict[str, NixValue]:
    return kwargs


@dataclass
class With(NixType):
    var: str
    expr: NixValue

    def dumps(self) -> str:
        return f"with {self.var}; {dumps(self.expr)}"


def with_(var: str, expr: NixValue) -> With:
    return With(var, expr)


NixValue = bool | str | int | float | dict[str, "NixValue"] | list["NixValue"] | NixType


def dumps(n: NixValue) -> str:
    match n:
        case True:
            return "true"
        case False:
            return "false"
        case int() | float():
            return str(n)
        case str():
            if "\n" in n or '"' in n:
                return f"''{n}''"
            else:
                return f'"{n}"'
        case dict():
            return _attrset(n)
        case list():
            return "[ " + " ".join([_dumps(x) for x in n]) + " ]"
        case NixType():
            return n.dumps()


def _dumps(n: NixValue) -> str:
    """Surround in parens for recursive stuff"""
    return f"({dumps(n)})"


def _attrset(d: dict[str, NixValue]) -> str:
    return (
        "{ " + " ".join([f"{key} = {dumps(value)};" for key, value in d.items()]) + " }"
    )


def _let(let: Let) -> str:
    exprs = "\n".join([f"  {key} = {dumps(n)};" for key, n in let.exprs.items()])
    return f"""let
{exprs}
in {dumps(let.result)}"""


def _call(c: Call):
    return " ".join([dumps(c.func)] + [_dumps(arg) for arg in c.args])
