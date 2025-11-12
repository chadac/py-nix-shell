#!/usr/bin/env python3
"""Test the new CacheHistory class."""

import tempfile
import time
from pathlib import Path

import nix_shell

# Create a shell
shell = nix_shell.mk_shell(packages=["curl"])

# Test CacheHistory class directly
with tempfile.TemporaryDirectory() as tmpdir:
    history_file = Path(tmpdir) / "test_history.json"
    history = nix_shell.cache.CacheHistory(history_file, max_history=3)

    # Test push() method with NixBuild objects
    shells = []
    for i in range(5):  # Add more than max_history to test cleanup
        test_shell = nix_shell.mk_shell(packages=[f"test-package-{i}"])
        shells.append(test_shell)
        # Add alias for some entries
        alias_key = f"test-key-{i}" if i % 2 == 0 else None
        history.push(test_shell, alias_key)
        time.sleep(0.01)  # Small delay to ensure different timestamps

    print(f"History entries after pushing 5 items (max=3): {len(history._entries)}")

    # Test peek() method
    latest = history.peek()
    if latest:
        print(f"Latest entry: {latest['build_id']}")

    # Test get() method with aliases
    found = history.get("test-key-4")  # Should resolve via alias
    if found:
        print(f"Found entry via alias: {found['build_id'][:8]}...")

    # Test direct build_id lookup
    if shells:
        direct = history.get(shells[0].build_id)
        if direct:
            print(f"Found entry via build_id: {direct['build_id'][:8]}...")

    not_found = history.get("non-existent")
    print(f"Non-existent entry: {not_found}")

    print(f"Aliases in history: {len(history._aliases)}")

# Test integration with cache.load()
cached_shell = nix_shell.cache.load(shell, history=5)
print(f"Cache integration works! Build ID: {cached_shell.build_id[:8]}...")

print("CacheHistory class implementation complete!")
