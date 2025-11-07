"""Filesystem-related Nix expression builders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


from .core import NixExpr, NixExprType
from .common_vars import builtins


@dataclass(frozen=True)
class StorePath(NixExprType):
    """Represents a file or directory added to the Nix store."""

    filename: str
    contents: str

    @classmethod
    def from_path(cls, path: Path, filename: str | None = None) -> StorePath:
        """Create a StorePath from a file on disk."""
        return cls(filename or path.name, path.read_text())

    @classmethod
    def from_string(cls, contents: str, filename: str = "file.txt") -> StorePath:
        """Create a StorePath from a string with the given filename."""
        return cls(filename, contents)

    def expr(self) -> NixExpr:
        """Generate the Nix expression for adding this file to the store."""
        return (builtins["toFile"], self.filename, self.contents)
