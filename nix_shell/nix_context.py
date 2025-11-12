from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Generator

from nix_shell import cli, dsl
from nix_shell.flake import FlakeRefLock
from nix_shell.utils.flake import (
    FlakeLock,
    FlakeRef,
    fetch_locked_from_flake_ref,
    locked_to_url,
)

if TYPE_CHECKING:
    from nix_shell.cache import CacheOptions


@dataclass
class FlakeInputs:
    """
    Provides convenient attribute-based access to flake inputs in a NixContext.

    Usage:
        ctx.inputs.nixpkgs  # Returns NixVar for nixpkgs input
        ctx.inputs.devenv   # Returns NixVar for devenv input
    """

    name: str = "flakeImports"
    flakes: dict[str, FlakeRefLock | None] = field(default_factory=dict)
    flake_lock: FlakeLock | None = None

    def _v(self, name: str) -> dsl.NixVar:
        return dsl.NixVar(f"{self.name}.{name}")

    def items(self) -> Generator[tuple[(str, dsl.NixVar)], None, None]:
        if self.flake_lock is not None:
            for node in self.flake_lock["nodes"].names():
                yield (node, self._v(node))
        for flake_name in self.flakes:
            if (
                self.flake_lock is not None
                and flake_name not in self.flake_lock["nodes"]
            ):
                yield (flake_name, self._v(flake_name))

    def __getitem__(self, name: str) -> dsl.NixVar:
        """Get a flake input by name, creating it if it doesn't exist."""
        if (
            self.flake_lock is not None
            and name in self.flake_lock["nodes"]
            or name in self.flakes
        ):
            return self._v(name)
        else:
            self.flakes[name] = None
            return self._v(name)

    def __setitem__(self, name: str, ref: FlakeRefLock) -> None:
        self.flakes[name] = ref

    def expr(self) -> dsl.NixExpr:
        """
        Generate a Nix expression that imports all flake inputs.

        Returns an attribute set where each key is a flake input name
        and the value is the imported flake.
        """
        flake_imports: dict[str, dsl.NixExpr] = {}

        # Process flake.lock nodes if available
        if self.flake_lock is not None:
            for node_name, node in self.flake_lock["nodes"].items():
                # Skip the root node
                if node_name == self.flake_lock.get("root", "root"):
                    continue

                # Check if we have locked data for this node
                if "locked" in node:
                    locked_ref = node["locked"]
                    # Convert locked reference to flake URL
                    flake_url = locked_to_url(locked_ref)
                    # Import the flake using builtins.getFlake
                    flake_imports[node_name] = dsl.builtins["getFlake"](flake_url)

        # Process manually added flakes
        for flake_name, flake_ref_lock in self.flakes.items():
            # Skip if already processed from flake.lock
            if flake_name in flake_imports:
                continue

            if flake_ref_lock is not None:
                # Convert locked reference to flake URL
                flake_url = locked_to_url(flake_ref_lock)
                # Import the flake using builtins.getFlake
                flake_imports[flake_name] = dsl.builtins["getFlake"](flake_url)
            else:
                raise ValueError(
                    f"flake input {flake_name} referenced without any existing entry."
                )

        # Return as an attribute set
        return flake_imports


def _mk_var_name_from_path(path: Path) -> str:
    """Generate a deterministic variable name from a hashable expression."""
    import hashlib

    # Use deterministic hash instead of Python's randomized hash()
    content = str(path.absolute()).encode("utf-8")
    hash_obj = hashlib.md5(content, usedforsecurity=False)
    hex_string = hash_obj.hexdigest()[:16]  # Use first 16 chars for shorter names
    return "var_" + hex_string


