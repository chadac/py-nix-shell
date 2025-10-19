"""Utility functions for nix_shell."""

import os
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
