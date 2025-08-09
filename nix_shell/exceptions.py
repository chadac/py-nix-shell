class NeedsNix(Exception):
    def __init__(self):
        super().__init__(
            "Nix is not installed. Follow the instructions at https://nixos.org/download/ to install Nix."
        )
