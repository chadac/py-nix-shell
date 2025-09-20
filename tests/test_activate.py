"""
Need something more involved to ensure `shell.activate()` works properly
"""

import pytest

from nix_shell.builders import mk_shell

shell = mk_shell(
    packages=["curl", "which", "openssl"],
    library_path=["curl"],
    nixpkgs="tarball+https://github.com/NixOS/nixpkgs/archive/23.11.tar.gz",
)

shell.persist_venv(name="test-activate")


@pytest.mark.isolate()
def test_activate_works_in_subprocess():
    shell.activate()

    # subprocess should now work as if it's inside the shell
    import subprocess

    assert (
        subprocess.check_output(["which", "curl"]).decode().strip()
        == "/nix/store/r304lglsa9i2jy5hpbdz48z3j3x2n4a6-curl-8.4.0-bin/bin/curl"
    )


@pytest.mark.isolate()
def test_acitvate_works_in_ctypes():
    shell.activate()

    import ctypes.util

    assert ctypes.util.find_library("curl") == "libcurl.so.4"
