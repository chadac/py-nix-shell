lint *files: (ruff-check files) (ruff-format-check files) (mypy files)
format *files: (ruff-format files) (ruff-check-fix files)

ruff-check *args:
  uv run -- ruff check {{args}}
ruff-check-fix *args: (ruff-check "--fix" "--select" "I" args) (ruff-check "--fix" "--select" "F401" args)

ruff-format *args:
  uv run -- ruff format {{args}}
ruff-format-check *args: (ruff-format "--check" args)

mypy *args:
  uv run -- mypy {{args}}

test *args:
  uv run -- pytest {{args}}
