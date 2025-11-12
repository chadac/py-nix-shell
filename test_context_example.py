#!/usr/bin/env python3
"""Example usage of the new context manager API."""

from pathlib import Path

import nix_shell

# Example usage of the context manager
with nix_shell.context() as ctx:
    # Add some files to the context
    makefile = ctx.path(Path("./Makefile"))  # hypothetical file

    # Add some variables
    ctx["myVar"] = nix_shell.dsl.str("hello world")

    # Create an expression that uses the context
    expr = nix_shell.dsl.mkShell(
        {
            "packages": [nix_shell.dsl.pkgs["curl"]],
            "shellHook": nix_shell.dsl.str(f"echo 'Using makefile: {makefile}'"),
        }
    )

    # Build shell with context
    shell = nix_shell.build.NixShell.from_expr_with_context(expr, ctx)

print("Context manager API implemented successfully!")
