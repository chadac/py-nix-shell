from nix_shell import _nix
from nix_shell.nix_subprocess import NixSubprocess, gen_shell_script


NIXPKGS = f"""
  nixpkgs = builtins.fetchTarball {{
    url = "https://github.com/NixOS/nixpkgs/archive/23.11.tar.gz";
    sha256 = "sha256:1ndiv385w1qyb3b18vw13991fzb9wg4cl21wglk89grsfsnra41k";
  }};
  pkgs = import nixpkgs {{ system = "{_nix.current_system()}"; }};
"""

SAMPLE_EXPR = f"""
let
  {NIXPKGS}
in pkgs.mkShell {{
  packages = [ pkgs.git pkgs.which ];
}}
"""


def test_dev_env():
    shell_script = gen_shell_script(expr=SAMPLE_EXPR)
    assert shell_script == """#!/nix/store/q1c2flcykgr4wwg5a6h450hxbk4ch589-bash-5.2-p15/bin/bash

source /nix/store/5rdd3ziwdxlz7m60c0wkag8gbnz9qzyr-nix-shell

eval "$@"
"""


def test_shell_run():
    shell = NixSubprocess.build(expr=SAMPLE_EXPR)
    assert shell.check_output(["which", "git"]).decode() == "/nix/store/zrs710jpfn7ngy5z4c6rrwwjq33b2a0y-git-2.42.0/bin/git\n"
    assert shell.check_output(["git", "--version"]).decode() == "git version 2.42.0\n"
