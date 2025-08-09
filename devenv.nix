{ pkgs, lib, config, inputs, ... }:
{
  languages.python = {
    enable = true;
    package = pkgs.python313;
    uv.enable = true;
  };
}
