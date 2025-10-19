"""Filesystem-related Nix expression builders."""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from pathlib import Path

from nix_shell import cli

from .core import NixExpr, NixExprType
from .lang import Raw, call, raw


@dataclass
class StorePath(NixExprType):
    """Represents a file or directory added to the Nix store."""

    path: Path

    @property
    def store_path(self) -> str:
        """Get the store path for this file/directory."""
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
                cmds += [f"mkdir -p $out/{parent}"]
                mk_dirs.add(parent)

            if isinstance(src_path, Path) and src_path.is_relative_to("/nix/store"):
                # already in the nix store, link it directly
                cmds += [f"ln -s {shlex.quote(str(src_path).strip())} $out/{dest_path}"]
            else:
                if isinstance(src_path, Path):
                    # need to convert into store path
                    store_path = StorePath(src_path)
                else:
                    # already a store path, link it directly
                    store_path = src_path
                cmds += [f"ln -s {shlex.quote(store_path.store_path)} $out/{dest_path}"]
        return call(f"{self.pkgs.value}.runCommand", "src", {}, "\n".join(cmds))
