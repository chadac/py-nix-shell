from dataclasses import dataclass, field
from pathlib import Path
from typing import NotRequired, TypedDict, Unpack

from nix_shell import cli, dsl
from nix_shell.build import NixShell
from nix_shell.constants import PKG_FLAKE_LOCK
from nix_shell.flake import (
    FlakeRefLock,
    fetch_locked_from_flake_ref,
    get_locked_from_impure_nixpkgs,
    get_locked_from_lockfile,
)
from nix_shell.nix_context import get_nix_context


class NixpkgsParams(TypedDict):
    """
    Parameters to customize where `nixpkgs` is sourced from.

    Args:
        nixpkgs (str): If present, the [flake reference URL](https://nix.dev/manual/nix/2.28/command-ref/new-cli/nix3-flake.html#url-like-syntax) for the `nixpkgs` version
        use_global_nixpkgs (bool): If true, uses the `nixpkgs` version from the local flake registry (`nix flake metadata nixpkgs`). (default: `False`)
        flake_lock (Path | str): If present, uses the `nixpkgs` version from a `flake.lock` file provided at the given path.
        flake_lock_name (str): The name of the `nixpkgs` entry in the `flake.lock` file (default: `nixpkgs`)
    """

    nixpkgs: NotRequired[str]
    use_global_nixpkgs: NotRequired[bool]
    flake_lock: NotRequired[Path | str]
    flake_lock_name: NotRequired[str]


class FlakeRefParams(TypedDict):
    """
    Parameters to provide for building Flake shells.

    Args:
        flake (str): The Flake reference URL. See [the Nix docs](https://nix.dev/manual/nix/2.28/command-ref/new-cli/nix3-flake.html#url-like-syntax) for more details
    """

    flake: str


class MkNixParams(NixpkgsParams):
    """
    Parameters for building a shell from a `shell.nix` file.

    Args:
        nix_file (Path | str): Path to the `shell.nix` file.
    """

    nix_file: Path | str


class MkShellParams(NixpkgsParams):
    """
    Parameters for dynamically building a shell from Python.

    Args:
        packages (list[str]): List of `nixpkgs` packages to install. (default: `[]`)
        inputs_from (list[str]): List of `nixpkgs` packages to use inputs from. (default: `[]`)
        build_inputs (list[str]): List of `nixpkgs` packages to use as build inputs. (default: `[]`)
        library_path (list[str]): List of `nixpkgs` packages to add to the LD_LIBRARY_PATH. (default: `[]`)
        shell_hook (str): Additional (bash) initialization commands to run once the shell initializes. (default: `""`)
        system (str): The system to build for. The default is the current system that `py-nix-shell` is running on.
    """

    packages: NotRequired[list[str]]
    inputs_from: NotRequired[list[str]]
    build_inputs: NotRequired[list[str]]
    library_path: NotRequired[list[str]]
    shell_hook: NotRequired[list[str]]
    extra_args: NotRequired[dict[str, dsl.NixExpr]]
    system: NotRequired[str]


def from_flake(**kwargs: Unpack[FlakeRefParams]) -> NixShell:
    """Create a Nix shell from a flake."""
    return NixShell.create(ref=kwargs["flake"])


def lock_nixpkgs(**kwargs: Unpack[NixpkgsParams]) -> FlakeRefLock:
    """Determine the version of `nixpkgs` to use."""
    if "nixpkgs" in kwargs:
        locked = fetch_locked_from_flake_ref(kwargs["nixpkgs"])
    elif "flake_lock" in kwargs:
        locked = get_locked_from_lockfile(
            kwargs["flake_lock"], kwargs.get("flake_lock_name", "nixpkgs")
        )
    elif kwargs.get("use_global_nixpkgs", False):
        locked = get_locked_from_impure_nixpkgs()
    else:
        locked = get_locked_from_lockfile(
            PKG_FLAKE_LOCK, kwargs.get("flake_lock_name", "nixpkgs")
        )
    return locked


