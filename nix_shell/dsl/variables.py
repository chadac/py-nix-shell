"""Common Nix variables for convenient access."""

from nix_shell.dsl.complex import var

pkgs = var("pkgs")
lib = var("lib")
builtins = var("builtins")
