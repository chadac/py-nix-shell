from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Generator

from nix_shell import cli, dsl
from nix_shell.flake import FlakeRef, FlakeRefLock, fetch_locked_from_flake_ref

if TYPE_CHECKING:
    from nix_shell.cache import CacheOptions


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

    # Cache configuration
    disable_cache: bool = False
    cache_options: CacheOptions | None = None

    def __post_init__(self) -> None:
        """Initialize default variables including pkgs from py-nix-shell's locked nixpkgs."""
        from nix_shell.flake import get_locked_from_py_nix_shell

        # Initialize pkgs from py-nix-shell's locked nixpkgs
        nixpkgs_locked = get_locked_from_py_nix_shell("nixpkgs")
        # Convert FlakeRefLock to a proper flake URL string
        flake_url = self._locked_to_url(nixpkgs_locked)
        self["nixpkgs"] = dsl.builtins["getFlake"](flake_url)
        self["pkgs"] = self["nixpkgs"]["legacyPackages"][cli.current_system()]

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
        flake_url = self._locked_to_url(locked)
        self[name] = dsl.builtins["getFlake"](flake_url)
        return self[name]

    def _locked_to_url(self, locked: FlakeRefLock) -> str:
        """Convert a FlakeRefLock to a flake URL string."""
        if locked["type"] == "github":
            return f"github:{locked['owner']}/{locked['repo']}/{locked['rev']}"
        elif locked["type"] == "git":
            return f"git+{locked['url']}?rev={locked['rev']}"
        elif locked["type"] == "path":
            return f"path:{locked['path']}"
        else:
            # Fallback for other types
            return str(locked)

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
        return dsl.func(
            params=[dsl.param(name, default) for name, default in self._params.items()],
            expr=dsl.let(**{var: expr for var, expr in self._vars.items()}, in_=expr),
        )

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
