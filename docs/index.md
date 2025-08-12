# py-nix-shell

[![ci](https://github.com/chadac/py-nix-shell/actions/workflows/pr.yaml/badge.svg)](https://github.com/chadac/py-nix-shell/actions/workflows/pr.yaml)
[![pypi](https://img.shields.io/pypi/v/nix-shell.svg)](https://pypi.org/project/nix-shell/)

Invoke commands inside Nix shells from Python using the familiar
`subprocess` interface.

## Features

* [**Easy to use**](https://chadac.github.io/py-nix-shell/usage/): Commands that use `subprocess.run` can be easily
  migrated -- simply swap `subprocess.run` with `nix_shell.run` and
  you're good to go.
* **Supports non-Nix users**: Folks without Nix can still use this,
  and get helpful error messages describing what they need to install
  or instructions for installing Nix.
* **Customizable**: You can manage your Shell environments with [flakes](https://nix.dev/concepts/flakes.html#flakes), a [shell.nix](https://nix.dev/tutorials/first-steps/declarative-shell.html), or even [through Python](https://chadac.github.io/py-nix-shell/usage#mk_shell)

## Installation

```bash
pip install nix-shell
```

## Getting Started

See the [docs](https://chadac.github.io/py-nix-shell/#) for more details, but

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
