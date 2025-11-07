{
  python3,
  lib,
}: let
  pyprojectToml = builtins.fromTOML (builtins.readFile ./pyproject.toml);
in python3.pkgs.buildPythonPackage {
  inherit (pyprojectToml.project) name version;
  src = lib.fileset.toSource {
    root = ./.;
    fileset = lib.fileset.unions [
      ./flake.lock
      ./pyproject.toml
      ./README.md

      ./nix_shell
    ];
  };

  format = "pyproject";

  build-system = with python3.pkgs; [ hatchling ];

}
