"""Nix expression builder and utilities."""

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
from .core import (
    NixComplexType,
    NixExpr,
    NixExprType,
    dumps,
)
from .filesystem import StorePath
from .variables import (
    builtins,
    lib,
    pkgs,
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
