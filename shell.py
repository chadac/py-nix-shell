"""
Development shell initialization script for py-nix-shell.

This script sets up a development environment using the nix_shell module.
If no shell configuration exists, it initializes a minimal flake-based setup.
"""

import nix_shell.cache
from nix_shell import flake_nix

flake_nix.init(minimal=True)  # initialize only with the flake.nix and flake.lock files
shell = flake_nix.devshell(target="devShells.default")

nix_shell.cache.load(
    shell,
    history=5,            # use
    use_global_context=5,
)

shell = nix_shell.cache.load(shell)
