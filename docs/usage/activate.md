# Nix shell activation

In some cases, you may want to distribute Nix utilities alongside an
application. For example:

1. For use with a Python CLI utility that needs to call specific
   versions of dependencies;
2. To ensure complex Python applications that depend on calling
   `subprocess.run` are able to source the Python path properly;
3. To work around weird issues such as with OSX's [SIP
   protection](https://developer.apple.com/library/archive/documentation/Security/Conceptual/System_Integrity_Protection_Guide/RuntimeProtections/RuntimeProtections.html)
   so that Python applications always link the proper library versions
   of packages.

Usage is simple:

```python
import nix_shell

shell = nix_shell.mk_shell(packages=["curl"], library_path=["zlib"])

shell.activate()

# subprocess.run now prefers the Nix versions of packages
import subprocess
subprocess.run(["which", "curl"])

# libraries like `ctypes` will also behave properly
import ctypes.util
ctypes.util.find_library("z")
```
