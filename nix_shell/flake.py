from __future__ import annotations

import json
from pathlib import Path

from nix_shell import _nix, nixlang
from nix_shell.nixlang import NixValue


FlakeRef = str | dict[str, NixValue]


def to_fetch_tree(ref: FlakeRef) -> dict[str, NixValue]:
    if isinstance(ref, str):
        tree_ref = _nix.flake.metadata(ref)["locked"]
    else:
        tree_ref  = ref
    return {
        "nixpkgsTree": nixlang.call("builtins.fetchTree", ref),
        "nixpkgs": nixlang.raw("nixpkgsTree.outPath"),
    }


def get_ref_from_lockfile(flake_lock: Path | str, nixpkgs: str = "nixpkgs") -> dict[str, NixValue]:
    with open(flake_lock, "r") as f:
        lock = json.load(f)
    locked = dict(lock["nodes"][nixpkgs]["locked"])
    locked.pop("__final", None)
    return locked


def get_impure_nixpkgs_ref() -> dict:
    locked = dict(_nix.flake.metadata("nixpkgs")["locked"])
    locked.pop("__final", None)
    return locked
