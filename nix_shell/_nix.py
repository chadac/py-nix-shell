from functools import cache, cached_property
import json
from pathlib import Path
import subprocess
from typing import NotRequired, TypedDict, Unpack


class NixBuildArgs(TypedDict):
    file: NotRequired[Path | str]
    installable: NotRequired[str]
    ref: NotRequired[str]
    expr: NotRequired[str]
    impure: NotRequired[bool]
    include: NotRequired[dict[str, str]]


def _parse_args(
    **params: Unpack[NixBuildArgs],
) -> list[str]:
    args = []
    if "ref" in params:
        args += [params["ref"]]
    elif "expr" in params:
        args += ["--expr", params["expr"]]
    elif "file" in params:
        args += ["-f", str(params["file"])]
        if "installable" in params:
            args += [params["installable"]]
    if params.get("impure", False):
        args += ["--impure"]
    for key, value in params.get("include", {}).items():
        args += ["-I", f"{key}={value}"]
    return args


def _cmd(
    cmd: str | list[str] = "build",
    extra_args: list[str] = [],
    **params: Unpack[NixBuildArgs],
) -> str:
    args = _parse_args(**params) + extra_args

    if isinstance(cmd, str):
        cmds = [cmd]
    else:
        cmds = cmd

    return subprocess.check_output(["nix"] + cmds + args).decode()


def build(no_link: bool = False, **params: Unpack[NixBuildArgs]):
    extra_args = []
    if no_link:
        extra_args += ["--no-link"]
    return _cmd(extra_args=extra_args, **params)


def evaluate(
    raw: bool = True,
    **params: Unpack[NixBuildArgs],
):
    extra_args = []
    if raw:
        extra_args += ["--raw"]
    return _cmd("eval", extra_args=extra_args, **params)


@cache
def current_system() -> str:
    return evaluate(expr="builtins.currentSystem", impure=True)


@cache
def impure_nixpkgs_path() -> str:
    return evaluate(expr="<nixpkgs>", impure=True, raw=False).strip()


class derivation:
    @staticmethod
    def show(**params: Unpack[NixBuildArgs]):
        return _cmd(["derivation", "show"], **params)


class flake:
    @staticmethod
    def metadata(flake_ref: str) -> dict:
        return json.loads(subprocess.check_output(
            ["nix", "flake", "metadata", flake_ref, "--json"]
        ).decode())
