@default:
  @just --list

# The following commands will only work if the virtual environment is activated.

@build: lint check test
  pyproject-build

# Run ruff format --check
@check:
  ruff format --check

# Remove dist and egg-info
@clean:
  -rm dist/*
  -rmdir dist
  -rm src/marksplitz.egg-info/*
  -rmdir src/marksplitz.egg-info

# Run ruff format
@format:
  ruff format

# Run ruff check
@lint:
  ruff check

# Run pytest
@test:
  pytest
