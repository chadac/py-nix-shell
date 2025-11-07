"""Common Nix variables for convenient access in DSL expressions."""

from nix_shell.dsl.complex import var

pkgs = var("pkgs")
lib = var("lib")
builtins = var("builtins")
