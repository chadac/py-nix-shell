"""Utilities for working with Flakes."""

from __future__ import annotations

import json
from pathlib import Path

from nix_shell import _nix, nixlang
from nix_shell.nixlang import NixValue

FlakeRef = str | dict[str, NixValue]


def to_fetch_tree(ref: FlakeRef) -> dict[str, NixValue]:
    """
    Convert a [flake reference](https://nix.dev/manual/nix/2.28/command-ref/new-cli/nix3-flake.html#url-like-syntax) into a proper locked reference.

    Flake URLs are often not reproducible; however, the result of this
    is properly hashed and reproducible.
    """
    if isinstance(ref, str):
        tree_ref = dict(_nix.flake.metadata(ref)["locked"])
        tree_ref.pop("__final", None)
    else:
        tree_ref = ref
    return {
        "nixpkgsTree": nixlang.call("builtins.fetchTree", tree_ref),
        "nixpkgs": nixlang.raw("nixpkgsTree.outPath"),
    }


def get_ref_from_lockfile(
    flake_lock: Path | str, nixpkgs: str = "nixpkgs"
) -> dict[str, NixValue]:
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
    locked = dict(_nix.flake.metadata("nixpkgs")["locked"])
    locked.pop("__final", None)
    return locked
