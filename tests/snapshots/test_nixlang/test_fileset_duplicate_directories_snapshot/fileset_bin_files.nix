(nixpkgs.runCommand "src" {  } ''
  mkdir -p $out/bin
  ln -s /nix/store/abc123-pkg/file1 $out/bin/file1
  ln -s /nix/store/def456-pkg/file2 $out/bin/file2
  ln -s /nix/store/ghi789-pkg/file3 $out/bin/file3
'')