(myCustomNixpkgs.runCommand "src" {  } ''
  mkdir -p $out/.
  ln -s /nix/store/abc123-hello/bin/hello $out/hello
  ln -s /nix/store/def456-world/bin/world $out/world
'')