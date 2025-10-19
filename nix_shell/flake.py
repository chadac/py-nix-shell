"""Utilities for working with Flakes."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from nix_shell import cli, expr
from nix_shell.build import NixBuild
from nix_shell.expr import NixExpr

FlakeRef = str | dict[str, NixExpr]


@dataclass
class FlakeInputFollows:
    follows: str | None = None
    inputs: dict[str, FlakeInputFollows] = field(default_factory=dict)


@dataclass
class FlakeInput:
    url: str
    inputs: dict[str, FlakeInputFollows]


@dataclass
class Flake:
    inputs: dict[str, FlakeInput]
    output: NixExpr

    @property
    def build(self):
        return NixBuild(
            inputs=
        )


def to_fetch_tree(ref: FlakeRef) -> dict[str, NixExpr]:
    """
    Convert a [flake reference](https://nix.dev/manual/nix/2.28/command-ref/new-cli/nix3-flake.html#url-like-syntax) into a proper locked reference.

    Flake URLs are often not reproducible; however, the result of this
    is properly hashed and reproducible.
    """
    if isinstance(ref, str):
        tree_ref = dict(cli.flake.metadata(ref)["locked"])
        tree_ref.pop("__final", None)
    else:
        tree_ref = ref
    return {
        "nixpkgsTree": expr.call("builtins.fetchTree", tree_ref),
        "nixpkgs": expr.raw("nixpkgsTree.outPath"),
    }


def get_ref_from_lockfile(
    flake_lock: Path | str, nixpkgs: str = "nixpkgs"
) -> dict[str, NixExpr]:
    """
    Grabs the locked reference for a given node from a `flake.lock`.

    Args:
        flake_lock (Path | str): The path to the `flake.lock` file.
        nixpkgs (str): The name of the node to grab.
    """
    with open(flake_lock, "r") as f:
        lock = json.load(f)
    locked = dict(lock["nodes"][nixpkgs]["locked"])
    locked.pop("__final", None)
    return locked


def get_impure_nixpkgs_ref() -> dict:
    """
    Get a locked reference to the version of `nixpkgs` from the local Nix channel.
    """
    locked = dict(cli.flake.metadata("nixpkgs")["locked"])
    locked.pop("__final", None)
    return locked
