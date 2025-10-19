"""Tests for the nix_shell.nixlang module."""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from nix_shell import cli, dsl
from nix_shell.dsl import FileSet, NixExpr, NixExprType, StorePath, raw
from tests.helpers import assert_match_nix


@patch("nix_shell.cli.store.add")
def test_fileset_with_store_path_objects(mock_store_add):
    """Test FileSet with StorePath objects as sources."""
    mock_store_add.return_value = "/nix/store/abc123-myfile"

    store_path = StorePath(Path("/tmp/myfile"))
    fileset = FileSet(
        paths={
            Path("myfile"): store_path,
        }
    )

    result = fileset.expr()
    expr_str = str(result)

    # Should handle StorePath objects properly
    assert "ln -s" in expr_str
    assert "$out/myfile" in expr_str
    assert "/nix/store/abc123-myfile" in expr_str


@patch("nix_shell.cli.store.add")
def test_fileset_mixed_path_types(mock_store_add):
    """Test FileSet with mix of regular paths and StorePath objects."""
    mock_store_add.side_effect = ["/nix/store/def123-file1", "/nix/store/ghi456-file3"]

    store_path = StorePath(Path("/tmp/file1"))
    fileset = FileSet(
        paths={
            Path("file1"): store_path,
            Path("file2"): Path("/nix/store/abc123-pkg/file2"),
            Path("subdir/file3"): Path("/tmp/file3"),  # Will become StorePath
        }
    )

    result = fileset.expr()
    expr_str = str(result)

    # Should create subdir
    assert "mkdir -p $out/subdir" in expr_str

    # Should link all files
    assert "$out/file1" in expr_str
    assert "$out/file2" in expr_str
    assert "$out/subdir/file3" in expr_str


def test_fileset_nix_store_paths_linked_directly():
    """Test that paths already in /nix/store are linked directly."""
    fileset = FileSet(
        paths={
            Path("git"): Path("/nix/store/abc123-git/bin/git"),
            Path("curl"): Path("/nix/store/def456-curl/bin/curl"),
        }
    )

    result = fileset.expr()
    expr_str = str(result)

    # Should link nix store paths directly without converting to StorePath
    assert "/nix/store/abc123-git/bin/git" in expr_str
    assert "/nix/store/def456-curl/bin/curl" in expr_str
    assert "$out/git" in expr_str
    assert "$out/curl" in expr_str


@patch("nix_shell.cli.store.add")
def test_fileset_non_store_paths_converted(mock_store_add):
    """Test that non-store paths are converted to StorePath."""
    mock_store_add.return_value = "/nix/store/abc123-test"

    fileset = FileSet(
        paths={
            Path("test"): Path("/tmp/test"),
        }
    )

    result = fileset.expr()
    expr_str = str(result)

    # Should have converted non-store path to StorePath and linked it
    assert "/nix/store/abc123-test" in expr_str
    assert "$out/test" in expr_str
    mock_store_add.assert_called_once_with(Path("/tmp/test"))


def test_fileset_empty_paths():
    """Test FileSet with empty paths dict."""
    FileSet(paths={})


def test_fileset_snapshot(snapshot):
    """Test FileSet with files at root level using snapshots."""
    fileset = FileSet(
        paths={
            Path("file1"): Path("/nix/store/abc123-pkg/file1"),
            Path("file2"): Path("/nix/store/def456-pkg/file2"),
        },
        pkgs=raw("pkgs"),
    )

    # Wrap as a function that takes pkgs parameter to make it buildable
    complete_expr = dsl.func([dsl.v("pkgs")], fileset)

    assert_match_nix(snapshot, dsl.dumps(complete_expr), "fileset_root_files.nix")


def test_fileset_duplicate_directories_snapshot(snapshot):
    """Test FileSet doesn't create duplicate mkdir commands."""
    fileset = FileSet(
        paths={
            Path("bin/file1"): Path("/nix/store/abc123-pkg/file1"),
            Path("bin/file2"): Path("/nix/store/def456-pkg/file2"),
            Path("bin/file3"): Path("/nix/store/ghi789-pkg/file3"),
        },
        pkgs=raw("pkgs"),
    )

    # Wrap as a function that takes pkgs parameter to make it buildable
    complete_expr = dsl.func([dsl.v("pkgs")], fileset)

    assert_match_nix(snapshot, dsl.dumps(complete_expr), "fileset_bin_files.nix")


