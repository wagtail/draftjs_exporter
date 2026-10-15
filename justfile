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
  uv run mypy .
  uv run ty check
  uv run pyright
  uv run pyrefly check
  uv run lint-imports

# Check the type completeness of the public API. Informational: the score
# depends on how much of the API uses precise types, not on correctness.
# Exits with an error while the score is below 100%.
verify-types:
  uv run pyright --verifytypes draftjs_exporter --ignoreexternal

# Format project files.
format *paths=".":
  uv run ruff check --fix {{paths}}
  uv run ruff format {{paths}}
  npm run format -- {{paths}}

# Test the project or a specific file (like `just test tests/test_dom.py`).
test *args:
  PYTHONDEVMODE=1 uv run pytest -W error --capture=no -n auto {{args}}

# Restarts the tests whenever a file changes.
test-watch *args:
  PYTHONDEVMODE=1 nodemon -q -e py -w tests -w draftjs_exporter -x "clear && just test {{args}} || true"

# Run the tests while generating test coverage data.
test-coverage *args:
  PYTHONDEVMODE=1 uv run pytest -W error --cov --cov-report=term --cov-report=html --capture=no -n auto {{args}}

# Compatibility-focused test suite.
test-compatibility *args:
  uv run --isolated --python 3.11 --with 'beautifulsoup4==4.7.1, html5lib==1.1, lxml==4.9.4, pytest-xdist' pytest -n auto {{args}}

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
# promptfoo only resolves the Claude Agent SDK and the OpenCode SDK from the
# project's node_modules, so both are installed locally without saving it.
# `npm install` prunes them.
eval-init:
  npm install -g promptfoo
  npm install --no-save @anthropic-ai/claude-agent-sdk @opencode-ai/sdk

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

# Where the Claude eval's fixtures live: outside the repository, so that no arm
# can read the library source or the reference answers.
eval_claude_fixtures := env("XDG_CACHE_HOME", env("HOME") / ".cache") / "draftjs-exporter-eval"

# Assemble the fixture directories the Claude eval's four arms run in.
eval-claude-fixtures: docs-build
  rm -rf "{{eval_claude_fixtures}}"
  mkdir -p "{{eval_claude_fixtures}}/empty" "{{eval_claude_fixtures}}/docs"
  mkdir -p "{{eval_claude_fixtures}}/skill/.claude/skills" "{{eval_claude_fixtures}}/docs-skill/.claude/skills"
  cp site/llms.txt site/llms-full.txt "{{eval_claude_fixtures}}/docs/"
  cp site/llms.txt site/llms-full.txt "{{eval_claude_fixtures}}/docs-skill/"
  cp -r draftjs_exporter/.agents/skills/draftjs-exporter "{{eval_claude_fixtures}}/skill/.claude/skills/"
  cp -r draftjs_exporter/.agents/skills/draftjs-exporter "{{eval_claude_fixtures}}/docs-skill/.claude/skills/"

# Assemble the same four arms for the OpenCode eval, where OpenCode discovers
# skills in `.agents/skills/` rather than `.claude/skills/`.
eval-opencode-fixtures: docs-build
  rm -rf "{{eval_claude_fixtures}}-opencode"
  mkdir -p "{{eval_claude_fixtures}}-opencode/empty" "{{eval_claude_fixtures}}-opencode/docs"
  mkdir -p "{{eval_claude_fixtures}}-opencode/skill/.agents/skills" "{{eval_claude_fixtures}}-opencode/docs-skill/.agents/skills"
  cp site/llms.txt site/llms-full.txt "{{eval_claude_fixtures}}-opencode/docs/"
  cp site/llms.txt site/llms-full.txt "{{eval_claude_fixtures}}-opencode/docs-skill/"
  cp -r draftjs_exporter/.agents/skills/draftjs-exporter "{{eval_claude_fixtures}}-opencode/skill/.agents/skills/"
  cp -r draftjs_exporter/.agents/skills/draftjs-exporter "{{eval_claude_fixtures}}-opencode/docs-skill/.agents/skills/"

# Check the Claude eval's cases against the grader, without calling a model.
eval-claude-check:
  uv run python docs/prompts/graders/check_references.py

# Run the skill eval on a Claude model (like `just eval-claude claude-haiku-5-5 --repeat 3`).
eval-claude model="claude-sonnet-5-5" *args="": eval-claude-fixtures eval-claude-check
  @command -v promptfoo >/dev/null || { echo 'promptfoo not found - run `just eval-init`'; exit 1; }
  @test -d node_modules/@anthropic-ai/claude-agent-sdk || { echo 'Claude Agent SDK not found - run `just eval-init`'; exit 1; }
  EVAL_CLAUDE_MODEL="{{model}}" \
  EVAL_CLAUDE_FIXTURES="{{eval_claude_fixtures}}" \
  PROMPTFOO_PYTHON="$PWD/.venv/bin/python" \
  promptfoo eval -c docs/prompts/draftjs_exporter_skills_claude.yaml --no-cache {{args}}

# Run the skill eval on an OpenCode model (like `just eval-opencode deepseek-v4.1-flash --repeat 3`).
# `model` is a Neuralwatt model id, `key` a raw API key: use the model-specific key from
# ~/dev/.keys.yml for recorded runs, or `$NEURALWATT_API_KEY` to trial. Extra
# arguments like `--repeat 3` go after the key (`just eval-opencode m k --repeat 3`).
eval-opencode model="deepseek-v4.1-flash" key="$NEURALWATT_API_KEY" *args="": eval-opencode-fixtures eval-claude-check
  @command -v promptfoo >/dev/null || { echo 'promptfoo not found - run `just eval-init`'; exit 1; }
  @test -n "{{key}}" || { echo 'No API key given - pass one as the second argument'; exit 1; }
  @test -d node_modules/@opencode-ai/sdk || { echo 'OpenCode SDK not found - run `just eval-init`'; exit 1; }
  @case "{{key}}" in -*) echo "second argument looks like a flag, not a key - pass the key: just eval-opencode {{model}} \"\$KEY\" {{key}}"; exit 1;; esac
  EVAL_OPENCODE_MODEL="{{model}}" \
  EVAL_OPENCODE_FIXTURES="{{eval_claude_fixtures}}-opencode" \
  EVAL_OPENCODE_KEY="{{key}}" \
  PROMPTFOO_PYTHON="$PWD/.venv/bin/python" \
  promptfoo eval -c docs/prompts/draftjs_exporter_skills_opencode.yaml --no-cache {{args}}

# Open the promptfoo viewer for the most recent eval results.
eval-view:
  promptfoo view -y
