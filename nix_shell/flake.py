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
        "nixpkgsTree": nixlang.call("builtins.getTree", ref),
        "nixpkgs": nixlang.call(
            "builtins.getFlake",
            "path:${nixpkgsTree.outPath}"
        )
    }


def get_ref_from_lockfile(flake_lock: Path | str, nixpkgs: str = "nixpkgs") -> dict[str, NixValue]:
    with open(flake_lock, "r") as f:
        lock = json.load(f)
    return lock["nodes"][nixpkgs]["locked"]


def get_impure_nixpkgs_ref() -> dict:
    return _nix.flake.metadata("nixpkgs")["locked"]
