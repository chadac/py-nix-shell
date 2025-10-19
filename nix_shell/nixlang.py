"""Deserializer for Nix language constructs."""

from __future__ import annotations

import abc
import shlex
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

from nix_shell import cli

_indent = "  "


class NixCompoundType(abc.ABC):
    """
    A more complex Nix expression type.
    """

    def dumps(self) -> str:
        raise NotImplementedError()


class NixExprType(NixCompoundType):
    def expr(self) -> NixExpr:
        return NotImplemented

    def dumps(self) -> str:
        # Default implementation: call expr() and return as string if it's a string,
        # otherwise serialize it normally
        expr_result = self.expr()
        if isinstance(expr_result, str):
            return expr_result
        return dumps(expr_result)


@dataclass
class StorePath(NixExprType):
    path: Path

    @property
    def store_path(self) -> str:
        return cli.store.add(self.path).strip()

    def expr(self) -> NixExpr:
        return self.store_path


@dataclass
class FileSet(NixExprType):
    """
    An object representing a collection of files that will be mapped into a
    store directory that links each individually.

    This is useful for mirroring a subset of files in a repository for faster
    Nix expression evaluation.
    """

    paths: dict[Path, Path | StorePath]
    pkgs: Raw = field(default_factory=lambda: raw("nixpkgs"))

    def expr(self) -> NixExpr:
        cmds = []
        mk_dirs = set([])
        for dest_path, src_path in self.paths.items():
            parent = dest_path.parent
            # if the parent dir doesn't exist yet, make it
            if parent != dest_path and parent not in mk_dirs:
                cmds += [shlex.join(["mkdir", "-p", "$out/" + str(parent)])]
                mk_dirs.add(parent)

            if isinstance(src_path, Path) and src_path.is_relative_to("/nix/store"):
                # already in the nix store, link it directly
                cmds += [
                    shlex.join(
                        ["ln", "-s", str(src_path).strip(), "$out/" + str(dest_path)]
                    )
                ]
            else:
                if isinstance(src_path, Path):
                    # need to convert into store path
                    store_path = StorePath(src_path)
                else:
                    # already a store path, link it directly
                    store_path = src_path
                cmds += [
                    shlex.join(
                        ["ln", "-s", store_path.store_path, "$out/" + str(dest_path)]
                    )
                ]
        return call(f"{self.pkgs.value}.runCommand", "src", {}, "\n".join(cmds))


@dataclass
class Let(NixCompoundType):
    exprs: dict[str, NixExpr]
    result: NixExpr

    def dumps(self) -> str:
        return _let(self)


def let(in_: NixExpr, **exprs: NixExpr) -> Let:
    return Let(exprs, in_)


@dataclass
class Raw(NixCompoundType):
    value: str

    def dumps(self) -> str:
        return self.value


def raw(value: str) -> Raw:
    return Raw(value)


@dataclass
class Call(NixCompoundType):
    func: Raw
    args: tuple[NixExpr, ...]

    def dumps(self) -> str:
        return _call(self)


def call(func: str, *args: NixExpr) -> Call:
    return Call(raw(func), args)


def attrs(**kwargs: NixExpr) -> dict[str, NixExpr]:
    return kwargs


@dataclass
class With(NixCompoundType):
    var: str
    expr: NixExpr

    def dumps(self) -> str:
        return f"with {self.var}; {dumps(self.expr)}"


def with_(var: str, expr: NixExpr) -> With:
    return With(var, expr)


NixExpr = (
    bool | str | int | float | dict[str, "NixExpr"] | list["NixExpr"] | NixCompoundType
)


def dumps(n: NixExpr) -> str:
    match n:
        case True:
            return "true"
        case False:
            return "false"
        case int() | float():
            return str(n)
        case str():
            return _str(n)
        case dict():
            return _attrset(n)
        case list():
            return "[ " + " ".join([dumps(x) for x in n]) + " ]"
        case NixCompoundType():
            return n.dumps()


def _attrset(d: dict[str, NixExpr]) -> str:
    return (
        "{ " + " ".join([f"{key} = {dumps(value)};" for key, value in d.items()]) + " }"
    )


def _let(let: Let) -> str:
    exprs = "\n".join([f"  {key} = {dumps(n)};" for key, n in let.exprs.items()])
    return f"""let
{exprs}
in {dumps(let.result)}"""


def _call(c: Call):
    return "(" + " ".join([dumps(c.func)] + [dumps(arg) for arg in c.args]) + ")"


def _str(s: str) -> str:
    if "\n" in s or '"' in s:
        wrapped = f"''\n{textwrap.indent(s, _indent)}\n''"
    else:
        wrapped = f'"{s}"'
    return wrapped
