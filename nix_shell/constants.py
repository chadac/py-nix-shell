"""Constants and configuration paths for py-nix-shell."""

import os
import sys
from pathlib import Path

_DEFAULT_LOCAL_CACHE = Path.home() / ".cache" / "py-nix-shell" / "local"
LOCAL_CACHE_ROOT = Path(os.environ.get("PY_NIX_SHELL_CACHE", str(_DEFAULT_LOCAL_CACHE)))
"""Local cache directory for shells."""

CACHE_ROOT = (
    Path(os.environ.get("XDG_CACHE_HOME", "~/.cache")).expanduser() / "py-nix-shell"
)
"""Location of the cache directory used for persisting some shells."""

PKG_FLAKE_LOCK = Path(__file__).parent / "flake.lock"
"""Path to the `flake.lock` file distributed with the project."""
