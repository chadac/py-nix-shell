#!/usr/bin/env python3
"""py-nix-shell CLI entry point."""

import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import nix_shell
from nix_shell.build import NixShell
from nix_shell.exceptions import NixError


class Colors:
    """ANSI color codes for terminal output."""

    # Only use colors if stdout is a TTY and colors are supported
    _use_colors = sys.stdout.isatty() and os.getenv("NO_COLOR") is None

    if _use_colors:
        HEADER = "\033[95m"
        BLUE = "\033[94m"
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        BOLD = "\033[1m"
        DIM = "\033[2m"
        UNDERLINE = "\033[4m"
        END = "\033[0m"
    else:
        HEADER = BLUE = CYAN = GREEN = YELLOW = RED = BOLD = DIM = UNDERLINE = END = ""


class ColoredLogFormatter(logging.Formatter):
    """Custom log formatter with colors for different log levels."""

    LEVEL_COLORS = {
        logging.DEBUG: Colors.DIM,
        logging.INFO: Colors.BLUE,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.BOLD + Colors.RED,
    }

    def format(self, record):
        # Make a copy to avoid modifying the original record
        record_copy = logging.makeLogRecord(record.__dict__)

        if Colors._use_colors:
            level_color = self.LEVEL_COLORS.get(record_copy.levelno, "")
            record_copy.levelname = (
                f"{level_color}{record_copy.levelname:5s}{Colors.END}"
            )

            # Color the message based on level
            if record_copy.levelno >= logging.ERROR:
                record_copy.msg = f"{Colors.RED}{record_copy.msg}{Colors.END}"
            elif record_copy.levelno >= logging.WARNING:
                record_copy.msg = f"{Colors.YELLOW}{record_copy.msg}{Colors.END}"

        return super().format(record_copy)


