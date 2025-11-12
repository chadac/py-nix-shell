from pathlib import Path

from nix_shell import dsl
from nix_shell.cli import current_system
from nix_shell.utils.dsl import NixContext


def use_shell_nix(
    shell_nix: Path = Path("shell.nix"),
    ctx: NixContext | None = None,
    **params: dsl.NixExpr,
) -> dsl.NixExpr:
    raise NotImplementedError()


def use_flake(
    flake_nix: Path | None = Path("flake.nix"),
    flake_lock: Path = Path("flake.lock"),
    output: str | None = None,
) -> dsl.NixExpr:
    if output is None:
        output = f"devShells.{current_system()}.default"
    raise NotImplementedError()
