"""
You can also do ridiculous stuff if you want with this whole setup.
"""

from nix_shell import dsl

# This is equilvanet to creating an mkShell nix expression.
shell = dsl.pkgs["mkShell"](
    {
        "packages": [dsl.pkgs["curl"], dsl.pkgs["openssl"]],
    }
)