class ColoredHelpFormatter(argparse.HelpFormatter):
    """Custom help formatter with colors and better organization."""

    def format_help(self):
        help_text = f"""{Colors.BOLD}{Colors.BLUE}py-nix-shell{Colors.END} - {Colors.DIM}Nix shell environment manager{Colors.END}

{Colors.BOLD}USAGE:{Colors.END}
  {Colors.GREEN}pynix{Colors.END} {Colors.CYAN}[COMMAND]{Colors.END} {Colors.DIM}[OPTIONS]{Colors.END}

{Colors.BOLD}COMMANDS:{Colors.END}
  {Colors.BOLD}Environment Management:{Colors.END}
    {Colors.GREEN}env{Colors.END}        {Colors.DIM}(default){Colors.END} Print shell activation script
    {Colors.GREEN}activate{Colors.END}   Spawn interactive shell with environment loaded

  {Colors.BOLD}Nix aliases:{Colors.END}
    {Colors.GREEN}shell{Colors.END}      Run 'nix shell' directly
    {Colors.GREEN}develop{Colors.END}    Run 'nix develop' directly
    {Colors.GREEN}build{Colors.END}      Run 'nix build' directly
    {Colors.GREEN}print-dev-env{Colors.END}  Print raw 'nix print-dev-env' output

  {Colors.BOLD}Useful tools:{Colors.END}
    {Colors.GREEN}show{Colors.END}       Display the Nix expression to be evaluated

{Colors.BOLD}OPTIONS:{Colors.END}
  {Colors.CYAN}-h, --help{Colors.END}              Show this help message
  {Colors.CYAN}-c, --command{Colors.END} {Colors.YELLOW}EXPR{Colors.END}      Evaluate Python expression to build shell
  {Colors.CYAN}--command-from-stdin{Colors.END}    Read expression from stdin
  {Colors.CYAN}-f FILE{Colors.END}                 Use custom shell file (default: shell.py)
  {Colors.CYAN}-v, --verbose{Colors.END}           Increase verbosity (-v=INFO, -vv=DEBUG, -vvv=TRACE)

{Colors.BOLD}EXAMPLES:{Colors.END}
  {Colors.DIM}# Use default shell.py and get activation script{Colors.END}
  {Colors.GREEN}pynix{Colors.END}

  {Colors.DIM}# Spawn interactive shell{Colors.END}
  {Colors.GREEN}pynix activate{Colors.END}

  {Colors.DIM}# Quick shell with packages{Colors.END}
  {Colors.GREEN}pynix shell{Colors.END} {Colors.CYAN}-c{Colors.END} {Colors.YELLOW}"mk_shell(packages=['curl', 'jq'])"{Colors.END}

  {Colors.DIM}# Use custom shell file{Colors.END}
  {Colors.GREEN}pynix activate{Colors.END} {Colors.CYAN}-f{Colors.END} {Colors.YELLOW}my_shell.py{Colors.END}

  {Colors.DIM}# Activate in your shell{Colors.END}
  {Colors.GREEN}eval "$(pynix env)"{Colors.END}

{Colors.DIM}For more info: https://github.com/chadac/py-nix-shell{Colors.END}
"""
        return help_text


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Set up colored logging for py-nix-shell."""
    logger = logging.getLogger("py-nix-shell")

    if logger.handlers:
        return logger  # Already configured

    logger.setLevel(level)

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Create formatter
    formatter = ColoredLogFormatter(fmt="%(levelname)s: %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


def get_default_namespace() -> dict[str, Any]:
    return {k: v for k, v in nix_shell.__dict__.items() if not k.startswith("_")}


def load_shell_from_file(file_path: Path) -> NixShell:
    """Load a shell from a Python file by executing it and extracting the 'shell' variable."""
    if not file_path.exists():
        raise FileNotFoundError(f"Shell file not found: {file_path}")

    # Execute the Python file and extract the shell variable
    namespace: dict[str, Any] = get_default_namespace()
    exec(file_path.read_text(), namespace)

    if "shell" not in namespace:
        raise ValueError(f"No 'shell' variable found in {file_path}")

    shell = namespace["shell"]
    if not isinstance(shell, NixShell):
        raise ValueError(f"'shell' variable in {file_path} is not a NixShell instance")

    return shell


def load_shell_from_expression(expr: str) -> NixShell:
    """Load a shell from a Python expression."""
    # Import all public nix_shell members into the namespace for convenience

    namespace = get_default_namespace()

    shell = eval(expr, namespace)
    if not isinstance(shell, NixShell):
        raise ValueError("Expression did not evaluate to a NixShell instance")

    return shell


def cmd_env(shell: NixShell) -> None:
    """Print shell commands to activate the Nix environment, inspired by nix-direnv."""
    # Get the dev environment
    dev_env = shell.dev_env

    # Load the shell script template
    script_path = Path(__file__).parent / "activate.sh"
    template = script_path.read_text()

    # Replace the placeholder with the actual dev environment
    activation_script = template.replace("%NIX_DEV_ENV%", dev_env)

    print(activation_script)


def cmd_activate(shell: NixShell) -> None:
    """Spawn an interactive shell with the Nix environment activated."""
    import os
    import subprocess

    # Get the dev environment
    dev_env = shell.dev_env

    # Load the shell script template
    script_path = Path(__file__).parent / "activate.sh"
    template = script_path.read_text()

    # Replace the placeholder with the actual dev environment
    activation_script = template.replace("%NIX_DEV_ENV%", dev_env)

    # Detect the current shell
    current_shell = os.environ.get("SHELL", "/bin/bash")

    # Create a temporary script that sources the activation and starts an interactive shell
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        f.write(f"""#!/usr/bin/env bash
# Temporary activation script for py-nix-shell
{activation_script}

# Start an interactive shell
exec {current_shell}
""")
        temp_script = f.name

    try:
        # Make the script executable
        os.chmod(temp_script, 0o755)

        # Run the script in interactive mode
        subprocess.run([temp_script], check=False)
    finally:
        # Clean up the temporary script
        os.unlink(temp_script)


def cmd_shell(shell: NixShell) -> None:
    """Run 'nix shell' with the shell's parameters."""
    from nix_shell import cli

    logger = logging.getLogger("py-nix-shell")

    try:
        cli.shell(**shell.params)
    except KeyboardInterrupt:
        logger.info("Exiting nix shell...")
    except Exception as e:
        logger.error(f"Error running nix shell: {e}")
        sys.exit(1)


def cmd_develop(shell: NixShell) -> None:
    """Run 'nix develop' with the shell's parameters."""
    from nix_shell import cli

    logger = logging.getLogger("py-nix-shell")

    try:
        cli.develop(**shell.params)
    except KeyboardInterrupt:
        logger.info("Exiting nix develop...")
    except Exception as e:
        logger.error(f"Error running nix develop: {e}")
        sys.exit(1)


