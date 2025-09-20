import argparse
import runpy
from pathlib import Path

from nix_shell.build import NixShell


def _get_shell(shell_py: Path = Path("./shell.py")) -> NixShell:
    module = runpy.run_path(str(shell_py.absolute()))
    assert "shell" in module, f"{shell_py} must declare a global `shell` variable"
    assert isinstance(module["shell"], NixShell), (
        f"{shell_py} must declare a global `shell` variable of type `NixShell`"
    )
    return module["shell"]  # type: ignore


def activate(shell_py: Path = Path("./shell.py"), cmd: str | None = None) -> None:
    shell = _get_shell(shell_py)

    # Run interactive bash shell
    shell.run(cmd or shell.builder)


def print_dev_env(shell_py: Path = Path("./shell.py")) -> None:
    shell = _get_shell(shell_py)
    print(shell.dev_env)


def main():
    parser = argparse.ArgumentParser(
        prog="py-nix-shell", description="Create fast Nix shells"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    activate_parser = subparsers.add_parser("activate", help="Spawns a new shell.")
    activate_parser.add_argument(
        "shell_py",
        type=str,
        nargs="?",
        default="./shell.py",
        help="Path to the shell.py (default=shell.py)",
    )
    activate_parser.add_argument(
        "-c",
        "--cmd",
        type=str,
        help="Name of shell command to run (default is builder for derivation)",
    )

    shellenv_parser = subparsers.add_parser(
        "print-dev-env", help="Alias for `print-dev-env` on a shell."
    )
    shellenv_parser.add_argument(
        "shell_py",
        type=str,
        nargs="?",
        default="./shell.py",
        help="Path to the shell.py (default=shell.py)",
    )

    args = parser.parse_args()
    match args.command:
        case "activate":
            activate(Path(args.shell_py), args.cmd)
        case "print-dev-env":
            print_dev_env(Path(args.shell_py))
        case _:
            # should be unreachable
            raise ValueError("unknown command")
