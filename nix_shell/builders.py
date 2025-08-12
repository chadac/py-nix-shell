from pathlib import Path
from typing import NotRequired, TypedDict, Unpack

from nix_shell import _nix, nixlang
from nix_shell.constants import PKG_FLAKE_LOCK
from nix_shell.flake import (
    get_impure_nixpkgs_ref,
    get_ref_from_lockfile,
    to_fetch_tree,
)
from nix_shell.nix_subprocess import NixSubprocess


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
    """

    packages: NotRequired[list[str]]
    inputs_from: NotRequired[list[str]]
    build_inputs: NotRequired[list[str]]
    library_path: NotRequired[list[str]]
    shell_hook: NotRequired[str]


def _pkgs_list(pkgs: list[str]) -> nixlang.NixValue:
    return nixlang.with_("pkgs", [nixlang.raw(pkg) for pkg in pkgs])


def from_flake(**kwargs: Unpack[FlakeRefParams]) -> NixSubprocess:
    """Create a Nix shell from a flake."""
    return NixSubprocess.build(ref=kwargs["flake"])


def parse_nixpkgs_tree(**kwargs: Unpack[NixpkgsParams]) -> dict[str, nixlang.NixValue]:
    """Determine the version of `nixpkgs` to use."""
    if "nixpkgs" in kwargs:
        nixpkgs_tree = to_fetch_tree(kwargs["nixpkgs"])
    elif "flake_lock" in kwargs:
        flake_ref = get_ref_from_lockfile(
            kwargs["flake_lock"], kwargs.get("flake_lock_name", "nixpkgs")
        )
        nixpkgs_tree = to_fetch_tree(flake_ref)
    elif kwargs.get("use_global_nixpkgs", False):
        flake_ref = get_impure_nixpkgs_ref()
        nixpkgs_tree = to_fetch_tree(flake_ref)
    else:
        flake_ref = get_ref_from_lockfile(
            PKG_FLAKE_LOCK, kwargs.get("flake_lock_name", "nixpkgs")
        )
        nixpkgs_tree = to_fetch_tree(flake_ref)
    return nixpkgs_tree


def from_nix(**kwargs: Unpack[MkNixParams]) -> NixSubprocess:
    """Create a Nix shell from a `shell.nix` file."""
    include: dict[str, str] = {}
    if "nixpkgs" in kwargs:
        include["nixpkgs"] = _nix.flake.metadata(kwargs["nixpkgs"])["locked"]["path"]
    elif "use_global_nixpkgs" in kwargs:
        include["nixpkgs"] = get_impure_nixpkgs_ref()["path"]
    elif "flake_lock" in kwargs:
        include["nixpkgs"] = get_ref_from_lockfile(  # type: ignore
            kwargs["flake_lock"], kwargs.get("flake_lock_name", "nixpkgs")
        )["path"]
    return NixSubprocess.build(
        file=kwargs["nix_file"],
        include=tuple(sorted(include.items())),
    )


def mk_shell_expr(
    **kwargs: Unpack[MkShellParams],
) -> str:
    """Generate the `shell.nix` expresssion for `mk_shell`"""
    nixpkgs_tree = parse_nixpkgs_tree(**kwargs)  # type: ignore[misc]
    expr = nixlang.let(
        **nixpkgs_tree,
        pkgs=nixlang.call(
            "import",
            nixlang.raw("nixpkgs"),
            nixlang.attrs(
                system=_nix.current_system(),
            ),
        ),
        in_=nixlang.call(
            "pkgs.mkShell",
            nixlang.attrs(
                packages=_pkgs_list(kwargs.get("packages", [])),
                inputsFrom=_pkgs_list(kwargs.get("inputs_from", [])),
                buildInputs=_pkgs_list(kwargs.get("build_inputs", [])),
                shellHook=f"""
export LD_LIBRARY_PATH=${{pkgs.lib.makeLibraryPath ({nixlang.dumps(_pkgs_list(kwargs.get("library_path", [])))})}}:$LD_LIBRARY_PATH
"""
                + kwargs.get("shell_hook", ""),
            ),
        ),
    )
    return nixlang.dumps(expr)


def mk_shell(**kwargs: Unpack[MkShellParams]) -> NixSubprocess:
    """Create a Nix shell dynamically from Python."""
    shell_expr = mk_shell_expr(**kwargs)
    return NixSubprocess.build(expr=shell_expr)
