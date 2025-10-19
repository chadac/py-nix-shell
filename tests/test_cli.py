"""Tests for the nix_shell.cli module."""

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from nix_shell import cli

# Test the NixBuildArgs TypedDict and related functionality


def test_parse_args_with_ref():
    """Test parsing arguments with a flake reference."""
    args = cli._parse_args(ref="github:nixos/nixpkgs")
    assert args == ["github:nixos/nixpkgs"]


def test_parse_args_with_expr():
    """Test parsing arguments with a Nix expression."""
    args = cli._parse_args(expr="(import <nixpkgs> {}).hello")
    assert args == ["--expr", "(import <nixpkgs> {}).hello"]


def test_parse_args_with_file():
    """Test parsing arguments with a file path."""
    args = cli._parse_args(file="shell.nix")
    assert args == ["-f", "shell.nix"]


def test_parse_args_with_file_and_installable():
    """Test parsing arguments with file and installable."""
    args = cli._parse_args(file="default.nix", installable="mypackage")
    assert args == ["-f", "default.nix", "mypackage"]


def test_parse_args_with_impure():
    """Test parsing arguments with impure flag."""
    args = cli._parse_args(ref="github:nixos/nixpkgs", impure=True)
    assert args == ["github:nixos/nixpkgs", "--impure"]


def test_parse_args_with_include():
    """Test parsing arguments with include paths."""
    args = cli._parse_args(
        ref="github:nixos/nixpkgs",
        include=(("nixpkgs", "/nix/store/abc123"), ("mylib", "/path/to/lib")),
    )
    expected = [
        "github:nixos/nixpkgs",
        "-I",
        "nixpkgs=/nix/store/abc123",
        "-I",
        "mylib=/path/to/lib",
    ]
    assert args == expected


# Test the high-level Nix command wrappers


@patch("subprocess.check_output")
def test_build_basic(mock_subprocess):
    """Test basic nix build command."""
    mock_subprocess.return_value = b"/nix/store/abc123-hello\n"

    result = cli.build(ref="nixpkgs#hello")

    mock_subprocess.assert_called_once_with(["nix", "build", "nixpkgs#hello"])
    assert result == "/nix/store/abc123-hello\n"


@patch("subprocess.check_output")
def test_build_with_options(mock_subprocess):
    """Test nix build with various options."""
    mock_subprocess.return_value = b"/nix/store/abc123-hello\n"

    cli.build(ref="nixpkgs#hello", out_link=Path("/tmp/result"), print_out_paths=True)

    mock_subprocess.assert_called_once_with(
        [
            "nix",
            "build",
            "nixpkgs#hello",
            "--out-link",
            "/tmp/result",
            "--print-out-paths",
        ]
    )


@patch("subprocess.check_output")
def test_build_no_link(mock_subprocess):
    """Test nix build with no-link option."""
    mock_subprocess.return_value = b""

    cli.build(ref="nixpkgs#hello", no_link=True)

    mock_subprocess.assert_called_once_with(
        ["nix", "build", "nixpkgs#hello", "--no-link"]
    )


@patch("subprocess.check_output")
def test_print_dev_env(mock_subprocess):
    """Test nix print-dev-env command."""
    mock_subprocess.return_value = b"export PATH=/nix/store/abc123/bin:$PATH\n"

    result = cli.print_dev_env(ref="nixpkgs#hello")

    mock_subprocess.assert_called_once_with(["nix", "print-dev-env", "nixpkgs#hello"])
    assert result == "export PATH=/nix/store/abc123/bin:$PATH\n"


@patch("subprocess.check_output")
def test_evaluate_raw(mock_subprocess):
    """Test nix eval with raw output."""
    mock_subprocess.return_value = b"x86_64-linux"

    result = cli.evaluate(expr="builtins.currentSystem", raw=True)

    mock_subprocess.assert_called_once_with(
        ["nix", "eval", "--expr", "builtins.currentSystem", "--raw"]
    )
    assert result == "x86_64-linux"


@patch("subprocess.check_output")
def test_evaluate_non_raw(mock_subprocess):
    """Test nix eval without raw output."""
    mock_subprocess.return_value = b'"x86_64-linux"'

    result = cli.evaluate(expr="builtins.currentSystem", raw=False)

    mock_subprocess.assert_called_once_with(
        ["nix", "eval", "--expr", "builtins.currentSystem"]
    )
    assert result == '"x86_64-linux"'


# Test cached utility functions


@patch("nix_shell.cli.evaluate")
def test_current_system_cached(mock_evaluate):
    """Test that current_system is cached."""
    # Clear the cache before testing
    cli.current_system.cache_clear()
    mock_evaluate.return_value = "x86_64-linux"

    # Call twice
    result1 = cli.current_system()
    result2 = cli.current_system()

    # Should only call evaluate once due to caching
    mock_evaluate.assert_called_once_with(expr="builtins.currentSystem", impure=True)
    assert result1 == "x86_64-linux"
    assert result2 == "x86_64-linux"


