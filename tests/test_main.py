import pytest

from pathlib import Path

import nix_shell


def test_can_infer_hello():
    assert nix_shell.check_output(["hello"]).decode() == "Hello, world!\n"


def test_can_infer_curl():
    # it should be able to run basic network commands
    # note: needs insecure for https since it doesn't have shell certs
    nix_shell.run(["curl", "https://google.com", "--insecure"], check=True)


@pytest.mark.parametrize("key", list(range(10)))
def test_can_use_curl_with_openssl(key: int):
    # it should be able to query with tls when it includes openssl
    nix_shell.run(["curl", "https://google.com"], packages=["curl", "openssl"])


def test_can_use_lockfile():
    nix_shell.run(
        ["curl", "https://google.com"],
        packages=["curl", "openssl"],
        flake_lock=Path(__file__).parent.parent / "flake.lock"
    )
