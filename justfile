# Task runner: https://github.com/casey/just
# Requires: `uv`, `npm`, and `just`.

# List all the justfile recipes.
help:
  just --list --list-prefix 'just '

# Remove Python file artifacts.
clean-pyc:
  find . -name '*.pyc' -exec rm -f {} +
  find . -name '*.pyo' -exec rm -f {} +
  find . -name '*~' -exec rm -f {} +

# Install dependencies and initialize for development.
init: clean-pyc
  uv venv
  uv sync --dev
  nvm use
  npm install

# Lint the project.
lint:
  ruff check
  ruff format --check
  mypy draftjs_exporter tests
  ty check

# Format project files.
format:
  ruff check --fix
  ruff format
  npm run format

# Test the project.
test:
  PYTHONDEVMODE=1 pytest -W error --capture=no

# Restarts the tests whenever a file changes.
test-watch:
  PYTHONDEVMODE=1 nodemon -q -e py -w tests -w draftjs_exporter -x "clear && just test || true"

# Run the tests while generating test coverage data.
test-coverage:
  PYTHONDEVMODE=1 pytest -W error --cov --cov-report=term --cov-report=html --capture=no

# Compatibility-focused test suite.
test-compatibility:
  uv run --isolated --python 3.10 --with 'beautifulsoup4==4.7.1, html5lib==1.1, lxml==4.6.5' pytest

# Restarts the example whenever a file changes.
dev:
  nodemon -q -e py -w tests -w draftjs_exporter -w example.py -x "clear && python -X dev -W error example.py || true"

# Runs a one-off performance (speed, memory) benchmark.
benchmark:
  python benchmark.py
  python -m memray summary benchmark.bin
  python -m memray stats benchmark.bin

# Builds package for publication.
build:
  rm -f dist/*
  uv build

# Publishes a new version to PyPI.
publish: build
  uv publish
