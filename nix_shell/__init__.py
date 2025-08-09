import subprocess
from typing import Any, Callable, get_type_hints

from nix_shell.builders import FlakeRefParams, MkNixParams, MkShellParams, from_flake, mk_nix
from nix_shell.nix_subprocess import NixSubprocess
from nix_shell.builders import mk_shell


def _infer_shell(*args, **kwargs) -> tuple[NixSubprocess, Any, Any]:
    shell_cmd: Callable[..., NixSubprocess]
    shell_kwargs_keys: set[str]
    if "flake" in kwargs:
        shell_kwargs_keys = set(FlakeRefParams.__annotations__.keys())
        shell_cmd = from_flake
    elif "nix_file" in kwargs:
        shell_kwargs_keys = set(MkNixParams.__annotations__.keys())
        shell_cmd = mk_nix
    else:
        if "packages" not in kwargs:
            if isinstance(args[0], list):
                kwargs["packages"] = [args[0][0]]
            else:
                kwargs["packages"] = [args[0].split(" ", 1)[0]]
        shell_kwargs_keys = set(MkShellParams.__annotations__.keys())
        shell_cmd = mk_shell
    shell_kwargs = {key: value for key, value in kwargs.items() if key in shell_kwargs_keys}
    nix = shell_cmd(**shell_kwargs)
    new_kwargs = {key: value for key, value in kwargs.items() if key not in shell_kwargs_keys}
    return nix, args, new_kwargs


def run(*args, **kwargs) -> subprocess.CompletedProcess:
    nix, new_args, new_kwargs = _infer_shell(*args, **kwargs)
    return nix.run(*new_args, **new_kwargs)


def check_output(*args, **kwargs) -> bytes:
    nix, new_args, new_kwargs = _infer_shell(*args, **kwargs)
    return nix.check_output(*new_args, **new_kwargs)


def Popen(*args, **kwargs) -> subprocess.Popen[str]:
    nix, new_args, new_kwargs = _infer_shell(*args, **kwargs)
    return nix.Popen(*new_args, **new_kwargs)



__all__ = [
    "run",
    "check_output",
    "Popen",
    "mk_shell",
]
