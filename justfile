# checks files for lint issues
lint *files: (ruff-check files) (ruff-format-check files) (mypy files)
# formats files
format *files: (ruff-format files) (ruff-check-fix files)
# formats and then runs linters
check *files: (format files) (lint files)

# runs `ruff check`
ruff-check *args:
  uv run -- ruff check {{args}}
# runs `ruff check --fix`
ruff-check-fix *args: (ruff-check "--fix" "--select" "I" args) (ruff-check "--fix" "--select" "F401" args)

# runs `ruff format`
ruff-format *args:
  uv run -- ruff format {{args}}
# runs `ruff format --check`
ruff-format-check *args: (ruff-format "--check" args)

# runs mypy
mypy *args:
  uv run -- mypy {{args}}

# run unit tests
test *args:
  uv run -- pytest {{args}}

# update all snapshots
snapshot-update *args: (test "--snapshot-update" args)

# build and deploy docs
docs: docs-build docs-deploy

# build docs
docs-build:
  mkdocs build

# serve docs locally
docs-serve:
  mkdocs serve -w nix_shell -w docs

# deploy docs
docs-deploy:
  mkdocs gh-deploy
