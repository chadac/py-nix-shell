import os

import nix_shell

extra_packages = os.environ.get("NIX_EXTRA_PACKAGES", "").strip().split(",")

shell = nix_shell.mk_shell(
    packages=["curl", "openssl"] + [p for p in extra_packages if p],
)

# preserve this inside a virtualenv
shell.persist_venv()
