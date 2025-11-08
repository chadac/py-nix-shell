#!/usr/bin/env python3
"""Example shell.py that uses a flake for the Nix environment."""

from nix_shell import flake_nix
from nix_shell.cache import use_cache

# Initialize flake with minimal mode and include additional files
flake_nix.init(minimal=True, files=["devenv.nix"])

# Enable caching
use_cache()

# Create a shell from the devShell output
shell = flake_nix.devshell()
