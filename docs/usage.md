# General usage

`py-nix-shell` provisions Nix shells in one of three ways: via a
`shell.nix`, a Nix flake, or programatically via Python.

The most basic invocation is via `nix_shell.run`:

```python
nix_shell.run(["uv", "run", "--", "pytest"])
```

This automatically installs `uv` from `nixpkgs` and uses that to
invoke `pytest`.

You may also manually specify packages to include:

```python
nix_shell.check_output(["make", "test"], packages=["uv", "gnumake", "python312"])
```

If you already have a `shell.nix` or `flake.nix`, it's possible to
activate these environments as well:

```python
nix_shell.call(["curl", "http://localhost:8080"], nix_file=Path("/to/your/shell.nix"))

nix_shell.Popen(["curl", "http://localhost:8080"], flake=Path("/to/your/flake/project"))
nix_shell.Popen(["curl", "http://localhost:8080"], flake="github:your/flake-project")
```

If you need to invoke multiple commands in sequence, you can also
generate a reusable shell in three ways:

## from_nix

Provisions a Nix shell from a `shell.nix` file.

```
from nix_shell import from_nix

nix = from_nix(nix_file="/path/to/your/shell.nix")

# This runs inside the given Nix shell
nix.run(["curl", "https://google.com"])
```

## from_flake

Provisions a Nix shell from a Flake output.

```
from nix_shell import from_flake

# if you don't specify the particular output we will assume it is devShells.default
nix = from_flake(flake="path:/to/your/flake.nix")

# but you can specify alternatives
nix = from_flake(flake="path:/to/your/flake.nix#devShells.alternate")
```

## mk_shell

Provisions a Nix shell programatically via Python. For example,
something like

```python
nix = nix_shell.mk_shell(
    packages=["curl", "openssl"],
    library_path=["stdenv.cc.cc.lib"],
    shell_hook="echo 'Hello world!'",
)
```

would be equivalent to the following `shell.nix`:

```nix
{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = with pkgs; [ curl openssl ];
  shellHook = ''
    export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib ]}:$LD_LIBRARY_PATH
    echo 'Hello world!'
  '';
}
```

This enables you to quickly and dynamically provision shells whenever
needed.

# Advanced Usage

## Pure evaluation

By default, all Nix shell evaluations in `py-nix-shell` are pure. This
means that generally your `shell.nix` files can't access user
envirnonment variables, and you can't access other files on the
filesystem from Nix.

In order to disable this behavior, you can pass `impure=True`:

```python
nix = nix_shell.from_nix("/path/to/your/shell.nix", impure=True)
```

## `nixpkgs` version locking

This is specific only to `mk_shell` and `from_nix`. `from_flake` only
uses the `nixpkgs` version as specified in the `flake.lock file.

In order to support pure evaluation, `py-nix-shell` direclty manages
the version of `nixpkgs` you use. You can control this behavior by
passing the following:

* **default behavior**: Uses the version specified in this project's [flake.lock](https://github.com/chadac/py-nix-shell/blob/main/flake.lock). The package is updated weekly so that you can automatically keep your `nixpkgs` version up-to-date if needed.
* `use_global_nixpkgs=True`: If you'd prefer to use the version of
  `nixpkgs` the user has locally, you can specify `use_global_nixpkgs`
  command. This extracts the `nixpkgs` version from `nix flake
  metadata nixpkgs`.
* `flake_lock=Path("./to/your/flake.lock")`: You may also use a
  `flake.lock` file. This will check for a `nixpkgs` entry and use
  that version. If your `flake.lock` keeps its `nixpkgs` version under
  a different name, you can use
  `flake_lock_name="alternative_nixpkgs"` to specify.
