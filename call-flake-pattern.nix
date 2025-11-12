{ flake_nix, flake_lock, devenv_nix }:
let
  pkgs = let
    nixpkgs = builtins.getFlake "github:cachix/devenv-nixpkgs/d1c30452ebecfc55185ae6d1c983c09da0c274ff";
  in nixpkgs.legacyPackages.x86_64-linux;

  callFlake = src: let
    flake = builtins.getFlake "github:NixOS/flake-compat/f387cd2afec9419c8ee37694406ca490c3f34ee5";
    func = import "${flake}";
  in (func { inherit src; }).outputs;

  project =
    let
      flakeDir = (
        pkgs.runCommand "virtual-flake" { } ''
          mkdir -p $out
          cat <<NIX_EOF > $out/flake.nix
          ${flake_nix}
          NIX_EOF

          cat <<NIX_EOF > $out/flake.lock
          ${flake_lock}
          NIX_EOF

          cat <<NIX_EOF > $out/devenv.nix
          ${devenv_nix}
          NIX_EOF
        ''
      );
    in callFlake flakeDir;
in project.devShells.x86_64-linux.default
