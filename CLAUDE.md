# Claude Development Notes

This file contains important information for Claude when working on this codebase.

## Code Quality Checks

Always run these commands before completing tasks to ensure code quality:

- `just check` - Check and auto-format code (just lint + ruff format + ruff check --fix)
  - Prefer `just check` for all linting
  - `just lint` - Run linting checks, don't modify (ruff check + ruff format check + mypy)
- `just test` - Run the full test suite

## Testing

- Test entrypoint: `just test`
- Individual test files: `just test tests/test_filename.py`
- Uses pytest with pytest-isolate plugin
- Test files are in the `tests/` directory

## Module Naming

Recent changes:
- `_nix.py` has been renamed to `cli.py`
- All imports have been updated accordingly
- Type names: use `NixExpr` (not `NixValue`), `NixCompoundType` (not `NixType`)

## Development Workflow

1. Make code changes
2. Run `just format` to auto-format
3. Run `just lint` to check for issues
4. Run `just test` to ensure all tests pass
5. Fix any issues found by the above commands

This ensures consistent code style and catches issues early.

**Important**: Always run `just check` after making any code changes to ensure consistent formatting and linting.
