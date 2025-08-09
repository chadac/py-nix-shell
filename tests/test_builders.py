from nix_shell.builders import mk_shell_expr


def test_mk_shell_expr_format():
    assert mk_shell_expr(packages=["curl", "openssl"])
