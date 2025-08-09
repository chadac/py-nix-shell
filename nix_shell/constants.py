import os
from pathlib import Path


CACHE_ROOT = (
    Path(os.environ.get("XDG_CACHE_HOME", "~/.cache")).expanduser() / "py-nix-shell"
)
