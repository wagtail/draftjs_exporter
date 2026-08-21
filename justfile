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
  prek

# Lint the project.
lint:
  uv run ruff check
  uv run ruff format --check
  uv run mypy draftjs_exporter tests
  uv run ty check

# Format project files.
format *paths=".":
  uv run ruff check --fix {{paths}}
  uv run ruff format {{paths}}
  npm run format -- {{paths}}

# Test the project or a specific file (like `just test tests/test_dom.py`).
test *args:
  PYTHONDEVMODE=1 uv run pytest -W error --capture=no {{args}}

# Restarts the tests whenever a file changes.
test-watch *args:
  PYTHONDEVMODE=1 nodemon -q -e py -w tests -w draftjs_exporter -x "clear && just test {{args}} || true"

# Run the tests while generating test coverage data.
test-coverage *args:
  PYTHONDEVMODE=1 uv run pytest -W error --cov --cov-report=term --cov-report=html --capture=no {{args}}

# Compatibility-focused test suite.
test-compatibility *args:
  uv run --isolated --python 3.10 --with 'beautifulsoup4==4.7.1, html5lib==1.1, lxml==4.6.5' pytest {{args}}

# Restarts the example whenever a file changes.
dev:
  nodemon -q -e py -w tests -w draftjs_exporter -w example.py -x "clear && python -X dev -W error example.py || true"

# Runs a one-off performance (speed, memory) benchmark.
benchmark runs="1":
  uv run benchmark.py --runs {{runs}}
  uv run python -m memray summary benchmark.bin
  uv run python -m memray stats benchmark.bin

# Build the documentation.
docs-build:
  uv run mkdocs build --strict

# Build the documentation and serve it locally.
docs-serve:
  uv run mkdocs serve --strict

# Builds package for publication.
build:
  rm -f dist/*
  uv build

# Publishes a new version to PyPI.
publish: build
  uv publish

# Install the eval tooling globally, outside of package.json (per Node version).
eval-init:
  npm install -g promptfoo @opencode-ai/sdk

# Assemble the published-docs fixture the eval's docs arms read from.
eval-docs: docs-build
  rm -rf .eval-docs
  mkdir -p .eval-docs
  cp site/llms.txt site/llms-full.txt .eval-docs/

# Run promptfoo evals for the draftjs-exporter skill. Needs `just eval-init`.
eval *args="": eval-docs
  @command -v promptfoo >/dev/null || { echo 'promptfoo not found - run `just eval-init`'; exit 1; }
  @command -v opencode >/dev/null || { echo 'opencode CLI not found - see https://opencode.ai/docs/'; exit 1; }
  OPENCODE_CONFIG="$PWD/docs/prompts/opencode.json" \
  PROMPTFOO_PYTHON="$PWD/.venv/bin/python" \
  promptfoo eval -c docs/prompts/draftjs_exporter_skills.yaml {{args}}

# Open the promptfoo viewer for the most recent eval results.
eval-view:
  promptfoo view -y
