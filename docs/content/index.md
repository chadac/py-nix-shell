<a id="nix_shell.exceptions"></a>

# nix\_shell.exceptions

<a id="nix_shell._nix"></a>

# nix\_shell.\_nix

Interface for invoking the Nix CLI from Python.

<a id="nix_shell.builders"></a>

# nix\_shell.builders

<a id="nix_shell.builders.FlakeRefParams"></a>

## FlakeRefParams Objects

```python
class FlakeRefParams(TypedDict)
```

Parameters to provide for building Flake shells.

<a id="nix_shell.builders.from_flake"></a>

#### from\_flake

```python
def from_flake(**kwargs: Unpack[FlakeRefParams]) -> NixSubprocess
```

Create a Nix shell from a flake.

**Arguments**:

- `flake`: Flake reference to use for shell.

<a id="nix_shell.constants"></a>

# nix\_shell.constants

<a id="nix_shell.flake"></a>

# nix\_shell.flake

<a id="nix_shell.nix_subprocess"></a>

# nix\_shell.nix\_subprocess

<a id="nix_shell.nixlang"></a>

# nix\_shell.nixlang

Deserializer for Nix language constructs.

