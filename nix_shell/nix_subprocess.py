"""
This is the main logic for
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, Callable, Self, Unpack

from nix_shell import _nix


def gen_shell_script(**params: Unpack[_nix.NixBuildArgs]) -> str:
    """
    Generates a shell script for the given Nix shell.
    """
    # First we build it to ensure it exists
    # TODO: Probably link this to a sqlite cache potentially?
    _nix.build(no_link=True, **params)

    # Next, we evaluate the derivation to get our shell vars
    result = _nix.derivation.show(**params)
    derivs = json.loads(result)
    deriv = derivs[next(iter(derivs.keys()))]
    builder = deriv["builder"]
    # This gives us the path to the script that activates our shell environment
    activate_path = deriv["env"]["out"]
    # Now we'll return a script that simply activates everything and then runs
    # whatever it is provided
    return f"""#!{builder}

source {activate_path}

eval "$@"
"""


@dataclass
class NixSubprocess:
    """
    Runs `subprocess` commands inside the given `nix` shell.

    Args:
        shell_path (Path): Path to the file that is used to activate this shell.
    """

    shell_path: Path

    @classmethod
    @cache
    def build(cls, **params: Unpack[_nix.NixBuildArgs]) -> Self:
        """Build a new Nix subprocess env from `nix build` parameters."""
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
        new_cmd: str | list[str]
        if isinstance(cmd, list):
            new_cmd = [str(self.shell_path)] + cmd
        else:
            new_cmd = f"{self.shell_path} {cmd}"
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
