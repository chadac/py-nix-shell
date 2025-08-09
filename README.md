# py-nix-shell

Invoke commands sourced from Nix. This is mainly intended for those
who vend tools inside Nix-like environments who may want to use it to
invoke other tools without necessarily

If Nix is not installed, this (by default) falls back to a non-Nix
shell.

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
