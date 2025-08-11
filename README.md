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

# if the command name matches the `nixpkgs` name, install that by default
nix_shell.run(["curl", "https://google.com", "--insecure"])

# you can manually specify nix packages to install
nix_shell.run(["curl", "https://google.com"], packages=["curl", "openssl"])

# use a dev environment from a flake
nix_shell.run(["curl", "https://google.com"], flake="github:chadac/py-nix-shell#sample-curl-env")

# or, just use the `nixpkgs` version from a `flake.lock` file
nix_shell.run(["curl", "https://google.com"], packages=["curl", "openssl"], flake_lock=Path("./my/flake.lock"))
```

You can use `run`, `check_output`, `Popen`, `call`, `check_call`,
`getoutput` and `getstatusoutput`.

If you want to run a bunch of commands under the same environment, you
can use the following:

```python
import nix_shell

# build a shell manually
nix = nix_shell.mk_shell(packages=["curl"], library_path=["stdenv.cc.cc.lib"])

# specify a shell.nix file to use
nix = nix_shell.from_nix("path:/to/my/shell.nix")

# specify a flake to use
nix = nix_shell.from_flake("path:/to/my/flake.nix#devShells.default")

nix.run(["curl", "https://google.com"])
```

## Details

### Versioning

`nix-shell` tries to keep evaluation pure in order to leverage caching
capabilities when running Nix commands. As such, when running commands
via `from_nix` for `mk_shell`, the `nixpkgs` version is determined
using the `flake.lock` from this project. It is updated weekly.
