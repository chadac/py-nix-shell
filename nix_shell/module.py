"""Nix module system implementation for py-nix-shell."""

from __future__ import annotations

import inspect
from abc import ABC
from dataclasses import dataclass, field

from nix_shell import dsl


class ModuleType(ABC):
    """Base class for all module types in the Nix module system."""

    def _update_source_location(self) -> None:
        """Capture source location where this module was instantiated for debugging."""
        # Capture source location where this module was instantiated
        # Used for debugging purposes
        self._source_location: str | None = None
        frame = inspect.currentframe()
        assert frame is not None
        while (next_frame := frame.f_back) is not None:
            frame = next_frame
            module = next_frame.f_globals["__name__"]
            if module == "nix_shell.module":
                continue
            self._source_location = f"{module}:{frame.f_lineno}"
            break

    def __add__(self, other: Module) -> ModuleSystem:
        """Combine this module with another to create a module system."""
        return ModuleSystem([self, other])

    def _get_name(self) -> str:
        """Get a descriptive name for this module including its source location."""
        cls = type(self)
        return f"{cls.__module__}.{cls.__qualname__} at {self.source_location}"

    @property
    def source_location(self) -> str:
        """The file and line number where this module was created."""
        return self._source_location or "unknown:0"

    @property
    def mod_expr(self) -> dsl.NixExpr:
        """Get the Nix expression representing this module."""
        ...

    @property
    def expr(self) -> dsl.NixExpr:
        """Get the Nix expression for this module in a module system."""
        return ModuleSystem([self]).expr


@dataclass
class Module(ModuleType):
    """A Nix module with parameters, options, and configuration."""

    params: list[dsl.NixVar | dsl.ParamWithDefault] | None = None
    options: dsl.NixExpr | None = None
    config: dsl.NixExpr | None = None
    _file: str | None = None

    def __post_init__(self):
        """Initialize the module by capturing its source location."""
        self._update_source_location()

    def __add__(self, other: Module) -> ModuleSystem:
        return ModuleSystem([self, other])

    def _doc_args(self) -> list[str]:
        """Get documentation arguments for this module."""
        return []

    @property
    def file(self) -> str:
        """Get the file name or identifier for this module."""
        if self._file is not None:
            return self._file
        else:
            return self._get_name()

    @property
    def mod_expr(self) -> dsl.NixExpr:
        """Get the Nix expression representing this module."""
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
        """Initialize the module expression by capturing its source location."""
        self._update_source_location()

    @property
    def mod_expr(self) -> dsl.NixExpr:
        """Get the Nix expression representing this module."""
        return self.path


@dataclass
class ModuleSystem(dsl.NixComplexType):
    """A system of Nix modules that can be evaluated together."""

    modules: list[ModuleType]
    lib: dsl.NixVar = field(default_factory=lambda: dsl.NixVar("pkgs.lib"))

    def __add__(self, other: ModuleType) -> ModuleSystem:
        """Add another module to this module system."""
        return ModuleSystem(self.modules + [other], self.lib)

    def __radd__(self, other: ModuleType) -> ModuleSystem:
        """Add another module to this module system (reverse operation)."""
        return ModuleSystem(self.modules + [other], self.lib)

    @property
    def expr(self) -> dsl.NixExpr:
        """Get the Nix expression for evaluating this module system."""
        return dsl.call(
            self.lib["evalModules"],
            dsl.attrs(modules=[m.mod_expr for m in self.modules]),
        )
