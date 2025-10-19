(
  { pkgs }:
  (pkgs.runCommand "src" { } ''
    mkdir -p $out/.
    ln -s '/nix/store/abc123-pkg/file with spaces' $out/file with spaces
    ln -s '/nix/store/def456-pkg/special$chars' $out/special$chars
  '')
)
