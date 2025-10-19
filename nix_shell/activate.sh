#!/usr/bin/env bash

# Nix environment activation (inspired by nix-direnv)
# To activate: eval "$(py-nix-shell env)"

# Save important variables that shouldn't be overwritten
__SAVED_NIX_BUILD_TOP="${NIX_BUILD_TOP:-__UNSET__}"
__SAVED_TMP="${TMP:-__UNSET__}"
__SAVED_TMPDIR="${TMPDIR:-__UNSET__}"
__SAVED_TEMP="${TEMP:-__UNSET__}"
__SAVED_TEMPDIR="${TEMPDIR:-__UNSET__}"
__SAVED_terminfo="${terminfo:-__UNSET__}"
__SAVED_shell="${SHELL:-__UNSET__}"
__old_xdg_data_dirs="${XDG_DATA_DIRS:-}"

# Source the nix dev environment
# This will be replaced with the actual dev environment output
%NIX_DEV_ENV%

# Clean up temporary directory if it exists
if [[ -n "${NIX_BUILD_TOP+x}" && $NIX_BUILD_TOP == */nix-shell.* && -d $NIX_BUILD_TOP ]]; then
  rm -rf "$NIX_BUILD_TOP"
fi

# Restore important variables
_restore_var() {
  local var="$1" value="$2"
  if [[ $value == "__UNSET__" ]]; then
    unset "$var"
  else
    export "$var"="$value"
  fi
}

_restore_var "NIX_BUILD_TOP" "$__SAVED_NIX_BUILD_TOP"
_restore_var "TMP" "$__SAVED_TMP"
_restore_var "TMPDIR" "$__SAVED_TMPDIR"
_restore_var "TEMP" "$__SAVED_TEMP"
_restore_var "TEMPDIR" "$__SAVED_TEMPDIR"
_restore_var "SHELL" "$__SAVED_SHELL"
_restore_var "terminfo" "$__SAVED_terminfo"

# Handle XDG_DATA_DIRS specially - merge old and new
__new_xdg_data_dirs="${XDG_DATA_DIRS:-}"
export XDG_DATA_DIRS=""
IFS=':'
for dir in $__new_xdg_data_dirs${__old_xdg_data_dirs:+:}$__old_xdg_data_dirs; do
  dir="${dir%/}" # remove trailing slashes
  if [[ ":$XDG_DATA_DIRS:" == *":$dir:"* ]]; then
    continue # already present, skip
  fi
  XDG_DATA_DIRS="$XDG_DATA_DIRS${XDG_DATA_DIRS:+:}$dir"
done

# Clean up temporary variables
unset __SAVED_NIX_BUILD_TOP __SAVED_TMP __SAVED_TMPDIR __SAVED_TEMP __SAVED_TEMPDIR __SAVED_terminfo
unset __old_xdg_data_dirs __new_xdg_data_dirs
