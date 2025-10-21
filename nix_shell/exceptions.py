from subprocess import SubprocessError
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class NeedsNix(Exception):
    """
    Error raised whenever the Nix command is missing.
    """

    def __init__(self):
        super().__init__(
            "Nix is not installed. Follow the instructions at https://nixos.org/download/ to install Nix."
        )


class NixError(Exception):
    """
    Error raised whenever a Nix command fails.
    """

    def __init__(
        self, exception: SubprocessError, params: dict, command: list[str] | None = None
    ):
        import logging

        self.original_exception = exception
        self.params = params
        self.command = command or []

        # Get logger for debugging
        logger = logging.getLogger("py-nix-shell")

        # Create human-readable error message
        if hasattr(exception, "returncode"):
            error_msg = f"Nix command failed with exit code {exception.returncode}"
        else:
            error_msg = f"Nix command failed: {type(exception).__name__}"

        # Log debug information
        logger.debug(f"Nix command failed: {' '.join(self.command)}")
        logger.debug(f"Parameters: {params}")
        logger.debug(f"Original exception: {exception}")

        # Include stderr output if available
        if hasattr(exception, "stderr") and exception.stderr:
            logger.debug(f"Stderr: {exception.stderr}")
            error_msg += f"\nStderr: {exception.stderr}"

        # Include stdout output if available
        if hasattr(exception, "stdout") and exception.stdout:
            logger.debug(f"Stdout: {exception.stdout}")

        super().__init__(error_msg)


def wrap_subprocess_error(func):
    """
    Decorator to wrap subprocess errors in NixError with proper logging.

    Usage:
        @wrap_subprocess_error
        def my_nix_command(**params):
            return subprocess.check_output(["nix", "build", ...])
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SubprocessError as e:
            # Import here to avoid circular imports
            from typing import get_type_hints

            try:
                from nix_shell.cli import NixBuildArgs

                valid_keys = set(get_type_hints(NixBuildArgs).keys())
            except ImportError:
                # Fallback if import fails
                valid_keys = {"file", "installable", "ref", "expr", "impure", "include"}

            # Extract params if they exist in kwargs
            params = {k: v for k, v in kwargs.items() if k in valid_keys}

            # Try to reconstruct the command for better debugging
            command = []
            if hasattr(e, "cmd") and e.cmd:
                command = e.cmd if isinstance(e.cmd, list) else [str(e.cmd)]

            raise NixError(e, params, command) from e

    return wrapper