def test_fileset_nested_directories_snapshot(snapshot):
    """Test FileSet with nested directory structure."""
    fileset = FileSet(
        paths={
            Path("bin/hello"): Path("/nix/store/abc123-hello/bin/hello"),
            Path("lib/libhello.so"): Path("/nix/store/abc123-hello/lib/libhello.so"),
            Path("share/doc/README"): Path("/nix/store/abc123-hello/share/doc/README"),
        },
        pkgs=raw("pkgs"),
    )

    # Wrap as a function that takes pkgs parameter to make it buildable
    complete_expr = dsl.func([dsl.v("pkgs")], fileset)

    assert_match_nix(snapshot, dsl.dumps(complete_expr), "fileset_nested_dirs.nix")


def test_fileset_command_escaping_snapshot(snapshot):
    """Test FileSet properly escapes shell commands."""
    fileset = FileSet(
        paths={
            Path("file with spaces"): Path("/nix/store/abc123-pkg/file with spaces"),
            Path("special$chars"): Path("/nix/store/def456-pkg/special$chars"),
        },
        pkgs=raw("pkgs"),
    )

    # Wrap as a function that takes pkgs parameter to make it buildable
    complete_expr = dsl.func([dsl.v("pkgs")], fileset)

    assert_match_nix(snapshot, dsl.dumps(complete_expr), "fileset_escaping.nix")


def test_fileset_custom_pkgs_snapshot(snapshot):
    """Test FileSet with custom pkgs parameter."""
    fileset = dsl.func(
        params=[dsl.v("pkgs")],
        expr=FileSet(
            paths={
                Path("hello"): Path("/nix/store/abc123-hello/bin/hello"),
                Path("world"): Path("/nix/store/def456-world/bin/world"),
            },
            pkgs=raw("pkgs"),
        ),
    )

    assert_match_nix(snapshot, dsl.dumps(fileset), "fileset_custom_pkgs.nix")


def test_store_path_creation():
    """Test StorePath class basic functionality."""
    with tempfile.NamedTemporaryFile() as f:
        f.write(b"test")
        f.flush()
        store_path = StorePath(Path(f.name))
    assert store_path


def test_nixexprtype_default_dumps():
    """Test that NixExprType provides default dumps() for classes with expr()."""

    @dataclass
    class TestExprType(NixExprType):
        value: str

        def expr(self) -> NixExpr:
            return self.value

    test_obj = TestExprType("hello")
    result = test_obj.dumps()

    # Should use the default implementation that returns string values as-is
    assert result == "hello"  # String values returned directly without quotes


@patch("nix_shell.cli.store.add")
def test_store_path_with_nix_store_add(mock_add):
    """Test StorePath calls cli.store.add properly."""
    mock_add.return_value = "/nix/store/abc123-myfile"

    store_path = StorePath(Path("/tmp/myfile"))
    result = store_path.expr()

    mock_add.assert_called_once_with(Path("/tmp/myfile"))
    assert result == "/nix/store/abc123-myfile"


def test_store_path_integration():
    """Integration test: Create a real file, add it to store, and verify it works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        test_file = Path(tmpdir) / "hello.txt"
        test_file.write_text("Hello, World!")

        # Create StorePath and get the Nix expression
        store_path = StorePath(test_file)
        nix_expr = dsl.dumps(store_path)

        # The StorePath should return a store path string
        assert nix_expr.startswith("/nix/store/")
        assert len(nix_expr) > 20  # Store paths are long hashes

        # Verify the file exists in the store and has correct content
        # Note: StorePath.store_path property already strips newlines
        content = Path(store_path.store_path).read_text()
        assert content == "Hello, World!"


def test_fileset_integration():
    """Integration test: Create real files, build FileSet, and verify structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files with different content
        src1 = Path(tmpdir) / "file1.txt"
        src2 = Path(tmpdir) / "subdir" / "file2.txt"
        src2.parent.mkdir(parents=True)

        src1.write_text("Content 1")
        src2.write_text("Content 2")

        # Create FileSet that maps files to different locations
        fileset = FileSet(
            paths={
                Path("bin/hello"): src1,
                Path("lib/world"): src2,
            }
        )

        # Generate and build the FileSet using cli.build
        fileset_expr = dsl.dumps(fileset)

        # Wrap in a complete Nix expression with nixpkgs import
        complete_expr = f"""
        let
          nixpkgs = import <nixpkgs> {{}};
        in
        {fileset_expr}
        """

        # Build the FileSet derivation using cli module
        build_result = cli.build(
            expr=complete_expr, impure=True, no_link=True, print_out_paths=True
        )
        output_path = Path(build_result.strip())

        # Verify the directory structure was created correctly
        assert (output_path / "bin" / "hello").exists()
        assert (output_path / "lib" / "world").exists()

        # Verify the content is correct
        assert (output_path / "bin" / "hello").read_text() == "Content 1"
        assert (output_path / "lib" / "world").read_text() == "Content 2"

        # Verify they are symlinks pointing to the store
        assert (output_path / "bin" / "hello").is_symlink()
        assert (output_path / "lib" / "world").is_symlink()
