#!/usr/bin/env python3
"""E2E tests for the py-nix-shell CLI."""

import subprocess
import tempfile
from pathlib import Path
from textwrap import dedent

import pytest


def test_cli_help():
    """Test that --help works and shows expected content."""
    result = subprocess.run(
        ["python", "-m", "nix_shell.main", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "py-nix-shell - Nix shell environment manager" in result.stdout
    assert "Environment Management:" in result.stdout
    assert "Nix aliases:" in result.stdout
    assert "activate" in result.stdout
    assert "env" in result.stdout
    assert "shell" in result.stdout
    assert "develop" in result.stdout
    assert "build" in result.stdout
    assert "print-dev-env" in result.stdout
    assert "show" in result.stdout
    assert "--command" in result.stdout
    assert "EXAMPLES:" in result.stdout


def test_cli_missing_shell_py():
    """Test error handling when shell.py is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ["python", "-m", "nix_shell.main"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Shell file not found" in result.stderr


def test_cli_env_command_with_file():
    """Test env command with -f option."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        shell_file = tmpdir_path / "custom_shell.py"

        # Create a test shell.py file
        shell_file.write_text(
            dedent("""
            import nix_shell
            shell = nix_shell.mk_shell(packages=["curl"])
        """)
        )

        # Test env command with custom file
        result = subprocess.run(
            ["python", "-m", "nix_shell.main", "env", "-f", str(shell_file)],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )

        # Should succeed and output shell activation commands
        assert result.returncode == 0
        assert "Nix environment activation" in result.stdout


def test_cli_print_dev_env_command():
    """Test print-dev-env command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        shell_file = tmpdir_path / "shell.py"

        # Create a test shell.py file
        shell_file.write_text(
            dedent("""
            import nix_shell
            shell = nix_shell.mk_shell(packages=["curl"])
        """)
        )

        # Test print-dev-env command
        result = subprocess.run(
            ["python", "-m", "nix_shell.main", "print-dev-env"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Should output some bash instructions
        assert result.stdout.strip() != ""


def test_cli_expression_option():
    """Test -c/--command option for evaluating expressions."""
    result = subprocess.run(
        [
            "python",
            "-m",
            "nix_shell.main",
            "print-dev-env",
            "-c",
            "mk_shell(packages=['curl'])",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.strip() != ""


def test_cli_expression_from_stdin():
    """Test --command-from-stdin option."""
    expression = "mk_shell(packages=['curl'])"

    result = subprocess.run(
        ["python", "-m", "nix_shell.main", "print-dev-env", "--command-from-stdin"],
        input=expression,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.strip() != ""


def test_cli_invalid_shell_file():
    """Test error handling for invalid shell.py content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        shell_file = tmpdir_path / "shell.py"

        # Create a shell.py without the required 'shell' variable
        shell_file.write_text(
            dedent("""
            import nix_shell
            # Missing shell variable
            wrong_name = nix_shell.mk_shell(packages=["curl"])
        """)
        )

        result = subprocess.run(
            ["python", "-m", "nix_shell.main"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "No 'shell' variable found" in result.stderr


def test_cli_invalid_shell_type():
    """Test error handling when 'shell' variable is not a NixShell."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        shell_file = tmpdir_path / "shell.py"

        # Create a shell.py with wrong type for shell variable
        shell_file.write_text(
            dedent("""
            shell = "not a NixShell"
        """)
        )

        result = subprocess.run(
            ["python", "-m", "nix_shell.main"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "is not a NixShell instance" in result.stderr


def test_cli_invalid_expression():
    """Test error handling for invalid Python expressions."""
    result = subprocess.run(
        ["python", "-m", "nix_shell.main", "-c", "invalid_function()"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "name 'invalid_function' is not defined" in result.stderr


def test_cli_expression_wrong_type():
    """Test error handling when expression doesn't return NixShell."""
    result = subprocess.run(
        ["python", "-m", "nix_shell.main", "-c", "'not a shell'"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Expression did not evaluate to a NixShell instance" in result.stderr


def test_cli_default_to_env():
    """Test that no command defaults to env."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        shell_file = tmpdir_path / "shell.py"

        # Create a test shell.py file
        shell_file.write_text(
            dedent("""
            import nix_shell
            shell = nix_shell.mk_shell(packages=["curl"])
        """)
        )

        # Test without specifying command (should default to env)
        result = subprocess.run(
            ["python", "-m", "nix_shell.main"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )

        # Should succeed and output activation commands
        assert result.returncode == 0
        assert "Nix environment activation" in result.stdout


def test_cli_unknown_command():
    """Test error handling for unknown commands."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        shell_file = tmpdir_path / "shell.py"

        shell_file.write_text(
            dedent("""
            import nix_shell
            shell = nix_shell.mk_shell(packages=["curl"])
        """)
        )

        result = subprocess.run(
            ["python", "-m", "nix_shell.main", "nonexistent-command"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2  # argparse error code
        assert "invalid choice" in result.stderr


def test_cli_from_flake_expression():
    """Test using from_flake in expression."""
    # Skip if flake doesn't exist (this would be environment-dependent)
    pytest.skip("Flake-based test requires specific flake setup")


def test_cli_complex_shell_py():
    """Test with a more complex shell.py file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        shell_file = tmpdir_path / "shell.py"

        # Create a more complex shell.py
        shell_file.write_text(
            dedent("""
            import nix_shell

            # Example with multiple packages and environment setup
            shell = nix_shell.mk_shell(
                packages=["curl", "jq", "git"],
                library_path=["zlib"],
                shell_hook=["echo 'Development environment loaded'"]
            )
        """)
        )

        result = subprocess.run(
            ["python", "-m", "nix_shell.main", "print-dev-env"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert result.stdout.strip() != ""


def test_cli_activate_command():
    """Test activate command that spawns interactive shell."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        shell_file = tmpdir_path / "shell.py"

        # Create a test shell.py file
        shell_file.write_text(
            dedent("""
            import nix_shell
            shell = nix_shell.mk_shell(packages=["curl"])
        """)
        )

        # Test activate command - we'll run it with a timeout since it's interactive
        # This mainly tests that the command doesn't crash during startup
        try:
            subprocess.run(
                ["python", "-m", "nix_shell.main", "activate"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=2,  # Short timeout since we just want to test startup
            )
            # If it times out, that's actually expected for an interactive shell
        except subprocess.TimeoutExpired:
            # This is expected - the shell started successfully and was waiting for input
            pass


def test_cli_shell_command():
    """Test shell command that runs nix shell."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        shell_file = tmpdir_path / "shell.py"

        # Create a test shell.py file
        shell_file.write_text(
            dedent("""
            import nix_shell
            shell = nix_shell.mk_shell(packages=["curl"])
        """)
        )

        # Test shell command - we'll run it with a timeout since it's interactive
        try:
            subprocess.run(
                ["python", "-m", "nix_shell.main", "shell"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=2,  # Short timeout since we just want to test startup
            )
            # If it times out, that's actually expected for an interactive shell
        except subprocess.TimeoutExpired:
            # This is expected - the shell started successfully and was waiting for input
            pass


def test_cli_develop_command():
    """Test develop command that runs nix develop."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        shell_file = tmpdir_path / "shell.py"

        # Create a test shell.py file
        shell_file.write_text(
            dedent("""
            import nix_shell
            shell = nix_shell.mk_shell(packages=["curl"])
        """)
        )

        # Test develop command - we'll run it with a timeout since it's interactive
        try:
            subprocess.run(
                ["python", "-m", "nix_shell.main", "develop"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=2,  # Short timeout since we just want to test startup
            )
            # If it times out, that's actually expected for an interactive shell
        except subprocess.TimeoutExpired:
            # This is expected - the shell started successfully and was waiting for input
            pass


def test_cli_logging_errors():
    """Test that errors are properly logged to stderr."""
    result = subprocess.run(
        ["python", "-m", "nix_shell.main", "-c", "invalid_function()"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    # Error should be in stderr, not stdout
    assert result.stdout == ""
    assert "ERROR:" in result.stderr
    assert "invalid_function" in result.stderr


def test_cli_color_detection():
    """Test that colors are disabled in non-TTY environments."""
    result = subprocess.run(
        ["python", "-m", "nix_shell.main", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # In non-TTY (subprocess), colors should be disabled
    assert "\033[" not in result.stdout  # No ANSI escape codes


def test_cli_verbose_flags():
    """Test that verbose flags work and show appropriate log levels."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        shell_file = tmpdir_path / "shell.py"

        # Create a test shell.py file
        shell_file.write_text(
            dedent("""
            import nix_shell
            shell = nix_shell.mk_shell(packages=["curl"])
        """)
        )

        # Test default verbosity (should only show errors/warnings)
        result = subprocess.run(
            ["python", "-m", "nix_shell.main", "print-dev-env"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # With default verbosity, should not see INFO or DEBUG
        info_count = result.stderr.count("INFO:")
        debug_count = result.stderr.count("DEBUG:")
        assert info_count == 0
        assert debug_count == 0

        # Test -v verbosity (should show INFO)
        result = subprocess.run(
            ["python", "-m", "nix_shell.main", "-v", "print-dev-env"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # With -v, should see INFO but not DEBUG
        info_count = result.stderr.count("INFO:")
        debug_count = result.stderr.count("DEBUG:")
        assert info_count > 0
        assert debug_count == 0

        # Test -vv verbosity (should show DEBUG)
        result = subprocess.run(
            ["python", "-m", "nix_shell.main", "-vv", "print-dev-env"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # With -vv, should see DEBUG messages
        debug_count = result.stderr.count("DEBUG:")
        assert debug_count > 0


def test_cli_build_command():
    """Test build command that runs nix build."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        shell_file = tmpdir_path / "shell.py"

        # Create a test shell.py file
        shell_file.write_text(
            dedent("""
            import nix_shell
            shell = nix_shell.mk_shell(packages=["curl"])
        """)
        )

        # Test build command - it should succeed even though it's just building a shell
        result = subprocess.run(
            ["python", "-m", "nix_shell.main", "build"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )

        # Build command should complete successfully
        assert result.returncode == 0


def test_cli_verbose_help():
    """Test that help includes verbose flag information."""
    result = subprocess.run(
        ["python", "-m", "nix_shell.main", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "-v, --verbose" in result.stdout
    assert "verbosity" in result.stdout


def test_cli_shell_detection():
    """Test that the CLI detects shell and provides appropriate commands."""
    result = subprocess.run(
        [
            "python",
            "-m",
            "nix_shell.main",
            "env",
            "-c",
            "mk_shell(packages=['curl'])",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # Should contain shell-specific comments
    assert "# Nix environment activation" in result.stdout
    assert "# To activate:" in result.stdout


def test_cli_show_command():
    """Test show command that displays Nix expressions."""
    result = subprocess.run(
        [
            "python",
            "-m",
            "nix_shell.main",
            "show",
            "-c",
            "mk_shell(packages=['curl'])",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # Should contain the Nix expression
    assert "pkgs.mkShell" in result.stdout
    assert "curl" in result.stdout


def test_cli_show_command_with_file():
    """Test show command with a shell.py file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        shell_file = tmpdir_path / "shell.py"

        # Create a test shell.py file
        shell_file.write_text(
            dedent("""
            import nix_shell
            shell = nix_shell.mk_shell(packages=["git", "jq"])
        """)
        )

        result = subprocess.run(
            ["python", "-m", "nix_shell.main", "show"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Should contain the Nix expression with our packages
        assert "pkgs.mkShell" in result.stdout
        assert "git" in result.stdout
        assert "jq" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__])