@patch("nix_shell.cli.evaluate")
def test_impure_nixpkgs_path_cached(mock_evaluate):
    """Test that impure_nixpkgs_path is cached."""
    # Clear the cache before testing
    cli.impure_nixpkgs_path.cache_clear()
    mock_evaluate.return_value = "/nix/store/abc123-nixpkgs"

    # Call twice
    result1 = cli.impure_nixpkgs_path()
    result2 = cli.impure_nixpkgs_path()

    # Should only call evaluate once due to caching
    mock_evaluate.assert_called_once_with(expr="<nixpkgs>", impure=True, raw=True)
    assert result1 == "/nix/store/abc123-nixpkgs"
    assert result2 == "/nix/store/abc123-nixpkgs"


@patch("nix_shell.cli.evaluate")
def test_impure_nixpkgs_path_returns_unquoted_path(mock_evaluate):
    """Test that impure_nixpkgs_path returns a clean path without quotes."""
    # Clear the cache before testing
    cli.impure_nixpkgs_path.cache_clear()
    mock_evaluate.return_value = "/nix/store/xyz789-nixpkgs-source"

    result = cli.impure_nixpkgs_path()

    # Should call evaluate with raw=True to avoid quotes
    mock_evaluate.assert_called_once_with(expr="<nixpkgs>", impure=True, raw=True)
    # Should return the actual path, not a quoted string
    assert result == "/nix/store/xyz789-nixpkgs-source"
    assert not result.startswith('"')
    assert not result.endswith('"')


# Test derivation-related commands


@patch("subprocess.check_output")
def test_derivation_show(mock_subprocess):
    """Test nix derivation show command."""
    mock_output = {
        "/nix/store/abc123.drv": {
            "outputs": {"out": {"path": "/nix/store/def456"}},
            "builder": "/nix/store/bash123/bin/bash",
        }
    }
    mock_subprocess.return_value = json.dumps(mock_output).encode()

    result = cli.derivation.show(ref="nixpkgs#hello")

    mock_subprocess.assert_called_once_with(
        ["nix", "derivation", "show", "nixpkgs#hello"]
    )
    assert result == json.dumps(mock_output)


# Test flake-related commands


@patch("subprocess.check_output")
def test_flake_metadata(mock_subprocess):
    """Test nix flake metadata command."""
    mock_metadata = {
        "description": "A collection of packages for the Nix package manager",
        "locked": {
            "lastModified": 1234567890,
            "narHash": "sha256-abc123...",
            "owner": "NixOS",
            "repo": "nixpkgs",
            "rev": "abc123def456",
            "type": "github",
        },
    }
    mock_subprocess.return_value = json.dumps(mock_metadata).encode()

    result = cli.flake.metadata("nixpkgs")

    mock_subprocess.assert_called_once_with(
        ["nix", "flake", "metadata", "nixpkgs", "--json"]
    )
    assert result == mock_metadata


# Test store-related commands


@patch("subprocess.check_output")
def test_store_add(mock_subprocess):
    """Test nix store add command."""
    mock_subprocess.return_value = b"/nix/store/abc123-myfile\n"

    result = cli.store.add(Path("/tmp/myfile"))

    mock_subprocess.assert_called_once_with(["nix", "store", "add", "/tmp/myfile"])
    assert result == "/nix/store/abc123-myfile\n"


# Test error handling in CLI functions


@patch("subprocess.check_output")
def test_subprocess_error_propagation(mock_subprocess):
    """Test that subprocess errors are propagated."""
    mock_subprocess.side_effect = subprocess.CalledProcessError(
        1, ["nix", "build", "nonexistent"], "error: package not found"
    )

    with pytest.raises(subprocess.CalledProcessError):
        cli.build(ref="nonexistent")


def test_parse_args_empty():
    """Test parsing empty arguments."""
    args = cli._parse_args()
    assert args == []


def test_parse_args_multiple_sources_prioritizes_ref():
    """Test that ref takes priority over other sources."""
    args = cli._parse_args(
        ref="github:nixos/nixpkgs",
        expr="(import <nixpkgs> {}).hello",
        file="shell.nix",
    )
    # Should only include the ref, not expr or file
    assert args == ["github:nixos/nixpkgs"]


# Integration-style tests that test command composition


@patch("subprocess.check_output")
def test_complete_build_workflow(mock_subprocess):
    """Test a complete build workflow with multiple options."""
    mock_subprocess.return_value = b"/nix/store/result123-package\n"

    result = cli.build(
        expr="(import <nixpkgs> {}).hello",
        impure=True,
        include=(("nixpkgs", "/custom/nixpkgs"),),
        no_link=True,
        print_out_paths=True,
    )

    expected_cmd = [
        "nix",
        "build",
        "--expr",
        "(import <nixpkgs> {}).hello",
        "--impure",
        "-I",
        "nixpkgs=/custom/nixpkgs",
        "--no-link",
        "--print-out-paths",
    ]
    mock_subprocess.assert_called_once_with(expected_cmd)
    assert result == "/nix/store/result123-package\n"
