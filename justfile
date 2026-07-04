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
  fnm use
  npm install

# Lint the project.
lint:
  uv run ruff check
  uv run ruff format --check
  uv run mypy draftjs_exporter tests
  uv run ty check

# Format project files.
format:
  uv run ruff check --fix
  uv run ruff format
  npm run format

# Test the project.
test:
  PYTHONDEVMODE=1 uv run pytest -W error --capture=no

# Restarts the tests whenever a file changes.
test-watch:
  PYTHONDEVMODE=1 nodemon -q -e py -w tests -w draftjs_exporter -x "clear && just test || true"

# Run the tests while generating test coverage data.
test-coverage:
  PYTHONDEVMODE=1 uv run pytest -W error --cov --cov-report=term --cov-report=html --capture=no

# Compatibility-focused test suite.
test-compatibility:
  uv run --isolated --python 3.10 --with 'beautifulsoup4==4.7.1, html5lib==1.1, lxml==4.6.5' pytest

# Restarts the example whenever a file changes.
dev:
  nodemon -q -e py -w tests -w draftjs_exporter -w example.py -x "clear && python -X dev -W error example.py || true"

# Runs a one-off performance (speed, memory) benchmark.
benchmark runs="1":
  uv run benchmark.py --runs {{runs}}
  uv run python -m memray summary benchmark.bin
  uv run python -m memray stats benchmark.bin

# Builds package for publication.
build:
  rm -f dist/*
  uv build

# Publishes a new version to PyPI.
publish: build
  uv publish
