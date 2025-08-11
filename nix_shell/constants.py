import os
import sys
from pathlib import Path

LOCAL_CACHE_ROOT = Path(sys.executable).parent.parent / "var" / "cache" / "nix-shell"
CACHE_ROOT = (
    Path(os.environ.get("XDG_CACHE_HOME", "~/.cache")).expanduser() / "py-nix-shell"
)
"""Location of the cache directory used for persisting some shells."""


PKG_FLAKE_LOCK = Path(__file__).parent / "flake.lock"
"""Path to the `flake.lock` file distributed with the project."""
