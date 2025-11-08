from __future__ import annotations

import hashlib
import json
import logging
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Self, TypeVar, Unpack

if TYPE_CHECKING:
    from nix_shell.cache import CacheHistoryEntry

import nix_shell.cache
from nix_shell import cli, dsl
from nix_shell.constants import LOCAL_CACHE_ROOT
from nix_shell.flake import FlakeRef, FlakeRefLock, fetch_locked_from_flake_ref
from nix_shell.nix_context import NixContext, get_nix_context

T = TypeVar("T", bound="NixBuild")


logger = logging.getLogger("pynix")


@dataclass
class NixBuild:
    """
    Wrapper for `nix build` commands with some convenient utilities.

    Args:
        params (cli.NixBuildArgs): Parameters to the `nix build` command
    """

    params: cli.NixBuildArgs

    """List of store paths associated with the build."""
    _store_paths: list[str] | None = None

    """Keys used for caching Nix build results."""
    _venv_keys: set[str] = field(
        default_factory=lambda: {"build_id", "derivation", "dev_env"}
    )

    @classmethod
    def create(cls: type[T], **params: Unpack[cli.NixBuildArgs]) -> T:
        """Create a new NixBuild instance."""
        return cls(params)

    @classmethod
    def from_expr(cls: type[T], expr: dsl.NixExpr) -> T:
        """Create a NixBuild from a Nix expression."""
        return cls.create(expr=dsl.dumps(expr))

    @classmethod
    def from_expr_with_context(
        cls: type[T], expr: dsl.NixExpr, ctx: NixContext | None = None
    ) -> T:
        """Create a NixBuild from a Nix expression wrapped in a context."""
        ctx = ctx or get_nix_context()

        build = cls.create(
            expr=dsl.dumps(ctx.wrap(expr)),
            **ctx.build_args,
        )

        # Apply caching if enabled in context
        if ctx.cache_options is not None:
            logger.debug("loading shell from cache")
            build = nix_shell.cache.load(
                build,
                use_global_cache=ctx.cache_options["use_global"],
                history=ctx.cache_options["history"],
            )

        return build

    @classmethod
    def from_flake(
        cls: type[T],
        ref: FlakeRef | None = None,
        locked: FlakeRefLock | None = None,
        output: str = "default",
    ) -> T:
        """Create a NixBuild from a flake reference."""
        assert ref is not None or locked is not None, (
            "either a flake reference or lock must be passed"
        )
        if locked is None:
            assert ref is not None
            locked = fetch_locked_from_flake_ref(ref)
        return cls.create(
            expr=dsl.dumps(
                dsl.let(
                    flake=dsl.builtins["getFlake"](locked), in_=dsl.v("flake")[output]
                )
            )
        )

    @classmethod
    def from_cache(cls: type[T], entry: CacheHistoryEntry) -> T:
        """Create a phantom NixBuild from a cache entry."""
        from pathlib import Path

        # Create minimal NixBuild with empty params
        instance = cls({})

        # Load the cached data from the JSON file
        json_path = Path(entry["json_path"])
        if json_path.exists():
            instance.load(json_path)

        return instance

    def _get_build_id(self) -> str:
        """
        Identifier for the build.

        Useful for distinguishing pure builds, especially when building caches
        or determining when to reset a cache.
        """
        h = hashlib.md5(usedforsecurity=False)
        if any(
            self.params.get(impure_key) for impure_key in ["impure", "include", "file"]
        ):
            logging.warning(
                "ID generated from impure context; not guaranteed to be unique"
            )

        h.update(b"impure" if self.params.get("impure") else b"pure")
        if filename := self.params.get("file"):
            with open(filename, "rb") as f:
                while True:
                    data = f.read(256)
                    if not data:
                        break
                    h.update(data)
        for name, path in sorted(self.params.get("include", [])):
            h.update(name.encode())
            with open(path, "rb") as f:
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    h.update(data)
        h.update(self.params.get("installable", "no-installable").encode())
        h.update(self.params.get("ref", "no-ref").encode())
        h.update(self.params.get("expr", "no-expr").encode())
        return h.hexdigest()

    @cached_property
    def build_id(self) -> str:
        return self._get_build_id()

    def build(self) -> None:
        """Alias for `nix build`."""
        out_paths = cli.build(no_link=True, print_out_paths=True, **self.params)
        self._store_paths = out_paths.strip().split("\n")

    def store_paths(self) -> list[str]:
        """Returns the set of store paths that are generated by `nix build`."""
        if self._store_paths is None:
            self.build()
            assert self._store_paths is not None
        return self._store_paths

    @cached_property
    def derivation(self) -> dict[str, Any]:
        """The JSON-ified output of `nix derivation show`."""
        derivs = json.loads(cli.derivation.show(**self.params))
        return derivs[next(iter(derivs.keys()))]

    @cached_property
    def dev_env(self) -> str:
        """The bash instructions from `nix print-dev-env`."""
        return cli.print_dev_env(**self.params)

    @property
    def builder(self) -> str:
        """The builder associated with the derivation."""
        return self.derivation["builder"]

    def save_json(self, dest: Path) -> None:
        """Save the metadata from a Nix build (ID, derivation, dev env) to a JSON file."""
        data = {}
        for key in self._venv_keys:
            data[key] = getattr(self, key)
        with dest.open("w") as f:
            json.dump(data, f)

    def save_link(self, dest: Path) -> None:
        """Create a symlink to the derivation at the given location."""
        cli.build(out_link=dest, **self.params)

    def load(self, json_path: Path) -> None:
        """Load cached build data from a JSON file into this instance."""
        logger.debug(f"loading cached build results from {json_path}")
        with json_path.open("r") as f:
            data = json.load(f)

        # Populate the build object with cached data
        for key, value in data.items():
            if key in self._venv_keys:
                self.__dict__[key] = value


