"""Utilities for working with Flakes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import NotRequired, TypedDict, cast

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


class FlakeLockNode(TypedDict, total=False):
    """
    Represents a node in a flake.lock file.

    Based on the Nix flake.lock specification, each node can either be:
    - A root node (has 'inputs' field)
    - A locked input node (has 'locked' field)
    - A follows node (has 'follows' field)
    """

    # For root nodes and input nodes with sub-inputs
    inputs: NotRequired[dict[str, str | list[str]]]

    # For locked input nodes - contains the actual flake reference
    locked: NotRequired[FlakeRefLock]

    # For nodes that follow another input
    follows: NotRequired[str | list[str]]

    # Original flake reference before locking
    original: NotRequired[dict[str, str]]

    # Flake input name (for reference)
    flake: NotRequired[bool]


class FlakeLock(TypedDict):
    """
    Represents a complete flake.lock file structure.

    Based on the Nix flake.lock specification:
    https://nixos.org/manual/nix/stable/command-ref/new-cli/nix3-flake.html#lock-files
    """

    # All nodes in the lock file (inputs + root)
    nodes: dict[str, FlakeLockNode]

    # Name of the root node (usually "root")
    root: str

    # Lock file format version
    version: int


# Type alias for importing flake.lock files
FlakeLockImport = FlakeLock


def load_flake_lock(flake_lock_path: Path | str) -> FlakeLock:
    """
    Load and parse a flake.lock file into a FlakeLock TypedDict.

    Args:
        flake_lock_path: Path to the flake.lock file

    Returns:
        FlakeLock object with parsed content

    Raises:
        FileNotFoundError: If flake.lock file doesn't exist
        json.JSONDecodeError: If flake.lock file is invalid JSON
        KeyError: If required fields are missing from flake.lock
    """
    with open(flake_lock_path, "r") as f:
        lock_data = json.load(f)

    # Validate required fields
    if "nodes" not in lock_data:
        raise KeyError("flake.lock missing required 'nodes' field")
    if "root" not in lock_data:
        raise KeyError("flake.lock missing required 'root' field")
    if "version" not in lock_data:
        raise KeyError("flake.lock missing required 'version' field")

    return cast(FlakeLock, lock_data)


def get_input_locked_refs(flake_lock: FlakeLock) -> dict[str, FlakeRefLock]:
    """
    Extract all locked input references from a FlakeLock.

    Args:
        flake_lock: Parsed flake.lock data

    Returns:
        Dictionary mapping input names to their FlakeRefLock data
    """
    locked_refs: dict[str, FlakeRefLock] = {}

    for node_name, node in flake_lock["nodes"].items():
        if node_name == flake_lock["root"]:
            continue  # Skip root node

        if "locked" in node:
            locked_refs[node_name] = node["locked"]

    return locked_refs


def fetch_locked_from_flake_ref(ref: FlakeRef) -> FlakeRefLock:
    """
    Convert a [flake reference](https://nix.dev/manual/nix/2.28/command-ref/new-cli/nix3-flake.html#url-like-syntax) into a proper locked reference.

    Flake URLs are often not reproducible; however, the result of this
    is properly hashed and reproducible.
    """
    tree_ref: FlakeRefLock
    if isinstance(ref, str):
        new_ref = dict(cli.flake.metadata(ref)["locked"])
        new_ref.pop("__final", None)
        tree_ref = cast(FlakeRefLock, new_ref)
    elif isinstance(ref, Path):
        return fetch_locked_from_flake_ref(f"path:{str(ref.absolute())}")
    else:
        tree_ref = cast(FlakeRefLock, ref)
    return tree_ref


def get_locked_from_lockfile(
    flake_lock: Path | str, name: str = "nixpkgs"
) -> FlakeRefLock:
    """
    Grabs the locked reference for a given node from a `flake.lock`.

    Args:
        flake_lock (Path | str): The path to the `flake.lock` file.
        name (str): The name of the node to grab.
    """
    with open(flake_lock, "r") as f:
        lock = json.load(f)
    locked = dict(lock["nodes"][name]["locked"])
    locked.pop("__final", None)
    return locked  # type: ignore


def get_locked_from_py_nix_shell(name: str) -> FlakeRefLock:
    """Get a locked reference from the py-nix-shell flake.lock file."""
    return get_locked_from_lockfile(PKG_FLAKE_LOCK, name)


def locked_to_url(locked: FlakeRefLock) -> str:
    """Convert a FlakeRefLock to a flake URL string."""
    if locked["type"] == "github":
        assert "owner" in locked
        assert "repo" in locked
        assert "rev" in locked
        return f"github:{locked['owner']}/{locked['repo']}/{locked['rev']}"
    elif locked["type"] == "git":
        assert "url" in locked
        assert "rev" in locked
        return f"git+{locked['url']}?rev={locked['rev']}"
    elif locked["type"] == "path":
        assert "path" in locked
        return f"path:{locked['path']}"
    else:
        # Fallback for other types
        return str(locked)


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

    Uses NixOS/flake-compat to properly evaluate the flake from store paths, which is
    the standard, robust solution for this use case.

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

    # Since the files already have NixVars (paths in context), we'll
    # build the virtual filesystem directly here using cat with here-documents

    # Build the shell script using cat with here-documents
    shell_script_lines = ["mkdir -p $out"]
    for path, var in files.items():
        # Use cat with here-document to write file contents
        shell_script_lines.append(f"cat <<'NIX_EOF' > $out/{path}")
        shell_script_lines.append(f"${{{var.value}}}")
        shell_script_lines.append("NIX_EOF")
    shell_script = "\n".join(shell_script_lines)

    # Use flake-compat to evaluate the flake from the store path
    # This approach properly handles working directory context for relative imports
    virtual_flake = dsl.let(
        # Create the virtual directory containing the flake files
        flakeDir=dsl.call(
            ctx["pkgs"]["runCommand"],
            "virtual-flake",
            {},
            shell_script,
        ),
        # Use flake-compat's default.nix directly with proper arguments
        flakeCompat=dsl.call(
            dsl.raw("import"),
            dsl.call(
                dsl.raw("builtins.fetchTarball"),
                "https://github.com/edolstra/flake-compat/archive/f387cd2afec9419c8ee37694406ca490c3f34ee5.tar.gz",
            ),
        ),
        # Call flake-compat with the virtual flake directory
        in_=dsl.call(dsl.v("flakeCompat"), {"src": dsl.v("flakeDir")}),
    )

    return virtual_flake
