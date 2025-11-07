import nix_shell
from nix_shell import devenv

with nix_shell.context_with_defaults() as ctx:
    shell = devenv.init()

    shell += devenv.python(version="3.11", uv=True)
    shell += devenv.rust()
