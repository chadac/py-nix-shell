from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any, TypedDict, Unpack

from nix_shell import _nix


def gen_shell_script(**params: Unpack[_nix.NixBuildArgs]) -> str:
    _nix.build(**params)
    result = _nix.derivation.show(**params)
    derivs = json.loads(result)
    deriv = derivs[next(iter(derivs.keys()))]
    builder = deriv["builder"]
    activate_path = deriv["env"]["out"]
    return f"""#!{builder}

source {activate_path}

eval "$@"
"""


@dataclass
class NixSubprocess:
    shell_path: Path

    @classmethod
    def build(cls, **params: Unpack[_nix.NixBuildArgs]):
        shell_script = gen_shell_script(**params)
        shell_path = tempfile.NamedTemporaryFile(delete=False)
        shell_path.write(shell_script.encode())
        shell_path.close()
        os.chmod(shell_path.name, 0o700)
        return cls(Path(shell_path.name))

    def _process_args(self, cmd: list[str] | str, **kwargs) -> Any:
        new_kwargs = {
            **kwargs,
            **{
                "env": kwargs.get("env", {}),
            },
        }
        new_cmd = None
        if isinstance(cmd, list):
            new_cmd = [self.shell_path] + cmd
        else:
            new_cmd = f"{self.shell_path} {cmd}"
        return ([new_cmd], new_kwargs)

    def run(self, cmd: list[str] | str, **kwargs) -> subprocess.CompletedProcess:
        new_args, new_kwargs = self._process_args(cmd, **kwargs)
        return subprocess.run(*new_args, **new_kwargs)

    def check_output(self, cmd: list[str] | str, **kwargs) -> bytes:
        new_args, new_kwargs = self._process_args(cmd, **kwargs)
        return subprocess.check_output(*new_args, **new_kwargs)

    def Popen(self, cmd: list[str] | str, **kwargs) -> subprocess.Popen[str]:
        new_args, new_kwargs = self._process_args(cmd, **kwargs)
        return subprocess.Popen(*new_args, **new_kwargs)
