"""
Wrapper for the `subprocess` module with Nix support.
"""

import subprocess
from typing import Any, Callable

from nix_shell.build import NixShell
from nix_shell.builders import (
    FlakeRefParams,
    MkNixParams,
    MkShellParams,
    from_flake,
    from_nix,
    mk_shell,
)


def _infer_shell(*args, **kwargs) -> tuple[NixShell, Any, Any]:
    shell_cmd: Callable[..., NixShell]
    shell_kwargs_keys: set[str]
    if "flake" in kwargs:
        shell_kwargs_keys = set(FlakeRefParams.__annotations__.keys())
        shell_cmd = from_flake
    elif "nix_file" in kwargs:
        shell_kwargs_keys = set(MkNixParams.__annotations__.keys())
        shell_cmd = from_nix
    else:
        if "packages" not in kwargs:
            if isinstance(args[0], list):
                kwargs["packages"] = [args[0][0]]
            else:
                kwargs["packages"] = [args[0].split(" ", 1)[0]]
        shell_kwargs_keys = set(MkShellParams.__annotations__.keys())
        shell_cmd = mk_shell
    shell_kwargs = {
        key: value for key, value in kwargs.items() if key in shell_kwargs_keys
    }
    nix = shell_cmd(**shell_kwargs)
    new_kwargs = {
        key: value for key, value in kwargs.items() if key not in shell_kwargs_keys
    }
    return nix, args, new_kwargs


def run(*args, **kwargs) -> subprocess.CompletedProcess:
    nix, new_args, new_kwargs = _infer_shell(*args, **kwargs)
    return nix.run(*new_args, **new_kwargs)


def check_output(*args, **kwargs) -> bytes | str:
    nix, new_args, new_kwargs = _infer_shell(*args, **kwargs)
    return nix.check_output(*new_args, **new_kwargs)


def Popen(*args, **kwargs) -> subprocess.Popen[str] | subprocess.Popen[bytes]:
    nix, new_args, new_kwargs = _infer_shell(*args, **kwargs)
    return nix.Popen(*new_args, **new_kwargs)


def call(*args, **kwargs) -> int:
    nix, new_args, new_kwargs = _infer_shell(*args, **kwargs)
    return nix.call(*new_args, **new_kwargs)


def check_call(*args, **kwargs) -> int:
    nix, new_args, new_kwargs = _infer_shell(*args, **kwargs)
    return nix.check_call(*new_args, **new_kwargs)


def getoutput(*args, **kwargs) -> str:
    nix, new_args, new_kwargs = _infer_shell(*args, **kwargs)
    return nix.getoutput(*new_args, **new_kwargs)


def getstatusoutput(*args, **kwargs) -> tuple[int, str]:
    nix, new_args, new_kwargs = _infer_shell(*args, **kwargs)
    return nix.getstatusoutput(*new_args, **new_kwargs)