def from_nix(**kwargs: Unpack[MkNixParams]) -> NixShell:
    """Create a Nix shell from a `shell.nix` file."""
    include: dict[str, str] = {}
    if "nixpkgs" in kwargs:
        include["nixpkgs"] = cli.flake.metadata(kwargs["nixpkgs"])["locked"]["path"]
    elif "use_global_nixpkgs" in kwargs:
        include["nixpkgs"] = get_locked_from_impure_nixpkgs()["path"]
    elif "flake_lock" in kwargs:
        include["nixpkgs"] = get_locked_from_lockfile(  # type: ignore
            kwargs["flake_lock"], kwargs.get("flake_lock_name", "nixpkgs")
        )["path"]
    return NixShell.create(
        file=kwargs["nix_file"],
        include=tuple(sorted(include.items())),
    )


@dataclass
class NixShellBuilder(dsl.NixComplexType):
    """Builder for creating mkShell Nix expressions with package dependencies and configuration."""

    packages: list[str | dsl.NixExpr] = field(default_factory=list)
    inputs_from: list[str | dsl.NixExpr] = field(default_factory=list)
    build_inputs: list[str | dsl.NixExpr] = field(default_factory=list)
    library_path: list[str | dsl.NixExpr] = field(default_factory=list)
    extra_args: dict[str, dsl.NixExpr] = field(default_factory=lambda: {})
    shell_hook: list[str] = field(default_factory=list)
    system: str = field(default_factory=cli.current_system)

    def add_package(self, pkg: str | dsl.NixExpr) -> None:
        """Add a package to the shell environment."""
        self.packages.append(pkg)

    def add_input(self, pkg: str | dsl.NixExpr) -> None:
        """Add a package to inputsFrom for the shell."""
        self.inputs_from.append(pkg)

    def add_build_input(self, pkg: str | dsl.NixExpr) -> None:
        """Add a package to buildInputs for the shell."""
        self.build_inputs.append(pkg)

    def _nix_library_path(self) -> str | None:
        """Generate the LD_LIBRARY_PATH for the shell from library_path packages."""
        if self.library_path:
            return f"${{pkgs.lib.makeLibraryPath ({dsl.dumps(_with_pkgs(list(self.library_path)))})}}"
        else:
            return None

    @property
    def _expr(self) -> dsl.NixExpr:
        """Generate the mkShell Nix expression for this builder."""
        ctx = get_nix_context()

        shell_hook = list(self.shell_hook)
        if library_path := self._nix_library_path():
            shell_hook.append(
                f'export LD_LIBRARY_PATH=\\"{library_path}:$LD_LIBRARY_PATH\\"'
            )

        return ctx["pkgs"]["mkShell"](
            {
                "packages": _with_pkgs(self.packages),
                "inputsFrom": _with_pkgs(self.inputs_from),
                "buildInputs": _with_pkgs(self.build_inputs),
                "shellHook": "\n".join(shell_hook),
                **self.extra_args,
            }
        )

    def dumps(self) -> str:
        """Serialize the shell builder to a Nix expression string."""
        return dsl.dumps(self._expr)


def mk_shell_expr(
    **kwargs: Unpack[MkShellParams],
) -> str:
    """Generate the `shell.nix` expresssion for `mk_shell`"""
    shell = NixShellBuilder(
        packages=kwargs.get("packages", []),  # type: ignore
        inputs_from=kwargs.get("inputs_from", []),  # type: ignore
        build_inputs=kwargs.get("build_inputs", []),  # type: ignore
        library_path=kwargs.get("library_path", []),  # type: ignore
        extra_args=kwargs.get("extra_args", {}),
        shell_hook=kwargs.get("shell_hook", []),
        system=kwargs.get("system", cli.current_system()),
    )
    return dsl.dumps(shell)


def _with_pkgs(packages: list[str | dsl.NixExpr]) -> list[dsl.NixExpr]:
    """Convert a list of package names/expressions to a Nix list with pkgs prefix."""
    nix_packages: list[dsl.NixExpr] = []
    for pkg in packages:
        if isinstance(pkg, str):
            nix_packages.append(dsl.call(dsl.raw(f"pkgs.{pkg}")))
        else:
            nix_packages.append(pkg)
    return nix_packages


def mk_shell(**kwargs: Unpack[MkShellParams]) -> NixShell:
    """Create a Nix shell dynamically from Python."""
    shell_expr = mk_shell_expr(**kwargs)
    return NixShell.create(expr=shell_expr)