@dataclass
class NixContext:
    """
    Helper for building a Nix expression from a Nix context.

    Sometimes we have common variables (flake inputs, `nixpkgs`, files, etc)
    that need to be shared between a bunch of expressions. Rather than
    manually managing these, you can instead use a context to manage
    these shared variables.
    """

    _params: dict[str, dsl.NixExpr | None] = field(default_factory=dict)
    _vars: dict[str, dsl.NixExpr] = field(default_factory=dict)
    _files: dict[Path, dsl.NixVar] = field(default_factory=dict)
    flake_inputs: FlakeInputs = field(default_factory=lambda: FlakeInputs())

    # Cache configuration
    disable_cache: bool = False
    cache_options: CacheOptions | None = None

    def __post_init__(self) -> None:
        """Initialize default variables including pkgs from py-nix-shell's locked nixpkgs."""
        from nix_shell.utils.flake import get_locked_from_py_nix_shell

        # Initialize pkgs from py-nix-shell's locked nixpkgs
        self.flake_inputs["nixpkgs"] = get_locked_from_py_nix_shell("nixpkgs")
        self.flake_inputs["flake-compat"] = get_locked_from_py_nix_shell("flake-compat")

        self["system"] = cli.current_system()
        self["pkgs"] = self.flake_inputs["nixpkgs"]["legacyPackages"][self["system"]]
        self["lib"] = self["pkgs"]["lib"]

    def __getitem__(self, key: str) -> dsl.NixVar:
        """Get a variable by name from the context."""
        if key in self._vars:
            return dsl.NixVar(key)
        else:
            raise KeyError(f"variable '{key}' does not exist")

    def __setitem__(self, name: str, value: dsl.NixExpr) -> None:
        """Set a variable in the context."""
        self._vars[name] = value

    def set_default(self, name: str, value: dsl.NixExpr) -> None:
        """Set a variable only if it doesn't already exist."""
        if name not in self._vars:
            self[name] = value

    def flake(self, ref: FlakeRef, name: str = "flakeSrc") -> dsl.NixVar:
        """Add a flake reference to the context and return its variable."""
        locked = fetch_locked_from_flake_ref(ref)
        # Convert FlakeRefLock to a proper flake URL string
        flake_url = locked_to_url(locked)
        self[name] = dsl.builtins["getFlake"](flake_url)
        return self[name]

    def path(self, path: Path) -> dsl.NixVar:
        """Add a file path to the context and return its variable."""
        if path in self._files:
            return self._files[path]
        var_name = _mk_var_name_from_path(path)
        self._params[var_name] = None
        self._files[path] = dsl.NixVar(var_name)
        return self._files[path]

    def wrap(self, expr: dsl.NixExpr) -> dsl.NixExpr:
        """Wrap an expression in a function with context variables and parameters."""
        self["flakeInputs"] = self.flake_inputs.expr()
        return dsl.func(
            params=[dsl.param(name, default) for name, default in self._params.items()],
            expr=dsl.let(**{var: expr for var, expr in self._vars.items()}, in_=expr),
        )

    def has_var(self, name: str) -> bool:
        return name in self._vars

    @property
    def inputs(self) -> FlakeInputs:
        """Get the flake inputs helper for convenient attribute access."""
        return self._inputs_helper

    @property
    def build_args(self) -> cli.NixBuildArgs:
        """Generate CLI build arguments for files tracked in this context."""
        args: cli.NixBuildArgs = {}

        if self._files:
            # Use --arg-from-file to pass file paths
            args["arg_from_file"] = {
                var.value: path for path, var in self._files.items()
            }

        return args


_global_context: ContextVar[NixContext] = ContextVar("nix_global_context")


def get_nix_context() -> NixContext:
    """Get the current global Nix context, creating one if it doesn't exist."""
    try:
        context = _global_context.get()
    except LookupError:
        context = None

    if context is None:
        context = NixContext()
        _global_context.set(context)
    return context


@contextmanager
def context(ctx: NixContext | None = None) -> Generator[NixContext, None, None]:
    """Context manager for temporarily setting the global Nix context."""
    if ctx is None:
        ctx = NixContext()

    token = _global_context.set(ctx)
    try:
        yield ctx
    finally:
        _global_context.reset(token)
