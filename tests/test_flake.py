from nix_shell.flake import get_locked_from_impure_nixpkgs

# def test_fetch_tree():
#     # This test is disabled because to_fetch_tree function no longer exists
#     pass


def test_get_locked_from_impure_nixpkgs():
    ref = get_locked_from_impure_nixpkgs()
    assert ref is not None
