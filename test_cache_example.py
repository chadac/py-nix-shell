#!/usr/bin/env python3
"""Example usage of the new cache module."""

import nix_shell

# Create a simple shell
shell = nix_shell.mk_shell(packages=["curl"])

# Load/cache it with history tracking
cached_shell = nix_shell.cache.load(
    shell, 
    history=5,  # Keep 5 recent builds
    use_global_cache=False  # Use local cache
)

print("Cache module implemented successfully!")
print(f"Build ID: {cached_shell.build_id}")