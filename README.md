# py-nix-shell

Invoke commands sourced from Nix. This is mainly intended for those
who vend cli tools inside environments that often support Nix and need
to be able to reproducibly invoke those tools.

If folks don't have Nix, it will attempt to run the command anyways,
and then provide an information install-error style message (either
packages to install or a suggestion to install Nix).

This is a drop-in replacement for `subprocess` -- so you can
substitute your calls from `subprocess.<method>` to
`nix_shell.<method>`.

If Nix is not installed, this (by default) falls back to a non-Nix shell.

## Installation

```bash
pip install nix-shell
```

## Usage

```python
import nix_shell

# nix_shell supports existing subprocess commands

# if the command name matches the nixpkgs name, use that
# see https://search.nixos.org/packages for a list of packages
nix_shell.run(["curl", "https://google.com"])

# you can also specify the nix packages to install
nix_shell.run(["curl", "https://google.com"], packages=["curlMinimal"])

# you can also use a dev environment from a flake
nix_shell.run(["curl", "https://google.com"], flake="github:chadac/py-nix-shell#sample-curl-env")

# this supports
```

It is also possible to specify a common environment to run commands under:

```python
import nix_shell

nix = nix_shell.from_flake("/path/to/my/flake.nix")

nix.run(["curl", "https://google.com"])
```

```python
nix_shell.mk_shell(packages=["git"])
```
