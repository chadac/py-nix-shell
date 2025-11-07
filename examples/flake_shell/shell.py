import nix_shell
from nix_shell import flake_nix

with nix_shell.context_with_defaults() as ctx:
    if not (shell := ctx.load_shell()):
        shell = flake_nix.devshell("dev")
