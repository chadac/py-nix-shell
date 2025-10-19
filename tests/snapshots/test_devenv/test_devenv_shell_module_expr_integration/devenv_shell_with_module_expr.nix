let
  pkgs =
    let
      tree = (
        builtins.fetchTree {
          lastModified = 1758532697;
          narHash = "sha256-bhop0bR3u7DCw9/PtLCwr7GwEWDlBSxHp+eVQhCW9t4=";
          owner = "cachix";
          repo = "devenv-nixpkgs";
          rev = "207a4cb0e1253c7658c6736becc6eb9cace1f25f";
          type = "github";
        }
      );
      nixpkgs = tree.outPath;
    in
    (import nixpkgs { system = "x86_64-linux"; });
  devenv = (
    builtins.fetchTree {
      lastModified = 1760890764;
      narHash = "sha256-hCO8y2iJwlVTx6UKUpFY3doqHG5W0znV00mCAneX+FE=";
      owner = "cachix";
      repo = "devenv";
      rev = "8bd9769602d769d427450f64fbd02c80871a186c";
      type = "github";
    }
  );
  shell = (
    pkgs.lib.evalModules {
      modules = [
        "${devenv}/src/modules/top-level.nix"
        {
          _file = "nix_shell.module.Module at nix_shell.devenv:28";
          config =
            let
              nixpkgs = (
                builtins.fetchTree {
                  lastModified = 1758532697;
                  narHash = "sha256-bhop0bR3u7DCw9/PtLCwr7GwEWDlBSxHp+eVQhCW9t4=";
                  owner = "cachix";
                  repo = "devenv-nixpkgs";
                  rev = "207a4cb0e1253c7658c6736becc6eb9cace1f25f";
                  type = "github";
                }
              );
              devenv_lock = (
                builtins.fetchTree {
                  lastModified = 1760890764;
                  narHash = "sha256-hCO8y2iJwlVTx6UKUpFY3doqHG5W0znV00mCAneX+FE=";
                  owner = "cachix";
                  repo = "devenv";
                  rev = "8bd9769602d769d427450f64fbd02c80871a186c";
                  type = "github";
                }
              );
              git_hooks = (
                builtins.fetchTree {
                  lastModified = 1758108966;
                  narHash = "sha256-ytw7ROXaWZ7OfwHrQ9xvjpUWeGVm86pwnEd1QhzawIo=";
                  owner = "cachix";
                  repo = "git-hooks.nix";
                  rev = "54df955a695a84cd47d4a43e08e1feaf90b1fd9b";
                  type = "github";
                }
              );
            in
            {
              _module.args = {
                pkgs = pkgs;
                lib = pkgs.lib;
                inputs = {
                  nixpkgs = nixpkgs;
                  devenv = devenv;
                  git-hooks = git_hooks;
                };
                self = "/home/sample-user/workspace";
              };
              devenv = {
                warnOnNewVersion = false;
                flakesIntegration = false;
                cliVersion = "1.10";
              };
            };
        }
        /nix/store/vlvxbm7fr8x4i1clvqb0gan80kh4dp67-file.txt
      ];
    }
  );
in
shell.config.shell
