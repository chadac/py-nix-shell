"""Tests for the nix_shell.utils module."""

from pathlib import Path

from nix_shell.utils import find_shared_root


def test_find_shared_root_empty_list():
    """Test shared root with empty list returns current directory."""
    result = find_shared_root([])
    assert result == Path(".")


def test_find_shared_root_single_file():
    """Test shared root with single file returns its parent directory."""
    result = find_shared_root([Path("/home/user/file.txt")])
    assert result == Path("/home/user")


def test_find_shared_root_single_directory():
    """Test shared root with single directory returns the directory itself."""
    result = find_shared_root([Path("/home/user")])
    assert result == Path("/home/user")


def test_find_shared_root_same_directory():
    """Test shared root when all paths are in the same directory."""
    paths = [
        Path("/home/user/file1.txt"),
        Path("/home/user/file2.txt"),
        Path("/home/user/file3.txt"),
    ]
    result = find_shared_root(paths)
    assert result == Path("/home/user")


def test_find_shared_root_nested_paths():
    """Test shared root with nested paths."""
    paths = [
        Path("/home/user/docs/file1.txt"),
        Path("/home/user/docs/subdir/file2.txt"),
        Path("/home/user/docs/another/file3.txt"),
    ]
    result = find_shared_root(paths)
    assert result == Path("/home/user/docs")


def test_find_shared_root_different_branches():
    """Test shared root with paths in different directory branches."""
    paths = [
        Path("/home/user/documents/file1.txt"),
        Path("/home/user/pictures/file2.txt"),
        Path("/home/user/downloads/file3.txt"),
    ]
    result = find_shared_root(paths)
    assert result == Path("/home/user")


def test_find_shared_root_completely_different():
    """Test shared root with completely different paths."""
    paths = [
        Path("/home/user1/file1.txt"),
        Path("/opt/software/file2.txt"),
        Path("/var/log/file3.txt"),
    ]
    result = find_shared_root(paths)
    assert result == Path("/")


def test_find_shared_root_relative_paths():
    """Test shared root with relative paths."""
    paths = [
        Path("project/src/main.py"),
        Path("project/src/utils.py"),
        Path("project/tests/test_main.py"),
    ]
    result = find_shared_root(paths)
    # Since we resolve to absolute paths, the result will be absolute
    expected = (Path.cwd() / "project").resolve()
    assert result == expected


def test_find_shared_root_mixed_relative_absolute():
    """Test shared root with mixed relative and absolute paths."""
    # Note: This will resolve relative paths to absolute ones
    paths = [
        Path("file1.txt"),
        Path("/tmp/file2.txt"),
    ]
    result = find_shared_root(paths)
    # Result will be "/" since we're comparing resolved absolute paths
    assert result == Path("/")


def test_find_shared_root_nix_store_paths():
    """Test shared root with typical Nix store paths."""
    paths = [
        Path("/nix/store/abc123-git-2.40.0/bin/git"),
        Path("/nix/store/def456-curl-8.0.0/bin/curl"),
        Path("/nix/store/ghi789-python-3.11/bin/python"),
    ]
    result = find_shared_root(paths)
    assert result == Path("/nix/store")


def test_find_shared_root_nix_store_same_package():
    """Test shared root with files from the same Nix package."""
    paths = [
        Path("/nix/store/abc123-git-2.40.0/bin/git"),
        Path("/nix/store/abc123-git-2.40.0/libexec/git-core/git-add"),
        Path("/nix/store/abc123-git-2.40.0/share/man/man1/git.1"),
    ]
    result = find_shared_root(paths)
    assert result == Path("/nix/store/abc123-git-2.40.0")


def test_find_shared_root_directories_only():
    """Test shared root with directory paths only."""
    paths = [
        Path("/home/user/projects/proj1"),
        Path("/home/user/projects/proj2"),
        Path("/home/user/projects/proj3"),
    ]
    result = find_shared_root(paths)
    assert result == Path("/home/user/projects")


def test_find_shared_root_root_paths():
    """Test shared root with paths directly under root."""
    paths = [
        Path("/usr/bin/git"),
        Path("/bin/bash"),
        Path("/opt/tool"),
    ]
    result = find_shared_root(paths)
    assert result == Path("/")


def test_find_shared_root_identical_paths():
    """Test shared root with identical paths."""
    path = Path("/home/user/document.txt")
    paths = [path, path, path]
    result = find_shared_root(paths)
    assert result == Path("/home/user")


def test_find_shared_root_current_directory_relative():
    """Test shared root with relative paths in current directory."""
    paths = [
        Path("file1.txt"),
        Path("file2.txt"),
    ]
    result = find_shared_root(paths)
    # Since these are relative paths that resolve to the current working directory,
    # the shared root should be the current working directory (absolute)
    expected = Path.cwd()
    assert result == expected
