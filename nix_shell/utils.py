"""Utility functions for nix_shell."""

import logging
import os
import shutil
import subprocess
from pathlib import Path


def find_shared_root(paths: list[Path]) -> Path:
    """
    Find the shared root directory of a list of paths.

    Args:
        paths: List of Path objects to find the common root for

    Returns:
        Path object representing the deepest common directory

    Examples:
        >>> find_shared_root([Path("/a/b/c"), Path("/a/b/d")])
        Path("/a/b")
        >>> find_shared_root([Path("/a/b/c"), Path("/x/y/z")])
        Path("/")
        >>> find_shared_root([Path("a/b/c"), Path("a/d/e")])
        Path("a")
    """
    if not paths:
        return Path(".")

    # Convert all paths to absolute paths and handle files vs directories
    processed_paths = []
    for p in paths:
        abs_p = p.absolute()
        processed_paths.append(abs_p.parent if abs_p.suffix else abs_p)

    # Use os.path.commonpath to find the shared root
    try:
        common_path = os.path.commonpath(processed_paths)
        return Path(common_path)
    except ValueError:
        # This can happen on Windows with different drives, but shouldn't on Unix
        return Path("/")  # Return root as fallback


def format_nix(expr: str, raise_if_missing: bool = False) -> str:
    """Format a Nix expression using nixfmt if available."""
    if shutil.which("nixfmt"):
        return subprocess.check_output(["nixfmt"], input=expr.encode()).decode()
    elif not raise_if_missing:
        logging.warning(
            "nixfmt not found -- install it for expressions that are easier to debug"
        )
        return expr
    else:
        # TODO: Probably replace this with some `nix.run` logic.
        raise RuntimeError("The `nixfmt` command is required.")
