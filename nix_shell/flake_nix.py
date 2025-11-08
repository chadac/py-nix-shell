"""
Flake-based Nix shell management utilities.

This module provides functions to initialize and manage flake-based development shells.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from nix_shell import cli, dsl
from nix_shell.build import NixShell

if TYPE_CHECKING:
    from nix_shell.nix_context import NixContext

logger = logging.getLogger(__name__)


def init(*, minimal: bool = False, ctx: NixContext | None = None) -> None:
    """
    Load existing flake data into the NixContext.

    Requires that both flake.nix and flake.lock already exist.

    Args:
        minimal: If True, adds individual flake files to context for direct evaluation.
                If False, uses builtins.getFlake with locked reference.
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

        files = {
            "flake.nix": flake_nix_var,
            "flake.lock": flake_lock_var,
        }

        ctx["projectFlake"] = import_flake_from_files(files)
        logger.info("added flake files to context for direct evaluation")
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
    flake_nix_path = Path("flake.nix")
    flake_lock_path = Path("flake.lock")

    if not flake_nix_path.exists():
        raise FileNotFoundError("flake.nix not found. Run flake_nix.init() first.")

    # Check if this is a minimal setup (individual files) or full flake reference
    has_flake_files = any(
        str(flake_nix_path.resolve()) in str(path)
        or str(flake_lock_path.resolve()) in str(path)
        for path in ctx._files.keys()
    )

    if has_flake_files:
        # Minimal approach: evaluate flake directly from files
        # Build a Nix expression that imports the flake and accesses the target
        target_parts = target.split(".")

        # Create expression: (import ./flake.nix).outputs { ... }.devShells.${system}.default
        flake_var = ctx.path(flake_nix_path)
        ctx.path(flake_lock_path)  # Ensure lock file is added to context

        # For minimal flakes, we need to reconstruct the flake evaluation
        expr = dsl.let(
            flakeNix=dsl.call(dsl.raw("import"), flake_var),
            # Get system
            system=cli.current_system(),
            # Construct inputs (simplified for minimal case)
            inputs={
                "self": None,  # Will be replaced during evaluation
                "nixpkgs": dsl.builtins["getFlake"](
                    "github:NixOS/nixpkgs/nixos-unstable"
                ),
                "flake-utils": dsl.builtins["getFlake"]("github:numtide/flake-utils"),
            },
            in_=_build_nested_access(
                dsl.call(dsl.v("flakeNix")["outputs"], dsl.v("inputs")),
                target_parts + [dsl.v("system")],
            ),
        )
    else:
        # Full approach: use getFlake reference if available
        if "projectFlake" in ctx._vars:
            # Extract the target from the flake
            target_parts = target.split(".")

            # Only append system if not already specified in target
            system = cli.current_system()
            if system not in target_parts:
                target_parts.append(system)

            expr = _build_nested_access(ctx["projectFlake"], target_parts)
        else:
            raise ValueError(
                "No flake data found in context. Run flake_nix.init() first."
            )

    # Create NixShell from the expression
    shell = NixShell.from_expr_with_context(expr, ctx)
    return shell


def _build_nested_access(base_expr: Any, path_parts: list[Any]) -> Any:
    """Build nested attribute access expression: base.part1.part2.part3"""
    result = base_expr
    for part in path_parts:
        result = result[part]
    return result
