"""Nix expression builder and utilities."""

from .core import (
    NixCompoundType,
    NixExpr,
    NixExprType,
    dumps,
)
from .filesystem import FileSet, StorePath
from .lang import (
    Attrs,
    Call,
    Function,
    Let,
    NixVar,
    Param,
    Raw,
    With,
    attrs,
    builtins,
    call,
    dots,
    func,
    let,
    raw,
    v,
    var,
    with_,
)

__all__ = [
    # Core types and functions
    "NixCompoundType",
    "NixExpr",
    "NixExprType",
    "NixVar",
    "dumps",
    # Filesystem utilities
    "FileSet",
    "StorePath",
    # Language constructs
    "Call",
    "Let",
    "Raw",
    "With",
    "Attrs",
    "Function",
    "Param",
    "attrs",
    "call",
    "let",
    "raw",
    "with_",
    "dots",
    "func",
    "builtins",
    "var",
    "v",
]
