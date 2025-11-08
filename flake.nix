{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    nixpkgs-stable.url = "github:nixos/nixpkgs/release-25.05";
    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    devenv.url = "github:cachix/devenv";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
    git-hooks.url = "github:cachix/git-hooks.nix";
  };

  outputs = inputs: inputs.flake-parts.lib.mkFlake { inherit inputs; } {
    systems = import inputs.systems;
    perSystem = { pkgs, ... }: {
      packages.default = pkgs.callPackage ./. { };
      devShells = {
        default = pkgs.mkShell {
          packages = with pkgs; [ python313 uv just pre-commit ];
        };
        devenv = inputs.devenv.lib.mkShell {
          inherit inputs pkgs;
          modules = [ "${inputs.self}/devenv.nix" ];
        };

        # sample; used for testing as well
        example = pkgs.mkShell {
          packages = with pkgs; [ curl openssl ];
        };
      };
    };
  };
}
