# Advanced Usage

## Pure evaluation

`py-nix-shell` encourages [*pure Nix
evaluation*](https://nix.dev/manual/nix/2.24/command-ref/conf-file.html#conf-pure-eval)
-- in other words, it explicitly declares the versions of inputs used
up-front and disables impure evaluation capabilities like accessing
environment variables or random files on your filesystem while writing
Nix code.

This is largely because when your evaluation is pure, it's a whole lot
easier to cache the result of Nix shells and quickly access the
results of those caches without much additional specification.

It is possible to supplement impure requirements in your Nix
files. For example, if you wanted to pass certain environment
variables to a `shell.nix`, you could do:

```python
import nix_shell
shell = nix_shell.from_nix("shell.nix", args={
  "pythonVersion": os.environ.get("PYTHON_VERSION", "python313"),
  "env": {
    "MY_FLAG": os.environ.get("MY_FLAG", "")
  }
})
```

This is then passed as an argument to your `shell.nix`:

```nix
{ pkgs, pythonVersion, env }:
pkgs.mkShell {
  packages = [ pkgs.${pythonVersion} ];
  shellHook = ''
    export MY_FLAG='${env.MY_FLAG}'
  '';
}
```

To disable this behavior, pass `impure=True`:

```python
nix = nix_shell.from_nix("/path/to/your/shell.nix", impure=True)
```

Be warned that certain caching features are not guaranteed to work in
impure mode.

## `nixpkgs` version locking

**NOTE**: This does not apply to `from_flake`, which uses only input
versions from your `flake.lock`.

In order to support pure evaluation, `py-nix-shell` directly manages
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

## File sets

Because Nix doesn't really provide a means of purely managing many Nix
files beyond version tracking like Git, `py-nix-shell` does provide a
layer to supplement this functionality:

```python
shell = nix_shell.from_fileset(
  main="shell.nix",
  files=Path.cwd().glob("**.nix")
)
```

This is useful when you might have dev shells inside a Nix package
that do not necessarily need the entire Git repository to update the
shell. This can save on load times, especially since many shells do
not necessarily depend on the full contents of a repository.

```
{ pkgs }:
let
  myPackage = pkgs.callPackage ./my-package.nix {};
in pkgs.mkShell { packages = [ myPackage ]; }
```
