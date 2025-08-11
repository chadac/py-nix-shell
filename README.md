# py-nix-shell

[![ci](https://github.com/chadac/py-nix-shell/actions/workflows/pr.yaml/badge.svg)](https://github.com/chadac/py-nix-shell/actions/workflows/pr.yaml)
[![pypi](https://img.shields.io/pypi/v/nix-shell.svg)](https://pypi.org/project/nix-shell/)

Power tool for provisioning Nix shells for Python. This makes Nix
accessible and easy-to-use for Python devs while enabling Nix power
users to leverage advanced caching capabilities with pure eval.

## Uses

* [**As a Nix shell
  builder**](https://chadac.github.io/py-nix-shell/usage/shell.py):
  Write `shell.py` files to leverage the advantages of pure Nix shells
  without losing impure features, such as customizing with environment
  variables or using other forms of logic to maintain a Nix shell
* [**As a Python library**](https://chadac.github.io/py-nix-shell/usage/subprocess): Provides a `subprocess`-like interface to
  run regular CLI commands inside a nix shell; migrating existing
  tooling is as simple as replacing `subprocess.run` with
  `nix_shell.run`.
* [**As a shell wrapper**](https://chadac.github.io/py-nix-shell/usage/activate): You can immediately set up any
  pip-distributed CLI utilities to run inside a nix shell using
  `shell.activate()`.

## Installation

```bash
pip install nix-shell
```

## Getting Started

See the [docs](https://chadac.github.io/py-nix-shell/#) for more
details. Some example uses:

### Development environments

Similar to Nix's `shell.nix`, you can build Nix shells inside a
`shell.py` instead. For example:

```python
import nix_shell

# the `shell.py` needs to export a `shell` variable
shell = nix_shell.mk_shell(packages=["uv", "mise", "curl"], library_path=["zlib"])

# save shell metadata to the virtual environment to make reloading nearly instant
shell.persist_venv()
```

Shells can be activated via the cli utility:

```bash
py-nix-shell activate # activate the given shell
py-nix-shell print-den-env # useful for direnv-type activations
```

You can create Nix shells using a variety of [builders](https://chadac.github.io/py-nix-shell/builders):

```python
import nix_shell

# build a shell manually
shell = nix_shell.mk_shell(packages=["curl"], library_path=["stdenv.cc.cc.lib"])

# specify a shell.nix file to use
shell = nix_shell.from_nix("path:/to/my/shell.nix")

# specify a flake to use
shell = nix_shell.from_flake("path:/to/my/flake.nix#devShells.default")
```

### Subprocess execution

`py-nix-shell` provides an interface that supports nearly all
`subprocess` commands, but enables running them inside a Nix
wrapper. Usage is as simple as:

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

# it is also possible to reuse the same shell for multiple commands
shell = nix_shell.mk_shell(packages=["curl", "openssl"])
shell.run(["curl", "https://google.com"])
shell.run(["curl", "https://yahoo.com"])
```

You can use `run`, `check_output`, `Popen`, `call`, `check_call`,
`getoutput` and `getstatusoutput`.

### CLI wrappers

The same shell builders also provide an `activate` script which will
update your current Python session to use the Nix environment,
similarly to running it as if it were spawned by `nix shell`:

```python
import subprocess
import nix_shell
shell = nix_shell.mk_shell(packages=["curl", "openssl"])

def cli():
    shell.activate()
    subprocess.run(["which", "curl"]) # will point to the Nix version
```
