(
  { pkgs }:
  (pkgs.runCommand "src" { } ''
    mkdir -p $out/bin
    ln -s /nix/store/abc123-hello/bin/hello $out/bin/hello
    mkdir -p $out/lib
    ln -s /nix/store/abc123-hello/lib/libhello.so $out/lib/libhello.so
    mkdir -p $out/share/doc
    ln -s /nix/store/abc123-hello/share/doc/README $out/share/doc/README
  '')
)
