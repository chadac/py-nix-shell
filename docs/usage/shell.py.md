# shell.py

`py-nix-shell` provides an interface for quickly building new Nix
shells using Python syntax via the `pynix` CLI utility.

Usage is simple; using the same
[builders](https://chadac.github.io/py-nix-shell/builders.md)
specified above, if you export it as a global variable named `shell`
you can use it with `pynix`:

```python
import nix_shell
shell = nix_shell.mk_shell(
  packages=["curl", "uv"]
)
```

Shells can be activated similar to the `nix` syntax:

```bash
# activates the `shell.py` in the given directory
pynix

# activates an alternative `shell.py`
pynix activate -f alternate_shell.py

# prints the dev environment for a given shell, useful for direnv
pynix print-dev-env
```

## Shell management

`NixShellManager` provides the ability to manage multiple shells in
order to optimize activation. This can do the following:

1. `num_stages`: Speed up environment activation by building an
   "essential" shell first, and then building more feature-complete
   subsequent shells.
2. `block_on_rebuild`: If false, this will rebuild the Nix shell in a
   separate process and utilize the latest build shell instead. This
   is useful for stuff like updates where the change is necessary but
   you don't want to block on it.
3. `history`: You can preserve a number of shells built, which can speed up
   shell activation when swapping branches.

```python
import nix_shell

def build_shell(stage: int, python_version: str = "python313", **kwargs) -> nix_shell.NixShell:
    packages = ["uv", python_version]
    if stage > 1:
        packages = ["git"]
    elif stage > 2:
        packages = ["claude-code"]
    return nix_shell.mk_shell(packages=packages)

manager = nix_shell.mk_manager(
    build_shell,
    num_stages = 3,   # deploy a "minimal" stage first, then subsequent stages
    wait_for_rebuild = False,  # if the shell is outdated, build the new shell in a separate process and use an old shell for now
    history = 5, # preserve the last five shells generated to make re-activating faster
)

shell = manager.build(python_version="python312")
```

Note that these parameters can be changed after the manager is
initialized -- which means, for example, you could do the following:

```
manager = nix_shell.manager(
    build_shell,
    wait_for_rebuild = True,
)

# if our latest shell only updates the `nixpkgs` version, then skip
if manager.only_updates_nixpkgs:
    manager.wait_for_rebuild = False

shell = manager.build(python_version="python312")
```
