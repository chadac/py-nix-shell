"""Interface for invoking the Nix CLI from Python."""

import json
import subprocess
from functools import cache
from pathlib import Path
from typing import NotRequired, TypedDict, Unpack

from nix_shell.utils import format_nix

from .exceptions import wrap_subprocess_error


class NixBuildArgs(TypedDict):
    """
    Common arguments passed to commands like `nix build`.

    Mostly "Common evaluation options" and "Options that change the
    interpretation of installables".

    Either `file` + `installable`, `ref` or `expr` are required.

    Args:
        file (Path | str, optional): Equivalent to `--file`.
        installable (str): Path to installable if `--file` is specified.
        ref (str): [Flake reference](https://nix.dev/manual/nix/2.28/command-ref/new-cli/nix3-flake.html#url-like-syntax) to build.
        expr (str): Nix expression to build.
        impure (bool): Whether to run nix in impure evaluation mode. Defaults to `False`.
        include (tuple[tuple[str, str]]): Equivalent to `--include`.
    """

    file: NotRequired[Path | str]
    installable: NotRequired[str]
    ref: NotRequired[str]
    expr: NotRequired[str]
    impure: NotRequired[bool]
    include: NotRequired[tuple[tuple[str, str], ...]]


def _parse_args(
    **params: Unpack[NixBuildArgs],
) -> list[str]:
    args = []
    if "ref" in params:
        args += [params["ref"]]
    elif "expr" in params:
        args += ["--expr", format_nix(params["expr"])]
    elif "file" in params:
        args += ["-f", str(params["file"])]
        if "installable" in params:
            args += [params["installable"]]
    if params.get("impure", False):
        args += ["--impure"]
    for key, value in params.get("include", []):
        args += ["-I", f"{key}={value}"]
    return args


@wrap_subprocess_error
def _cmd(
    cmd: str | list[str] = "build",
    extra_args: list[str] = [],
    **params: Unpack[NixBuildArgs],
) -> str:
    import logging

    args = _parse_args(**params) + extra_args

    if isinstance(cmd, str):
        cmds = [cmd]
    else:
        cmds = cmd

    full_cmd = ["nix"] + cmds + args
    logger = logging.getLogger("py-nix-shell")

    # Log the command at DEBUG level
    logger.debug(f"Running command: {' '.join(full_cmd)}")

    # Check if we should capture stderr for -vvv mode
    if logger.isEnabledFor(logging.DEBUG):
        full_cmd += ["--show-trace"]
        # For debug mode, capture stderr to include in logs
        try:
            result = subprocess.run(
                full_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            if result.stderr:
                logger.debug(f"Command stderr: {result.stderr}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            # Log the error details before re-raising
            if e.stderr:
                logger.debug(f"Command failed stderr: {e.stderr}")
            if e.stdout:
                logger.debug(f"Command failed stdout: {e.stdout}")
            raise
    else:
        # Normal mode - just use check_output
        return subprocess.check_output(full_cmd).decode()


def build(
    out_link: Path | None = None,
    no_link: bool = False,
    print_out_paths: bool = False,
    **params: Unpack[NixBuildArgs],
):
    """Run `nix build`"""
    extra_args = []
    if out_link:
        extra_args += ["--out-link", str(out_link.absolute())]
    if no_link:
        extra_args += ["--no-link"]
    if print_out_paths:
        extra_args += ["--print-out-paths"]
    return _cmd(extra_args=extra_args, **params)


def print_dev_env(**params: Unpack[NixBuildArgs]):
    return _cmd("print-dev-env", **params)


def evaluate(
    raw: bool = True,
    **params: Unpack[NixBuildArgs],
):
    """
    Run `nix eval`

    Named `evaluate` because `eval` is a reserved word in Python.
    """
    extra_args = []
    if raw:
        extra_args += ["--raw"]
    return _cmd("eval", extra_args=extra_args, **params)


@wrap_subprocess_error
def _shell_cmd(
    cmd: str | list[str] = "develop",
    extra_args: list[str] = [],
    **params: Unpack[NixBuildArgs],
):
    args = _parse_args(**params) + extra_args
    if isinstance(cmd, str):
        cmds = [cmd]
    else:
        cmds = cmd
    return subprocess.run(
        ["nix"] + cmds + args,
        check=True,
        text=True,
    )


def develop(**params: Unpack[NixBuildArgs]):
    return _shell_cmd(**params)


def shell(**params: Unpack[NixBuildArgs]):
    return _shell_cmd(cmd="shell", **params)


@cache
def current_system() -> str:
    """
    The current system according to `nix`.

    This returns the result of `nix eval --impure --raw 'builtins.currentSystem'`.
    """
    return evaluate(expr="builtins.currentSystem", impure=True)


@cache
def impure_nixpkgs_path() -> str:
    """
    Return the path of the current `nixpkgs` channel.

    This grabs the result of `nix eval --impure '<nixpkgs>'`
    """
    return evaluate(expr="<nixpkgs>", impure=True, raw=True)


class derivation:
    @staticmethod
    def show(**params: Unpack[NixBuildArgs]):
        """Run `nix derivation show`"""
        return _cmd(["derivation", "show"], **params)


class flake:
    @staticmethod
    @wrap_subprocess_error
    def metadata(flake_ref: str) -> dict:
        """Run `nix flake metadata`"""
        return json.loads(
            subprocess.check_output(
                ["nix", "flake", "metadata", flake_ref, "--json"]
            ).decode()
        )


class store:
    @staticmethod
    @wrap_subprocess_error
    def add(path: Path) -> str:
        return subprocess.check_output(
            ["nix", "store", "add", str(path.absolute())]
        ).decode()
