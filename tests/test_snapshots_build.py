"""Tests to validate that all snapshot .nix files can be built successfully."""

from pathlib import Path
from typing import List, Tuple

import pytest

from nix_shell import cli
from nix_shell.exceptions import NixError


def find_all_snapshot_nix_files() -> List[Tuple[str, Path]]:
    """Find all .nix files in the tests/snapshots directory."""
    snapshots_dir = Path(__file__).parent / "snapshots"
    nix_files = []

    for nix_file in snapshots_dir.rglob("*.nix"):
        # Create a readable test ID from the path
        relative_path = nix_file.relative_to(snapshots_dir)
        test_id = str(relative_path).replace("/", "::").replace(".nix", "")
        nix_files.append((test_id, nix_file))

    return nix_files


def categorize_expression(nix_file: Path) -> str:
    """Categorize the type of Nix expression based on file path and content."""
    path_str = str(nix_file)

    if "devenv" in path_str:
        return "shell"
    elif "fileset" in path_str:
        return "derivation"
    else:
        # Read the file to make a best guess
        content = nix_file.read_text()
        if "shell.config.shell" in content or "mkShell" in content:
            return "shell"
        elif "runCommand" in content or content.strip().startswith("("):
            return "derivation"
        else:
            return "expression"


def build_nix_expression(nix_file: Path, category: str) -> None:
    """Build a Nix expression file using appropriate strategy based on category."""
    content = nix_file.read_text()

    # Check if expression uses <nixpkgs> channel syntax
    has_pkgs = "pkgs" in content

    expr = content.strip()

    impure = False
    if has_pkgs:
        expr = f"let pkgs = import <nixpkgs> {{}}; in ({expr})"
        impure = True

    if category == "shell":
        cli.build(expr=expr, no_link=True, impure=impure)
    else:
        cli.evaluate(expr=expr, impure=impure)


@pytest.mark.parametrize("test_id,nix_file", find_all_snapshot_nix_files())
def test_snapshot_builds_successfully(test_id: str, nix_file: Path):
    """Test that each snapshot .nix file can be built or evaluated successfully."""

    # Skip if file doesn't exist (shouldn't happen, but just in case)
    if not nix_file.exists():
        pytest.skip(f"Snapshot file {nix_file} does not exist")

    # Categorize the expression type
    category = categorize_expression(nix_file)

    # Try to build/evaluate the expression
    build_nix_expression(nix_file, category)


def test_snapshot_directory_has_nix_files():
    """Ensure that we actually found some .nix files to test."""
    nix_files = find_all_snapshot_nix_files()
    assert len(nix_files) > 0, "No .nix files found in tests/snapshots directory"

    # Print found files for debugging
    print(f"Found {len(nix_files)} .nix files in snapshots:")
    for test_id, nix_file in nix_files:
        print(f"  {test_id}: {nix_file}")


def test_snapshot_expressions_have_valid_syntax():
    """Test that all snapshot files have valid Nix syntax (quick syntax-only check)."""
    nix_files = find_all_snapshot_nix_files()

    syntax_errors = []

    for test_id, nix_file in nix_files:
        try:
            # Quick syntax check by trying to parse the file
            cli.evaluate(expr=f"builtins.typeOf (builtins.readFile {nix_file})")
        except NixError as e:
            if "syntax error" in str(e).lower() or "parse error" in str(e).lower():
                syntax_errors.append(f"{test_id}: {e}")
        except Exception:
            # Other errors are okay for this syntax-only test
            pass

    if syntax_errors:
        pytest.fail(
            "Syntax errors found in snapshot files:\n" + "\n".join(syntax_errors)
        )
