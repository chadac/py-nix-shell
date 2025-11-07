import nix_shell

shell = nix_shell.mk_shell(packages=["curl", "openssl"])
