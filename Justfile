@default:
  @just --list

# Remove dist and egg-info
@clean:
  -rm dist/*
  -rm src/marksplitz.egg-info/*

# The following commands require the virtual environment is activated:

@build: lint check test
  pyproject-build

# Run ruff format --check
@check:
  ruff format --check

# lint and check
@checks: lint check test

# Run ruff format
@format:
  ruff format

# Run ruff check
@lint:
  ruff check

# Run pytest
@test:
  pytest

# Run marksplitz.py to write help text to temp.txt
@help:
  python3 src/marksplitz/marksplitz.py -h > temp.txt
