from dataclasses import dataclass, field
from pathlib import Path

from nix_shell import dsl
from nix_shell.cli import current_system
from nix_shell.dsl_utils import import_flake, import_nixpkgs
from nix_shell.flake import FlakeRefLock, get_locked_from_py_nix_shell
from nix_shell.module import Module, ModuleExpr, ModuleSystem, ModuleType


@dataclass
class DevenvShell:
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

    def _default_modules(self) -> list[ModuleType]:
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
                            "warnOnNewVersion": False,
                            "flakesIntegration": False,
                            "cliVersion": "1.10",  # TODO: Calculate this value
                        },
                    },
                )
            ),
        ]

    @property
    def expr(self) -> dsl.NixExpr:
        module_system = ModuleSystem(modules=self._default_modules() + self.modules)
        return dsl.let(
            pkgs=import_nixpkgs(self.nixpkgs_lock, system=self.system),
            devenv=import_flake(self.devenv_lock),
            shell=module_system.expr,
            in_=dsl.v("shell")["config"]["shell"],
        )
