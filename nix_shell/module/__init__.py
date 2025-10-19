from __future__ import annotations
from nix_shell.expr import NixVar


class Module:
    def __add__(self, other: Module) -> ModuleSystem:
        return NotImplemented


@dataclass
class ModuleSystem:
    modules: list[Module]
    lib: NixVar

    def expr(self) -> NixExpr:
        return expr.
