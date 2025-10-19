from pathlib import Path

from nix_shell.utils import format_nix


def assert_match_nix(snapshot, expr_str: str, filename: str | Path) -> None:
    # replace Path.cwd()
    expr_str = expr_str.replace(str(Path.cwd()), "/home/sample-user/workspace")
    return snapshot.assert_match(format_nix(expr_str, raise_if_missing=True), filename)
