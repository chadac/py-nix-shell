#!/usr/bin/env python3
"""Test that the new NixBuild.load() method works."""

import json
import tempfile
from pathlib import Path

import nix_shell

# Create a simple shell
shell = nix_shell.mk_shell(packages=["curl"])

# Test the new load() method directly
with tempfile.TemporaryDirectory() as tmpdir:
    tmppath = Path(tmpdir)
    json_path = tmppath / "test.json"

    # Save some test data
    test_data = {"build_id": shell.build_id, "test_value": "loaded_from_cache"}
    with json_path.open("w") as f:
        json.dump(test_data, f)

    # Test loading
    shell.load(json_path)
    print("NixBuild.load() method works!")

# Test via cache module
cached_shell = nix_shell.cache.load(shell, history=3)
print("Cache module using NixBuild.load() works!")
print(f"Build ID: {cached_shell.build_id}")
