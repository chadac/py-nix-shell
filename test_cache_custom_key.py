#!/usr/bin/env python3
"""Example usage of the internal _load method with custom cache key."""

import nix_shell

# Create a simple shell
shell = nix_shell.mk_shell(packages=["curl"])

# Use internal _load method with custom key
cached_shell = nix_shell.cache._load(
    shell, cache_key="my-custom-shell-key", history=5, use_global_cache=False
)

print("Internal _load method with custom cache key works!")
print(f"Cache key: my-custom-shell-key")
print(f"Build ID: {cached_shell.build_id}")

# Regular load still works
regular_cached = nix_shell.cache.load(shell, history=3)
print(f"Regular load build ID: {regular_cached.build_id}")
