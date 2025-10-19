{
  python3,
  lib,

  version ? "0.0.1",
}: let
in python3.pkgs.buildPythonPackage {
  name = "py-nix-shell";
  inherit version;

  src = lib.cleanSource ./.;
}
