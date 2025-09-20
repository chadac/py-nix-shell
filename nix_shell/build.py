import hashlib
import json
import logging
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Any, Callable, Self, TypeVar, Unpack

from nix_shell import _nix
from nix_shell.constants import LOCAL_CACHE_ROOT

T = TypeVar("T", bound="NixBuild")


@dataclass
class NixBuild:
    """
    Wrapper for `nix build` commands with some convenient utilities.
    """

    params: _nix.NixBuildArgs
    _store_paths: list[str] | None = None
    _venv_keys: set[str] = field(
        default_factory=lambda: {"build_id", "derivation", "dev_env"}
    )

    @classmethod
    @lru_cache
    def create(cls: type[T], **params: Unpack[_nix.NixBuildArgs]) -> T:
        return cls(params)

    @cached_property
    def build_id(self) -> str:
        """
        Identifier for the build.

        Useful for distinguishing pure builds.
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

    def build(self) -> None:
        out_paths = _nix.build(no_link=True, print_out_paths=True, **self.params)
        self._store_paths = out_paths.strip().split("\n")

    def store_paths(self) -> list[str]:
        if self._store_paths is None:
            self.build()
            assert self._store_paths is not None
        return self._store_paths

    @cached_property
    def derivation(self) -> dict[str, Any]:
        derivs = json.loads(_nix.derivation.show(**self.params))
        return derivs[next(iter(derivs.keys()))]

    @cached_property
    def dev_env(self) -> str:
        return _nix.print_dev_env(**self.params)

    @property
    def builder(self) -> str:
        return self.derivation["builder"]

    def save_json(self, dest: Path) -> None:
        data = {}
        for key in self._venv_keys:
            if key in self.__dict__:
                data[key] = self.__dict__[key]
        with dest.open("w") as f:
            json.dump(data, f)

    def save_link(self, dest: Path) -> None:
        """Creates a symlink to the derivation at the given location."""
        _nix.build(out_link=dest, **self.params)


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
        self._venv_keys.add("env")

    @property
    def script_path(self) -> str:
        """Path to script that activates shell."""
        return self.derivation["env"]["out"]

    def _load(self, data: dict[str, Any]) -> None:
        # populate cache
        for key, value in data.items():
            self.__dict__[key] = value

    def _save(self, json_root: Path, profile_root: Path) -> None:
        LOCAL_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
        # first evaluate everything
        for key in self._venv_keys:
            getattr(self, key)
        # now save it
        self.save_json(json_root)
        self.save_link(profile_root)

    def persist_venv(self, name: str = "default") -> Self:
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
        env_str = self.check_output(
            [
                sys.executable,
                "-c",
                "import json, os; print(json.dumps(dict(os.environ)))",
            ],
        )
        return json.loads(env_str.strip())

    def activate(self) -> None:
        """
        Activates a Nix shell inside the given Python session.
        """
        for key, value in self.env.items():
            if key in LIST_LIKE_VARS and key in os.environ:
                os.environ[key] = value + ":" + os.environ[key]
            else:
                os.environ[key] = value

    def _process_args(self, cmd: list[str] | str, **kwargs) -> Any:
        new_kwargs = {
            **kwargs,
            **{
                "env": kwargs.get("env", {}),
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
