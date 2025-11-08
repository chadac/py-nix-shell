"""Assets are external resources that you would like to track with Nix.

Generally Nix requires stuff uses checksums... which is great for
security reasons, but keeping that stuff up-to-date can get a bit
frustrating.

`pynix` instead provides a convenient mechanism to auto-fetch, hash,
and store your assets in an `assets.lock` file.
"""


class Asset:
    pass


def nixhub(package: str, version: str = "latest") -> Asset:
    """
    Fetch a version of a package using the `python` version.

    Useful if you want to pull a package that is locked down
    to a verify specific version, and you'd like to build it
    as if you were using a specific `nixpkgs` version.
    """
    return NotImplemented


def github_release(owner: str, repo: str, version: str) -> Asset:
    raise NotImplementedError


def web(url: str) -> Asset:
    return NotImplemented
