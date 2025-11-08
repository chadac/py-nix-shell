"""Utilities for working with Flakes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import NotRequired, TypedDict

from nix_shell import cli, dsl
from nix_shell.constants import PKG_FLAKE_LOCK
from nix_shell.dsl import NixExpr


class FlakeRefLock(TypedDict):
    """
    TypedDict matching the 'locked' field specification in flake.lock files.

    This represents a locked flake reference with all the information needed
    to reproducibly fetch the exact same content.

    Based on the Nix flake.lock specification:
    https://nixos.org/manual/nix/stable/command-ref/new-cli/nix3-flake.html#lock-files
    """

    # Common fields for all types
    type: str  # e.g., "github", "gitlab", "sourcehut", "git", "file", etc.
    lastModified: int  # Unix timestamp of last modification
    narHash: str  # Content hash of the NAR (Nix Archive)

    # GitHub/GitLab/SourceHut specific fields
    owner: NotRequired[str]  # Repository owner
    repo: NotRequired[str]  # Repository name
    rev: NotRequired[str]  # Git revision/commit hash

    # Git specific fields
    url: NotRequired[str]  # Git URL for type="git"
    ref: NotRequired[str]  # Git reference (branch/tag)

    # File/path specific fields
    path: NotRequired[str]  # Local file path for type="file" or type="path"

    # Indirect flake registry fields
    id: NotRequired[str]  # Flake ID for indirect references

    # Additional optional fields that may appear
    submodules: NotRequired[bool]  # Whether to fetch git submodules
    shallow: NotRequired[bool]  # Whether to do shallow clone
    host: NotRequired[str]  # Custom host for git forges


FlakeRef = str | Path | FlakeRefLock


@dataclass
class FlakeInputFollows:
    """Represents a flake input with follows relationships."""

    follows: str | None = None
    inputs: dict[str, FlakeInputFollows] = field(default_factory=dict)


@dataclass
class FlakeInput:
    """Represents a flake input with URL and nested input relationships."""

    url: str
    inputs: dict[str, FlakeInputFollows]


@dataclass
class Flake:
    """Represents a complete flake with inputs and output expression."""

    inputs: dict[str, FlakeInput]
    output: NixExpr


def fetch_locked_from_flake_ref(ref: FlakeRef) -> FlakeRefLock:
    """
    Convert a [flake reference](https://nix.dev/manual/nix/2.28/command-ref/new-cli/nix3-flake.html#url-like-syntax) into a proper locked reference.

    Flake URLs are often not reproducible; however, the result of this
    is properly hashed and reproducible.
    """
    if isinstance(ref, str):
        tree_ref = dict(cli.flake.metadata(ref)["locked"])
        tree_ref.pop("__final", None)
    elif isinstance(ref, Path):
        return fetch_locked_from_flake_ref(f"path:{str(ref.absolute())}")
    else:
        tree_ref = ref
    return tree_ref  # type: ignore


def get_locked_from_lockfile(
    flake_lock: Path | str, name: str = "nixpkgs"
) -> FlakeRefLock:
    """
    Grabs the locked reference for a given node from a `flake.lock`.

    Args:
        flake_lock (Path | str): The path to the `flake.lock` file.
        nixpkgs (str): The name of the node to grab.
    """
    with open(flake_lock, "r") as f:
        lock = json.load(f)
    locked = dict(lock["nodes"][name]["locked"])
    locked.pop("__final", None)
    return locked  # type: ignore


def get_locked_from_py_nix_shell(name: str) -> FlakeRefLock:
    """Get a locked reference from the py-nix-shell flake.lock file."""
    return get_locked_from_lockfile(PKG_FLAKE_LOCK, name)


def get_locked_from_impure_nixpkgs() -> FlakeRefLock:
    """
    Get a locked reference to the version of `nixpkgs` from the local Nix channel.
    """
    locked = dict(cli.flake.metadata("nixpkgs")["locked"])
    locked.pop("__final", None)
    return locked  # type: ignore


def import_flake_from_files(files: dict[str, dsl.NixVar]) -> dsl.NixExpr:
    """
    Create a Nix expression that behaves like builtins.getFlake on a virtual set of files.

    This creates a store derivation containing the files and then manually evaluates
    the flake.nix file with proper inputs, which is more reliable than trying to
    use builtins.getFlake with store paths or external tools like call-flake.

    Args:
        files: Dict mapping relative file paths to NixVar objects representing the files
               e.g., {"flake.nix": flake_nix_var, "flake.lock": flake_lock_var}

    Returns:
        NixExpr that evaluates to the same thing as builtins.getFlake would
    """

    from nix_shell.nix_context import get_nix_context

    ctx = get_nix_context()

    if "flake.nix" not in files:
        raise ValueError("flake.nix file is required")

    if "flake.lock" not in files:
        raise ValueError("flake.lock file is required")

    # Create symlink commands for each file
    link_commands = []
    for path, var in files.items():
        # Use ${} for proper variable interpolation in the shell script
        link_commands.append(f"ln -s ${{{var.value}}} $out/{path}")

    # Build the shell script with proper formatting
    shell_script_lines = ["mkdir -p $out"]
    shell_script_lines.extend(link_commands)
    shell_script = "\n".join(shell_script_lines)

    # Manual flake evaluation - import flake.nix and call its outputs function
    # This is the most reliable approach that works with store paths
    virtual_flake = dsl.let(
        # Create the virtual directory containing the flake files
        flakeDir=dsl.call(
            ctx["pkgs"]["runCommand"],
            "virtual-flake",
            {},
            shell_script,
        ),
        # Import flake.nix and evaluate it manually
        flakeNix=dsl.call(
            dsl.raw("import"),
            dsl.raw('((toString flakeDir) + "/flake.nix")')
        ),
        # Parse flake.lock for input information
        flakeLock=dsl.call(
            dsl.raw("builtins.fromJSON"),
            dsl.call(
                dsl.raw("builtins.readFile"),
                dsl.raw('((toString flakeDir) + "/flake.lock")'),
            ),
        ),
        # Construct inputs based on the lock file
        inputs={
            "nixpkgs": ctx["nixpkgs"],
            "self": None,  # Self-reference handled specially (None becomes null)
        },
        # Call the flake outputs function
        in_=dsl.call(dsl.v("flakeNix")["outputs"], dsl.v("inputs")),
    )

    return virtual_flake
