"""Nix expression builder and utilities."""

from .core import (
    NixComplexType,
    NixExpr,
    NixExprType,
    dumps,
)
from .complex import (
    Attrs,
    Function,
    Let,
    NixVar,
    Param,
    ParamWithDefault,
    Raw,
    With,
    attrs,
    call,
    dots,
    func,
    let,
    param,
    raw,
    v,
    var,
    w,
)
from .filesystem import StorePath
from .variables import (
    pkgs,
    lib,
    builtins,
)

__all__ = [
    # Core types and functions
    "NixComplexType",
    "NixExpr",
    "NixExprType",
    "NixVar",
    "dumps",
    # Filesystem utilities
    "StorePath",
    # Language constructs
    "Let",
    "Raw",
    "With",
    "Attrs",
    "Function",
    "Param",
    "ParamWithDefault",
    "attrs",
    "call",
    "let",
    "param",
    "raw",
    "w",
    "dots",
    "func",
    "var",
    "v",
    # common variables
    "pkgs",
    "lib",
    "builtins",
]
