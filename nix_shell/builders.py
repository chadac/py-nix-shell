from functools import cache
from pathlib import Path
from typing import NotRequired, TypedDict, Unpack
from nix_shell import nixlang, _nix
from nix_shell.flake import FlakeRef, get_impure_nixpkgs_ref, get_ref_from_lockfile, to_fetch_tree
from nix_shell.nix_subprocess import NixSubprocess



class FlakeRefParams(TypedDict):
    flake: str


class MkNixParams(TypedDict):
    nix_file: Path
    nixpkgs: NotRequired[str]
    use_global_nixpkgs: NotRequired[bool]
    flake_lock: NotRequired[Path | str]
    flake_lock_name: NotRequired[str]


class MkShellParams(TypedDict):
    packages: NotRequired[list[str]]
    inputs_from: NotRequired[list[str]]
    build_inputs: NotRequired[list[str]]
    library_path: NotRequired[list[str]]
    shell_hook: NotRequired[str]
    nixpkgs: NotRequired[FlakeRef]
    flake_lock: NotRequired[Path]
    flake_lock_name: NotRequired[str]


def _pkgs_list(pkgs: list[str]) -> nixlang.NixValue:
    return nixlang.with_(
        "pkgs",
        [nixlang.raw(pkg) for pkg in pkgs]
    )


def from_flake(**kwargs: Unpack[FlakeRefParams]) -> NixSubprocess:
    return NixSubprocess.build(ref=kwargs["flake"])


def mk_nix(**kwargs: Unpack[MkNixParams]) -> NixSubprocess:
    include = {}
    if "nixpkgs" in kwargs:
        include["nixpkgs"] = _nix.flake.metadata(kwargs["nixpkgs"])["locked"]["path"]
    elif "use_global_nixpkgs" in kwargs:
        include["nixpkgs"] = get_impure_nixpkgs_ref()["path"]
    elif "flake_lock" in kwargs:
        include["nixpkgs"] = get_ref_from_lockfile(
            kwargs["flake_lock"], kwargs.get("flake_lock_name", "nixpkgs")
        )["path"]
    return NixSubprocess.build(
        file=kwargs["nix_file"],
        include=include,
    )


def mk_shell_expr(
    **kwargs: Unpack[MkShellParams],
) -> str:
    if "nixpkgs" in kwargs:
        nixpkgs_args = to_fetch_tree(kwargs["nixpkgs"])
    elif "flake_lock" in kwargs:
        flake_ref = get_ref_from_lockfile(
            kwargs["flake_lock"],
            kwargs.get("flake_lock_name", "nixpkgs")
        )
        nixpkgs_args = to_fetch_tree(flake_ref)
    else:
    # elif kwargs.get("use_global_nixpkgs", False):
        flake_ref = get_impure_nixpkgs_ref()
        nixpkgs_args = to_fetch_tree(flake_ref)
    # else:
    #     # TODO: Lock to the `flake.lock` in this package
    #     raise NotImplementedError()

    expr = nixlang.let(
        **nixpkgs_args,
        pkgs=nixlang.call("import", nixlang.raw("nixpkgs"), nixlang.attrs(
            system=_nix.current_system(),
        )),
        in_=nixlang.call("pkgs.mkShell", nixlang.attrs(
            packages=_pkgs_list(kwargs.get("packages", [])),
            inputsFrom=_pkgs_list(kwargs.get("inputs_from", [])),
            buildInputs=_pkgs_list(kwargs.get("build_inputs", [])),
            shellHook=f"""
export LD_LIBRARY_PATH=${{pkgs.lib.makeLibraryPath ({nixlang.dumps(_pkgs_list(kwargs.get('library_path', [])))})}}:$LD_LIBRARY_PATH
""" + kwargs.get("shell_hook", "")
        ))
    )
    return nixlang.dumps(expr)


def mk_shell(**kwargs: Unpack[MkShellParams]) -> NixSubprocess:
    shell_expr = mk_shell_expr(**kwargs)
    return NixSubprocess.build(expr=shell_expr)