LIST_LIKE_VARS = {
    "PATH",
    "LD_LIBRARY_PATH",
    "PYTHONPATH",
    "CLASSPATH",
    "PKG_CONFIG_PATH",
    "MANPATH",
    "INFOPATH",
    "XDG_DATA_DIRS",
    "XDG_CONFIG_DIRS",
    "CDPATH",
    "FPATH",
    "MAILPATH",
}


@dataclass
class NixShell(NixBuild):
    """
    Nix derivations that are made via `mkShell`.
    """

    def __post_init__(self):
        """Initialize NixShell with additional cache keys."""
        self._venv_keys.add("env")

    @property
    def script_path(self) -> str:
        """Path to script that activates this shell."""
        return self.derivation["env"]["out"]

    def _load(self, data: dict[str, Any]) -> None:
        """Load cached build data into this instance."""
        # populate cache
        for key, value in data.items():
            self.__dict__[key] = value

    def _save(self, json_root: Path, profile_root: Path) -> None:
        """Save build data to cache files."""
        LOCAL_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
        # first evaluate everything
        for key in self._venv_keys:
            getattr(self, key)
        # now save it
        self.save_json(json_root)
        self.save_link(profile_root)

    def persist_venv(self, name: str = "default") -> Self:
        """
        Save the Nix shell to a cache location in the virtual env.

        Useful when you may invoke this multiple times. The executor
        will used the cached results from previous Nix commands, which
        saves a lot of time on recomputations.
        """
        LOCAL_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
        json_root = LOCAL_CACHE_ROOT / f"{name}.json"
        profile_root = LOCAL_CACHE_ROOT / f"{name}-profile"
        if json_root.exists():
            with json_root.open("r") as f:
                data = json.load(f)

            if data.get("build_id") == self.build_id:
                self._load(data)
                return self

        # otherwise, update the environment
        self._save(json_root, profile_root)
        return self

    @cached_property
    def env(self) -> dict[str, str]:
        """The list of environment variables available in the shell."""
        env_str = self.check_output(
            [
                sys.executable,
                "-c",
                "import json, os; print(json.dumps(dict(os.environ)))",
            ],
        )
        return json.loads(env_str.strip())

    def activate(self) -> None:
        """Activates a Nix shell inside the given Python session."""
        for key, value in self.env.items():
            if key in LIST_LIKE_VARS and key in os.environ:
                os.environ[key] = value + ":" + os.environ[key]
            else:
                os.environ[key] = value

    def _process_args(
        self, cmd: list[str] | str, impure_env: bool = False, **kwargs
    ) -> Any:
        """
        Transforms arguments to `subprocess.Popen` (and associated) to use Nix.

        It works by prepending the output of `nix print-dev-env` to each
        shell invocation.
        """
        default_env = dict(os.environ) if impure_env else {}
        new_kwargs = {
            **kwargs,
            **{
                "env": kwargs.get("env", default_env),
            },
        }
        script = self.dev_env + "\n"
        if isinstance(cmd, list):
            script += shlex.join(cmd)
        else:
            script += cmd
        new_cmd = [self.builder, "-c", script]
        # TODO: Better subprocess error handling
        return ([new_cmd], new_kwargs)

    def _exec(self, f: Callable[..., Any], cmd: list[str] | str, **kwargs) -> Any:
        """Executes a (subprocess) function by transforming the given args."""
        new_args, new_kwargs = self._process_args(cmd, **kwargs)
        return f(*new_args, **new_kwargs)

    def run(
        self, *args, **kwargs
    ) -> subprocess.CompletedProcess[bytes] | subprocess.CompletedProcess[str]:
        """See [subprocess.run](https://docs.python.org/3/library/subprocess.html#subprocess.run)"""
        return self._exec(subprocess.run, *args, **kwargs)

    def check_output(self, *args, **kwargs) -> bytes | str:
        """See [subprocess.check_output](https://docs.python.org/3/library/subprocess.html#subprocess.check_output)"""
        return self._exec(subprocess.check_output, *args, **kwargs)

    def Popen(self, *args, **kwargs) -> subprocess.Popen[str] | subprocess.Popen[bytes]:
        """See [subprocess.Popen](https://docs.python.org/3/library/subprocess.html#subprocess.Popen)"""
        return self._exec(subprocess.Popen, *args, **kwargs)

    def call(self, *args, **kwargs) -> int:
        """See [subprocess.call](https://docs.python.org/3/library/subprocess.html#subprocess.call)"""
        return self._exec(subprocess.call, *args, **kwargs)

    def check_call(self, *args, **kwargs) -> int:
        """See [subprocess.check_call](https://docs.python.org/3/library/subprocess.html#subprocess.check_call)"""
        return self._exec(subprocess.check_call, *args, **kwargs)

    def getoutput(self, *args, **kwargs) -> str:
        """See [subprocess.getoutput](https://docs.python.org/3/library/subprocess.html#subprocess.getoutput)"""
        return self._exec(subprocess.getoutput, *args, **kwargs)

    def getstatusoutput(self, *args, **kwargs) -> tuple[int, str]:
        """See [subprocess.getstatusoutput](https://docs.python.org/3/library/subprocess.html#subprocess.getstatusoutput)"""
        return self._exec(subprocess.getstatusoutput, *args, **kwargs)

    def spawn(self) -> None:
        """Spawn a new interactive shell with this Nix environment activated."""
        from nix_shell import cli

        # Use nix develop for mkShell derivations, nix shell for packages
        try:
            # For mkShell-based environments, use nix develop
            if hasattr(cli, "develop"):
                cli.develop(**self.params)
            else:
                # Fallback to shell if develop doesn't exist
                cli.shell(**self.params)
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\nExiting nix shell...")
        except Exception as e:
            print(f"Error starting nix shell: {e}", file=sys.stderr)
