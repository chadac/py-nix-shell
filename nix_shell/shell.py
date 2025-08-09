from __future__ import annotations

from dataclasses import dataclass
import json
from functools import cached_property
from pathlib import Path
import subprocess
from typing import Literal, TypedDict


class DevEnvVar(TypedDict):
    var_type: Literal["var", "exported", "array"]
    value: str


class DevEnv(TypedDict):
    bash_functions: dict[str, str]
    variables: dict[str, DevEnvVar]


def nix_dev_env(
    ref: str | None = None,
    expr: str | None = None,
    impure: bool = False,
) -> DevEnv:
    if ref is not None and expr is not None:
        raise ValueError("'ref' and 'expr' cannot both be set.")
    if ref is None and expr is None:
        raise ValueError("either 'ref' or 'expr' must be set.")
    cmd = ["nix", "print-dev-env", "--json"]
    if ref is not None:
        cmd += [ref]
    else:
        cmd += ["--expr", expr]
    if impure:
        cmd += ["--impure"]
    result = subprocess.check_output(cmd).decode()
    return json.loads(result)


@dataclass
class NixShell:
    packages: list[str] | None = None
    shell_nix: str | None = None
    flake_ref: str | None = None


    def run(*args, **kwargs) -> subprocess.CompletedProcess:
        raise NotImplemented
