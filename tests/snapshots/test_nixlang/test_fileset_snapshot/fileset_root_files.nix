(nixpkgs.runCommand "src" {  } ''
  mkdir -p $out/.
  ln -s /nix/store/abc123-pkg/file1 $out/file1
  ln -s /nix/store/def456-pkg/file2 $out/file2
'')