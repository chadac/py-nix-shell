#!/usr/bin/env python3
"""Example shell.py that uses a flake for the Nix environment."""

from nix_shell import flake_nix

# Initialize flake with minimal mode to avoid git requirements
flake_nix.init(minimal=True)

# Create a shell from the devShell output
shell = flake_nix.devshell(target="devShells.x86_64-linux.default")
