"""
Flake-based Nix shell management utilities.

This module provides functions to initialize and manage flake-based development shells.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from nix_shell import cli
from nix_shell.build import NixShell

if TYPE_CHECKING:
    from nix_shell.nix_context import NixContext

logger = logging.getLogger(__name__)


def init(
    *,
    minimal: bool = False,
    files: list[str] | None = None,
    ctx: NixContext | None = None,
) -> None:
    """
    Load existing flake data into the NixContext.

    Requires that both flake.nix and flake.lock already exist.

    Args:
        minimal: If True, adds individual flake files to context for direct evaluation.
                If False, uses builtins.getFlake with locked reference.
        files: Additional files to include in the virtual flake (only used when minimal=True).
               These files will be copied alongside flake.nix and flake.lock.
        ctx: NixContext to load flake into (defaults to current global context)
    """
    from nix_shell.nix_context import get_nix_context

    ctx = ctx or get_nix_context()
    flake_nix_path = Path("flake.nix")
    flake_lock_path = Path("flake.lock")

    # Check that both flake files exist
    if not flake_nix_path.exists():
        raise FileNotFoundError(
            "flake.nix not found. Please create a flake.nix file first."
        )

    if not flake_lock_path.exists():
        raise FileNotFoundError(
            "flake.lock not found. Please run 'nix flake lock' first."
        )

    # Load flake data into context
    if minimal:
        # Add individual files to context for direct evaluation
        flake_nix_var = ctx.path(flake_nix_path)
        flake_lock_var = ctx.path(flake_lock_path)

        # Import the flake using our file-based evaluation
        from nix_shell.flake import import_flake_from_files

        flake_files = {
            "flake.nix": flake_nix_var,
            "flake.lock": flake_lock_var,
        }

        # Add additional files if specified
        if files:
            for file_path in files:
                file_path_obj = Path(file_path)
                if not file_path_obj.exists():
                    raise FileNotFoundError(f"Additional file not found: {file_path}")
                file_var = ctx.path(file_path_obj)
                flake_files[file_path] = file_var

        ctx["projectFlake"] = import_flake_from_files(flake_files)
        logger.info(
            f"added flake files to context for direct evaluation: {list(flake_files.keys())}"
        )
    else:
        # Use builtins.getFlake with the current directory as locked reference
        flake_ref = Path.cwd().resolve()
        ctx.flake(str(flake_ref), name="projectFlake")
        logger.info(f"added flake reference to context: {flake_ref}")


def devshell(
    *, target: str = "devShells.default", ctx: NixContext | None = None
) -> NixShell:
    """
    Create a NixShell from a flake devShell target using the context.

    Args:
        target: The flake output path (e.g., "devShells.default", "devShells.python")
        ctx: NixContext containing flake data (defaults to current global context)

    Returns:
        NixShell instance for the specified devShell
    """
    from nix_shell.nix_context import get_nix_context

    ctx = ctx or get_nix_context()

    # Check if we have projectFlake in context (from init with minimal=True)
    # If so, use the full approach that accesses projectFlake directly
    if "projectFlake" in ctx._vars:
        # Full approach: use projectFlake from context (created by init with minimal=True)
        # Extract the target from the flake
        target_parts = target.split(".")

        # Insert system if not already specified in target
        # Standard flake structure: devShells.{system}.{name}
        system = cli.current_system()
        if (
            system not in target
            and len(target_parts) >= 2
            and target_parts[0] == "devShells"
        ):
            # Insert system between devShells and the shell name
            target_parts.insert(1, system)

        expr = _build_nested_access(ctx["projectFlake"], target_parts)
    else:
        raise RuntimeError("Need to call flake_nix.init()")

    return expr


def _build_nested_access(base_expr: Any, path_parts: list[Any]) -> Any:
    """Build nested attribute access expression: base.part1.part2.part3"""
    result = base_expr
    for part in path_parts:
        result = result[part]
    return result
