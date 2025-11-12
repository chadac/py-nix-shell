"""Integration with devbox for creating development environments."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from nix_shell import dsl
from nix_shell.build import NixShell
from nix_shell.cli import current_system
from nix_shell.simple_shell import SimpleNixShell


@dataclass
class DevboxShell:
    """A devbox development shell parsed from devbox.json and devbox.lock."""

    packages: list[str] = field(default_factory=list)
    init_hook: list[str] = field(default_factory=list)
    scripts: dict[str, list[str]] = field(default_factory=dict)
    nixpkgs_ref: str | None = None
    system: str = field(default_factory=current_system)

    @classmethod
    def from_files(
        cls,
        devbox_json: Path = Path("devbox.json"),
        devbox_lock: Path = Path("devbox.lock"),
    ) -> DevboxShell:
        """Create a DevboxShell by parsing devbox.json and devbox.lock files."""

        # Parse devbox.json
        with open(devbox_json) as f:
            config = json.load(f)

        packages = config.get("packages", [])
        shell_config = config.get("shell", {})
        init_hook = shell_config.get("init_hook", [])
        scripts = shell_config.get("scripts", {})

        # Parse devbox.lock
        nixpkgs_ref = None
        if devbox_lock.exists():
            with open(devbox_lock) as f:
                lock = json.load(f)

            # Find nixpkgs reference
            for key in lock.get("packages", {}):
                if "nixpkgs" in key:
                    nixpkgs_ref = key
                    break

        return cls(
            packages=packages,
            init_hook=init_hook,
            scripts=scripts,
            nixpkgs_ref=nixpkgs_ref,
        )

    def _get_package_names(self) -> list[str]:
        """Convert devbox packages to package names for NixShellBuilder."""
        package_names = []

        for package in self.packages:
            # Parse package@version format
            if "@" in package:
                name, version = package.split("@", 1)
                # For now, just use the package name
                # TODO: Handle specific versions and store paths from devbox.lock
                package_names.append(name)
            else:
                package_names.append(package)

        return package_names

    def _get_shell_hook(self) -> str:
        """Generate shell hook from init_hook and scripts."""
        lines = []

        # Add init hooks
        lines.extend(self.init_hook)

        # Add script definitions
        for script_name, script_commands in self.scripts.items():
            # Create a function for each script
            lines.append(f"{script_name}() {{")
            for command in script_commands:
                lines.append(f"  {command}")
            lines.append("}")

        return "\\n".join(lines)

    def mk_shell(self) -> dsl.NixExpr:
        """Generate a mkShell expression for this devbox configuration."""
        simple_shell = SimpleNixShell(
            packages=self._get_package_names(),
            shell_hook=[self._get_shell_hook()],
        )
        return simple_shell.to_mk_shell()


def activate(
    devbox_json: Path = Path("devbox.json"), devbox_lock: Path = Path("devbox.lock")
) -> NixShell:
    """Create a shell from devbox configuration files."""
    devbox_shell = DevboxShell.from_files(devbox_json, devbox_lock)
    shell_expr = devbox_shell.mk_shell()
    return NixShell.from_expr_with_context(shell_expr)
