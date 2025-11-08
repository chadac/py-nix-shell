"""Integration with devenv for creating development environments."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from nix_shell import dsl
from nix_shell.cli import current_system
from nix_shell.dsl_utils import (
    NixContext,
    get_nix_context,
    import_flake,
    import_nixpkgs,
)
from nix_shell.flake import FlakeRefLock, get_locked_from_py_nix_shell
from nix_shell.module import Module, ModuleExpr, ModuleSystem, ModuleType


@dataclass
class DevenvShell:
    """A devenv development shell with configurable modules and flake locks."""

    nixpkgs_lock: FlakeRefLock = field(
        default_factory=lambda: get_locked_from_py_nix_shell("nixpkgs")
    )
    devenv_lock: FlakeRefLock = field(
        default_factory=lambda: get_locked_from_py_nix_shell("devenv")
    )
    git_hooks_lock: FlakeRefLock = field(
        default_factory=lambda: get_locked_from_py_nix_shell("git-hooks")
    )
    modules: list[ModuleType] = field(default_factory=lambda: [])
    system: str = field(default_factory=current_system)

    def __add__(self, other: Module) -> DevenvShell:
        """Add a module to this devenv shell."""
        return DevenvShell(
            nixpkgs_lock=self.nixpkgs_lock,
            devenv_lock=self.devenv_lock,
            git_hooks_lock=self.git_hooks_lock,
            modules=self.modules + [other],
            system=self.system,
        )

    def __radd__(self, other: Module) -> DevenvShell:
        """Add a module to this devenv shell (reverse operation)."""
        return self + other

    def _default_modules(self) -> list[ModuleType]:
        """Get the default devenv modules for this shell."""
        return [
            ModuleExpr("${devenv}/src/modules/top-level.nix"),
            Module(
                config=dsl.let(
                    nixpkgs=import_flake(self.nixpkgs_lock),
                    devenv_lock=import_flake(self.devenv_lock),
                    git_hooks=import_flake(self.git_hooks_lock),
                    in_={
                        "_module.args": {
                            "pkgs": dsl.v("pkgs"),
                            "lib": dsl.v("pkgs")["lib"],
                            "inputs": {
                                "nixpkgs": dsl.v("nixpkgs"),
                                "devenv": dsl.v("devenv"),
                                "git-hooks": dsl.v("git_hooks"),
                            },
                            "self": str(Path.cwd()),
                        },
                        "devenv": {
                            "root": str(Path.cwd()),
                            "warnOnNewVersion": False,
                            "flakesIntegration": False,
                            "cliVersion": "1.10",  # TODO: Calculate this value
                        },
                    },
                )
            ),
        ]

    def mk_expr(self, ctx: NixContext = get_nix_context()) -> dsl.NixExpr:
        """Generate the Nix expression for this devenv shell."""
        module_system = ModuleSystem(modules=self._default_modules() + self.modules)
        ctx.set_default("pkgs", import_nixpkgs(self.nixpkgs_lock, system=self.system))
        ctx.set_default("lib", ctx["pkgs"]["lib"])
        return dsl.let(
            pkgs=import_nixpkgs(self.nixpkgs_lock, system=self.system),
            devenv=import_flake(self.devenv_lock),
            shell=module_system.expr,
            in_=dsl.v("shell")["config"]["shell"],
        )


def _default_devenv_modules(ctx: NixContext | None = None) -> list[ModuleType]:
    """Get default devenv modules with the given context."""
    ctx = ctx or get_nix_context()

    return [
        ModuleExpr("${devenv}/src/modules/top-level.nix"),
        Module(
            config={
                "_module.args": {
                    "pkgs": ctx["pkgs"],
                    "lib": ctx["pkgs"]["lib"],
                    "inputs": ctx["flakeInputs"],
                    "self": str(Path.cwd()),
                },
                "devenv": {
                    "root": str(Path.cwd()),
                    "warnOnNewVersion": False,
                    "flakesIntegration": False,
                    "cliVersion": "1.10",  # TODO: Calculate this value
                },
            },
        ),
    ]


def init(
    attrs: dict[str, Any] | None = None,
    module_path: Path = Path("devenv.nix"),
    load_devenv_nix: bool = True,
    ctx: NixContext | None = None,
) -> DevenvShell:
    """Initialize a devenv shell with optional configuration and modules."""
    modules: list[ModuleType] = []

    # load a custom set of attrs
    if attrs is not None:
        modules.append(Module(params=[dsl.v("pkgs")], config=attrs))

    # load a `devenv.nix`
    if load_devenv_nix and module_path.exists():
        devenv_nix = dsl.StorePath.from_path(module_path)
        modules.append(ModuleExpr(devenv_nix))

    return DevenvShell(modules=modules)


def uv_workspace(
    python_version: Literal[
        "3.11", "3.12", "3.13", "3.14", "latest", "default"
    ] = "default",
    uv_version: str = "latest",
):
    """Create a Python workspace with uv package manager enabled."""
    python_pkg = "python3"
    match python_version:
        case "3.11":
            python_pkg = "python311"
        case "3.12":
            python_pkg = "python312"
        case "3.13" | "latest":
            python_pkg = "python313"
        case "3.14":
            python_pkg = "python314"

    # TODO: Custom uv version
    return init(
        {
            "languages.python": {
                "enable": True,
                "version": dsl.pkgs[python_pkg],
                "uv.enable": True,
            }
        }
    )
