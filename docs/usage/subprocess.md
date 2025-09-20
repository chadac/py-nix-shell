# subprocess substitution

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
