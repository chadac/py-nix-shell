"""Constants and configuration paths for py-nix-shell."""

import os
from pathlib import Path


def _get_local_cache_root() -> Path:
    """Determine the local cache root, preferring virtualenv-local cache when available."""
    # Check if we're in a virtualenv
    venv_path = os.environ.get("VIRTUAL_ENV")
    if venv_path:
        # Use <venv_root>/var/cache/py-nix-shell when in a virtualenv
        venv_cache = Path(venv_path) / "var" / "cache" / "py-nix-shell"
        return venv_cache

    # Fall back to user's home cache directory
    default_cache = Path.home() / ".cache" / "py-nix-shell" / "local"
    return Path(os.environ.get("PY_NIX_SHELL_CACHE", str(default_cache)))


LOCAL_CACHE_ROOT = _get_local_cache_root()
"""Local cache directory for shells."""

CACHE_ROOT = (
    Path(os.environ.get("XDG_CACHE_HOME", "~/.cache")).expanduser() / "py-nix-shell"
)
"""Location of the cache directory used for persisting some shells."""

PKG_FLAKE_LOCK = Path(__file__).parent / "flake.lock"
"""Path to the `flake.lock` file distributed with the project."""
