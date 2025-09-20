## shell.py

`py-nix-shell` provides an interface for quickly building new Nix
shells using Python syntax via the `py-nix-shell` CLI utility.

Usage is simple; using the same
[builders](https://chadac.github.io/py-nix-shell/builders.md)
specified above, if you export it as a global variable named `shell`
you can use it with `py-nix-shell`:

```python
import nix_shell
shell = nix_shell.mk_shell(
  packages=["curl", "uv"]
)
```

Shells can be activated similar to the `nix` syntax:

```bash
# activates the `shell.py` in the given directory
py-nix-shell

# activates an alternative `shell.py`
py-nix-shell activate alternate_shell.py

# prints the dev environment for a given shell, useful for direnv
py-nix-shell print-dev-env
```
