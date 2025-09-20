# Builders

While `nix_shell` can act as a very minimal layer on top of a generic
`shell.nix`, we offer a variety of *builders* that generate Nix
derivations for you.

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

This enables you to avoid using Nix language in your development setup
-- useful if you're vending Nix as a utility for Python developers,
for example.

## from_nix

Provisions a Nix shell from a `shell.nix` file.

```
from nix_shell import from_nix

shell = from_nix(nix_file="/path/to/your/shell.nix")

# This runs inside the given Nix shell
shell.run(["curl", "https://google.com"])
```

## from_flake

Provisions a Nix shell from a Flake output.

```
from nix_shell import from_flake

# if you don't specify the particular output we will assume it is devShells.default
shell = from_flake(flake="path:/to/your/flake.nix")

# but you can specify alternatives
shell = from_flake(flake="path:/to/your/flake.nix#devShells.alternate")
```
