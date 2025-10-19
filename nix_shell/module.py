from __future__ import annotations

import inspect
from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from nix_shell import dsl


class ModuleType(ABC):
    def _update_source_location(self):
        # Capture source location where this module was instantiated
        self._source_location: str = "unknown"
        frame = inspect.currentframe()
        assert frame is not None
        while (frame := frame.f_back) is not None:
            module = frame.f_globals["__name__"]
            if module == "nix_shell.module":
                continue
            self._source_location = f"{module}:{frame.f_lineno}"
            break

    def __add__(self, other: Module) -> ModuleSystem:
        return ModuleSystem([self, other])

    def _get_name(self) -> str:
        cls = type(self)
        return f"{cls.__module__}.{cls.__qualname__} at {self._source_location}"

    def get_source_location(self) -> str:
        """Get the file and line number where this module was created."""
        return self._source_location or "unknown:0"

    @property
    def mod_expr(self) -> dsl.NixExpr: ...

    @property
    def expr(self) -> dsl.NixExpr:
        return ModuleSystem([self]).expr


@dataclass
class Module(ModuleType):
    params: list[dsl.Param] | None = None
    options: dsl.NixExpr | None = None
    config: dsl.NixExpr | None = None
    _file: str | None = None

    def __post_init__(self):
        self._update_source_location()

    def __add__(self, other: Module) -> ModuleSystem:
        return ModuleSystem([self, other])

    def _doc_args(self) -> list[str]:
        return []

    @property
    def file(self) -> str:
        if self._file is not None:
            return self._file
        else:
            return self._get_name()

    @property
    def mod_expr(self) -> dsl.NixExpr:
        attrs: dsl.Attrs = {"_file": self.file}
        if self.options is not None:
            attrs["options"] = self.options
        if self.config is not None:
            attrs["config"] = self.config
        if self.params is not None:
            return dsl.func(self.params + [dsl.dots], attrs)
        else:
            return attrs

    @property
    def expr(self) -> dsl.NixExpr:
        return ModuleSystem([self]).expr


@dataclass
class ModuleExpr(ModuleType):
    """
    Reference to a module as a Nix expression.
    """

    path: dsl.NixExpr

    def __post_init__(self):
        self._update_source_location()

    @property
    def mod_expr(self) -> dsl.NixExpr:
        return self.path


@dataclass
class ModuleSystem:
    modules: list[ModuleType]
    lib: dsl.NixVar = field(default_factory=lambda: dsl.NixVar("pkgs.lib"))

    def __add__(self, other: ModuleType) -> ModuleSystem:
        return ModuleSystem(self.modules + [other], self.lib)

    def __radd__(self, other: ModuleType) -> ModuleSystem:
        return ModuleSystem(self.modules + [other], self.lib)

    @property
    def expr(self) -> dsl.NixExpr:
        return dsl.call(
            self.lib["evalModules"],
            dsl.attrs(modules=[m.mod_expr for m in self.modules]),
        )
