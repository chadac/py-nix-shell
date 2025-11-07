"""Template functions for common project setups."""

from nix_shell.third_party import devenv


def python_project(
    python_version: str | None = None,
    extra_python_pkgs: list[str] | None = [],
    uv: bool = False,
    poetry: bool = False,
) -> devenv.Module:
    """Create a devenv module for a Python project with common tools."""
    opts = {"python": {"enable": True, "version": python_version}}
    if uv:
        opts["uv"] = {
            "enable": True,
        }
    return devenv.module(opts)
