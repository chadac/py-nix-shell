from dataclasses import dataclass, field

from nix_shell import dsl
from nix_shell.nix_context import NixContext, get_nix_context


def _with_pkgs(packages: list[str | dsl.NixExpr]) -> list[dsl.NixExpr]:
    """Convert a list of package names/expressions to a Nix list with pkgs prefix."""
    nix_packages: list[dsl.NixExpr] = []
    for pkg in packages:
        if isinstance(pkg, str):
            nix_packages.append(dsl.call(dsl.raw(f"pkgs.{pkg}")))
        else:
            nix_packages.append(pkg)
    return nix_packages


@dataclass
class SimpleNixShell:
    packages: list[str | dsl.NixExpr] = field(default_factory=list)
    inputs_from: list[str | dsl.NixExpr] = field(default_factory=list)
    build_inputs: list[str | dsl.NixExpr] = field(default_factory=list)
    library_path: list[str | dsl.NixExpr] = field(default_factory=list)
    shell_hook: list[str] = field(default_factory=list)

    extra_args: dict[str, dsl.NixExpr] = field(default_factory=lambda: {})

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

    def to_mk_shell(self, ctx: NixContext | None = None) -> dsl.NixExpr:
        ctx = ctx or get_nix_context()

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
