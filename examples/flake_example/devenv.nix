# Example devenv.nix file for testing
{
  packages = [ ];
  
  enterShell = ''
    echo "Hello from devenv.nix!"
  '';
}