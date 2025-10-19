from dataclasses import field
from pathlib import Path
from typing import Callable

from nix_shell.build import NixShell
from nix_shell.constants import LOCAL_CACHE_ROOT


class NixShellManager:
    """
    Tool for managing multiple Nix shells inside a `shell.py`.

    Args:
        shell_func (Callable[..., NixShell] | list[Callable[..., NixShell]]):
            The function used to build new shells.
        root (Path): Location to store Nix shell profile configurations.
        num_stages (int): The number of stages to use for building Nix shells;
            useful if you want a minimal usable shell and then extend it to more
            packages in the background.
        use_latest (bool): If true, this will prefer the latest existing shell
            and rebuild in a separate process.
        history (int): The number of shells to preserve for faster re-activation.
    """

    shell_func: Callable[..., NixShell]

    # manager configuration
    root: Path = field(default_factory=lambda: LOCAL_CACHE_ROOT / "shells")

    # options
    num_stages: int = 1
    block_on_rebuild: bool = True
    history: int = 1

    def build(
        self,
        *args,
        daemon: bool | None = None,
        stage: int | None = None,
        **kwargs,
    ) -> NixShell:
        if daemon is None:
            daemon = self.block_on_rebuild
        # TODO: Implement shell building logic
        return NotImplemented

    def fetch_latest(self) -> NixShell | None:
        """Fetch the latest shell built. Useful for conditional flags."""
        return NotImplemented

    @property
    def only_updates_nixpkgs(self) -> bool:
        """Return true if rebuilding only updates the `nixpkgs` version."""
        return NotImplemented


def mk_manager(*args, **kwargs) -> NixShellManager:
    return NixShellManager(*args, **kwargs)