def cmd_build(shell: NixShell) -> None:
    """Run 'nix build' with the shell's parameters."""
    from nix_shell import cli

    logger = logging.getLogger("py-nix-shell")

    try:
        result = cli.build(**shell.params)
        if result:
            print(result, end="")  # cli.build might return output
    except KeyboardInterrupt:
        logger.info("Build cancelled")
    except Exception as e:
        logger.error(f"Error running nix build: {e}")
        sys.exit(1)


def cmd_print_dev_env(shell: NixShell) -> None:
    """Print the bash instructions needed to activate a dev env."""
    dev_env = shell.dev_env
    print(dev_env)


def cmd_show(shell: NixShell) -> None:
    """Print the Nix expression being evaluated."""
    from nix_shell.utils import format_nix

    if "expr" in shell.params:
        print(format_nix(shell.params["expr"]))
    else:
        # For file-based or flake-based shells, we need to show what would be built
        logger = logging.getLogger("py-nix-shell")
        if "ref" in shell.params:
            print(f"# Flake reference: {shell.params['ref']}")
        elif "file" in shell.params:
            print(f"# File: {shell.params['file']}")
            if shell.params.get("installable"):
                print(f"# Installable: {shell.params['installable']}")
        else:
            logger.warning("Unable to determine Nix expression source")


def main():
    """py-nix-shell CLI entry point."""
    # Parse args first to get verbosity level
    # We'll set up logging after parsing arguments

    parser = argparse.ArgumentParser(
        prog="pynix",
        description="py-nix-shell manages Nix shell environments on your behalf. https://github.com/chadac/py-nix-shell",
        formatter_class=ColoredHelpFormatter,
        add_help=False,  # We'll handle help manually
    )

    parser.add_argument(
        "command",
        nargs="?",
        default="env",
        choices=[
            "activate",
            "env",
            "print-dev-env",
            "shell",
            "develop",
            "build",
            "show",
        ],
        help="Command to run (default: env)",
    )

    parser.add_argument(
        "-c",
        "--command",
        dest="expression",
        help="Evaluates a given Python expression to build the Nix shell.",
    )

    parser.add_argument(
        "--command-from-stdin",
        action="store_true",
        help="Evaluates a given Python expression from stdin and activates the environment.",
    )

    parser.add_argument(
        "-f",
        dest="file",
        type=Path,
        help="Evaluates a file besides `shell.py` to build the Nix shell.",
    )

    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        help="Show this help message and exit",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v for INFO, -vv for DEBUG, -vvv for all subprocess output)",
    )

    args = parser.parse_args()

    # Set up logging based on verbosity level
    if args.verbose == 0:
        log_level = logging.WARNING  # Only warnings and errors by default
    elif args.verbose == 1:
        log_level = logging.INFO  # -v: INFO level
    elif args.verbose == 2:
        log_level = logging.DEBUG  # -vv: DEBUG level
    else:  # args.verbose >= 3
        log_level = logging.DEBUG  # -vvv: DEBUG level + subprocess output
        # For -vvv, we'll also enable subprocess stdout/stderr capture

    logger = setup_logging(log_level)

    # Handle help manually to use our custom formatter
    if args.help:
        formatter = ColoredHelpFormatter(prog="pynix")
        print(formatter.format_help())
        sys.exit(0)

    try:
        # Determine shell source
        if args.expression:
            logger.info(f"Using expression: {args.expression}")
            shell = load_shell_from_expression(args.expression)
        elif args.command_from_stdin:
            logger.info("Reading expression from stdin")
            expression = sys.stdin.read().strip()
            shell = load_shell_from_expression(expression)
        elif args.file:
            logger.info(f"Using shell file: {args.file}")
            shell = load_shell_from_file(args.file)
        else:
            # Default to shell.py in current directory
            shell_file = Path("shell.py")
            logger.info(f"Using default shell file: {shell_file}")
            shell = load_shell_from_file(shell_file)

        # Execute the requested command
        logger.info(f"Executing command: {args.command}")
        if args.command == "activate":
            cmd_activate(shell)
        elif args.command == "env":
            cmd_env(shell)
        elif args.command == "shell":
            cmd_shell(shell)
        elif args.command == "develop":
            cmd_develop(shell)
        elif args.command == "build":
            cmd_build(shell)
        elif args.command == "print-dev-env":
            cmd_print_dev_env(shell)
        elif args.command == "show":
            cmd_show(shell)
        else:
            parser.error(f"Unknown command: {args.command}")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except NixError as e:
        logger.error(str(e))
        # Debug info is already logged by NixError.__init__
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
