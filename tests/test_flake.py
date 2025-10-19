from nix_shell import expr
from nix_shell.flake import get_impure_nixpkgs_ref, to_fetch_tree


def test_fetch_tree():
    ref = "github:nix-systems/default/da67096a3b9bf56a91d16901293e51ba5b49a27e"
    attrs = {
        "lastModified": 1681028828,
        "narHash": "sha256-Vy1rq5AaRuLzOxct8nz4T6wlgyUR7zLU309k9mBC768=",
        "owner": "nix-systems",
        "repo": "default",
        "rev": "da67096a3b9bf56a91d16901293e51ba5b49a27e",
        "type": "github",
    }
    expected = {
        "nixpkgsTree": expr.call("builtins.fetchTree", attrs),
        "nixpkgs": expr.raw("nixpkgsTree.outPath"),
    }

    # both should return the same result
    assert to_fetch_tree(ref) == expected
    assert to_fetch_tree(attrs) == expected


def test_get_impure_nixpkgs_ref():
    ref = get_impure_nixpkgs_ref()
    assert ref is not None
