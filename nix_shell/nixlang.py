from __future__ import annotations

from dataclasses import dataclass
import textwrap


@dataclass(frozen=True)
class Let:
    exprs: dict[str, NixValue]
    result: NixValue


def let(in_: NixValue, **exprs: NixValue) -> Let:
    return Let(exprs, in_)


@dataclass(frozen=True)
class Raw:
    value: str


def raw(value: str) -> Raw:
    return Raw(value)


@dataclass(frozen=True)
class Call:
    func: Raw
    args: tuple[NixValue, ...]


def call(func: str, *args: NixValue) -> Call:
    return Call(raw(func), args)


def attrs(**kwargs: NixValue) -> dict[str, NixValue]:
    return kwargs


@dataclass(frozen=True)
class With:
    var: str
    expr: NixValue

    def render(self) -> str:
        return f"with {self.var}; {dumps(self.expr)}"


def with_(var: str, expr: NixValue) -> With:
    return With(var, expr)


NixValue = bool | str | int | float | dict[str, "NixValue"] | Let | Raw | Call | list["NixValue"] | With


def dumps(n: NixValue) -> str:
    match n:
        case True:
            return "true"
        case False:
            return "false"
        case int() | float():
            return str(n)
        case str():
            if "\n" in n:
                return f"''{n}''"
            else:
                return f'"{n}"'
        case dict():
            return _attrset(n)
        case list():
            return "[ " + " ".join([_dumps(x) for x in n]) + " ]"
        case Let():
            return _let(n)
        case Raw(raw_str):
            return raw_str
        case Call():
            return _call(n)
        case With():
            return n.render()


def _dumps(n: NixValue) -> str:
    """Surround in parens for recursive stuff"""
    return f"({dumps(n)})"


def _attrset(d: dict[str, NixValue]) -> str:
    return "{ " + " ".join([
        f"{key} = {dumps(value)};"
        for key, value in d.items()
    ]) + " }"


def _let(l: Let) -> str:
    exprs = "\n".join([
        f"  {key} = {dumps(n)};" for key, n in l.exprs.items()
    ])
    return f"""let
{exprs}
in {dumps(l.result)}"""


def _call(c: Call):
    return " ".join(
        [dumps(c.func)] + [
            _dumps(arg) for arg in c.args
        ]
    )
