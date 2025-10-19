from nix_shell import devenv


def python_project(
    python_version: str | None = None,
    extra_python_pkgs: list[str] | None = [],
    uv: bool = False,
    poetry: bool = False,
) -> devenv.Module:
    opts = {"python": {"enable": True, "version": python_version}}
    if uv:
        opts["uv"] = {
            "enable": True,
        }
    return devenv.module(opts)
