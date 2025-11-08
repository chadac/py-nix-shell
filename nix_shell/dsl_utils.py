"""DSL utilities for working with Nix expressions."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from nix_shell import cli, dsl
from nix_shell.flake import FlakeRefLock
from nix_shell.nix_context import NixContext, get_nix_context
from nix_shell.utils import find_shared_root


def import_flake(locked: FlakeRefLock) -> dsl.NixExpr:
    """Import a flake from its locked reference."""
    return (dsl.builtins["fetchTree"], locked)


def import_nixpkgs(locked: FlakeRefLock, system: str | None = None) -> dsl.NixExpr:
    """Import nixpkgs from its locked reference for the given system."""
    nix_system = system or cli.current_system()
    return dsl.let(
        tree=(dsl.builtins["fetchTree"], locked),
        nixpkgs=dsl.v("tree")["outPath"],
        in_=(dsl.raw("import"), dsl.v("nixpkgs"), {"system": nix_system}),
    )


@dataclass
class FileSet:
    """A set of files that can be built into a Nix store path."""

    paths: dict[Path, dsl.StorePath]

    @classmethod
    def union(cls, paths: list[Path]):
        """Create a FileSet from a list of file paths with a common root."""
        root = find_shared_root(paths)
        result = {}
        for src_path in paths:
            dest_path = src_path.relative_to(root)
            result[dest_path] = dsl.StorePath.from_path(src_path)
        return cls(result)

    @classmethod
    def virtual(cls, paths: dict[Path | str, str]):
        """Create a FileSet from virtual files with specified content."""
        result = {}
        for dest_path, content in paths.items():
            result[Path(dest_path)] = dsl.StorePath.from_string(content)
        return cls(result)

    def mk_expr(self, ctx: NixContext) -> dsl.NixExpr:
        """Generate a Nix expression that creates a directory with these files."""
        cmds = []
        mk_dirs = set([])
        for dest_path, nix_file in self.paths.items():
            parent = dest_path.parent

            # if the parent dir doesn't exist yet, make it
            if parent != dest_path and parent not in mk_dirs:
                cmds += [f"mkdir -p $out/{parent}"]
                mk_dirs.add(parent)

            cmds += [f"ln -s {ctx[nix_file]} $out/{dest_path}"]

        return ctx["pkgs"]["runCommand"]("src", {}, "\n".join(cmds))


def virtual_filesystem(
    paths: dict[Path, Path],
    name: str = "virtual-filesystem",
    ctx: Optional[NixContext] = None,
) -> dsl.NixExpr:
    """
    Create a virtual filesystem in the Nix store using cat with here-documents.

    This function creates a derivation that writes files to specific paths using
    the content from source files. It follows the pattern from call-flake-pattern.nix
    where files are written using `cat <<EOF` instead of symlinks.

    Args:
        paths: Dictionary mapping source Path objects to destination Path objects
               (relative paths within the virtual filesystem)
        name: Name for the derivation (default: "virtual-filesystem")
        ctx: NixContext to use (defaults to current global context)

    Returns:
        NixExpr that evaluates to a store path containing the virtual filesystem

    Example:
        >>> paths = {
        ...     Path("flake.nix"): Path("flake.nix"),
        ...     Path("flake.lock"): Path("flake.lock"),
        ... }
        >>> expr = virtual_filesystem(paths, name="my-flake")
    """
    ctx = ctx or get_nix_context()

    # Add source paths to the context and get their variables
    file_vars = {}
    for src_path in paths.keys():
        if not src_path.is_absolute():
            src_path = src_path.resolve()
        file_vars[src_path] = ctx.path(src_path)

    # Build the shell script with cat commands
    shell_script_lines = []

    # Create necessary directories first
    dirs_created = set()
    for dest_path in paths.values():
        parent = dest_path.parent
        if parent != Path(".") and parent not in dirs_created:
            shell_script_lines.append(f"mkdir -p $out/{parent}")
            dirs_created.add(parent)

    # Write each file using cat with here-document
    for src_path, dest_path in paths.items():
        var = file_vars[src_path]
        # Use cat with here-document to write file contents
        # The 'NIX_EOF' delimiter is quoted to prevent variable expansion
        shell_script_lines.append(f"cat <<'NIX_EOF' > $out/{dest_path}")
        shell_script_lines.append(f"${{{var.value}}}")
        shell_script_lines.append("NIX_EOF")

    shell_script = "\n".join(shell_script_lines)

    # Create the derivation using runCommand
    return dsl.call(
        ctx["pkgs"]["runCommand"],
        name,
        {},
        shell_script,
    )
