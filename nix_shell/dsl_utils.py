from nix_shell import cli, dsl
from nix_shell.flake import FlakeRefLock


def import_flake(locked: FlakeRefLock) -> dsl.NixExpr:
    return dsl.call(dsl.builtins["fetchTree"], dsl.attrs(**locked))


def import_nixpkgs(locked: FlakeRefLock, system: str | None = None) -> dsl.NixExpr:
    nix_system = system or cli.current_system()
    return dsl.let(
        tree=dsl.call(dsl.builtins["fetchTree"], dsl.attrs(**locked)),
        nixpkgs=dsl.NixVar("tree")["outPath"],
        in_=dsl.call("import", dsl.NixVar("nixpkgs"), dsl.attrs(system=nix_system)),
    )
