from pathlib import Path

from nix_shell import dsl
from nix_shell.cli import current_system
from nix_shell.dsl_utils import Context, get_nix_context


def use_shell_nix(
    shell_nix: Path = Path("shell.nix"),
    ctx: Context | None = None,
    **params: dsl.NixExpr,
) -> dsl.NixExpr:
    ctx = ctx or get_nix_context()

    p = dsl.StorePath.from_path(shell_nix)

    return (
        dsl.raw("import"),
        ctx[p],
        {
            **ctx,
        },
    )


def use_flake(
    flake_nix: Path | None = Path("flake.nix"),
    flake_lock: Path = Path("flake.lock"),
    output: str | None = None,
) -> dsl.NixExpr:
    if output is None:
        output = f"devShells.{current_system()}.default"
