# Contribution Guidelines

Thank you for considering to help this project.

We welcome all support, whether on bug reports, code, design, reviews, tests, documentation, and more. Check out the [project roadmap](ROADMAP.md) for high-level ideas that align with the project's goals.

Please note that this project is released with a [Contributor Code of Conduct](https://wagtail.org/code-of-conduct/). By participating in this project you agree to abide by its terms.

## Project architecture

Review the [project architecture](contributing/architecture.md). Understanding the high-level architecture will help you navigate the codebase and find where to make changes.

## Development

### Installation

> Requirements: [`uv`](https://github.com/astral-sh/uv), [just](https://github.com/casey/just), [prek](https://prek.j178.dev/)

Clone the repository, configure the git hooks, then initialize with `just init`.

```sh
git clone git@github.com:wagtail/draftjs_exporter.git
cd draftjs_exporter/
# Install everything.
just init
```

### Commands

- `just help`: See what commands are available.
- `just init`: Install dependencies and initialise for development.
- `just lint`: Lint the project. Accepts optional paths to scope to, e.g. `just lint draftjs_exporter/dom.py`.
- `just format *paths="."`: Format project files.
- `just test *args`: Test the project or a specific file (like `just test tests/test_dom.py`).
- `just test-watch *args`: Restarts the tests whenever a file changes.
- `just test-coverage *args`: Run the tests while generating test coverage data.
- `just test-compatibility *args`: Compatibility-focused test suite.
- `just dev`: Restarts the example whenever a file changes.
- `just benchmark runs="1"`: Runs a one-off performance (speed, memory) benchmark. Accepts an optional number of runs, e.g. `just benchmark 5`.
- `just clean-pyc`: Remove Python file artifacts.
- `just docs-build`: Build the documentation.
- `just docs-serve`: Build the documentation and serve it locally.
- `just build`: Builds package for publication.
- `just publish`: Publishes a new version to PyPI.

### Dependencies

This project uses multiple package managers and an automated dependency bot.

**Python** – managed with [uv](https://github.com/astral-sh/uv). Runtime dependencies are optional extras only (`lxml`, `html5lib`).

**JavaScript (tooling only)** – managed with `npm`. Only `prettier` is used, for formatting non-Python files. Locked in `package-lock.json`. Install with `npm install`.

**Dependency updates** – handled by [Renovate](https://docs.renovatebot.com/):

- Runs on a bi-weekly schedule (3rd and 22nd of each month).
- PRs are labelled `dependencies`.
- A 14-day minimum release age ensures stability before updates are proposed.
- `uv.lock` is refreshed weekly (Mondays) to catch transitive dependency updates.
- GitHub Actions, npm, and most Python dependencies are auto-merged.
- `lxml`, `beautifulsoup4`, and `html5lib` are excluded from automated updates – their version bounds are intentionally conservative and must be updated manually after verifying there are no output changes.

To manually update a dependency, edit the version in `pyproject.toml` or `package.json`, then run `uv sync --dev` or `npm install` to update the lockfile. Run `just test-compatibility` to verify the project works with the lower-bound dependency versions declared for optional extras.

### Debugging

- Always run the tests. To auto-run with watch, use `npm install -g nodemon`, then `just test-watch`.
- Use a debugger. `uv pip install ipdb`, then `import ipdb; ipdb.set_trace()`.
- You can use `example.py` as a basic CLI to try out the exporter with arbitrary ContentState JSON: `echo '{"json": "contents"}' | ./example.py -`.
- Inspect the DOM tree at any stage using `DOM.render_debug()` to see the virtual DOM structure before serialisation.
- Run individual test files with `just test tests/test_dom.py`, or filter with `-k`: `just test tests/test_dom.py -k "test_create_element"`.
- Use `just dev` to restart the example automatically whenever source files change.

## Coding style & conventions

We follow [PEP 8](https://peps.python.org/pep-0008/) for Python code style, enforced automatically by `ruff`:

- **Python**: formatted with `ruff format`, linted with `ruff check`. Configuration in `pyproject.toml`.
- **Other files**: formatted with `prettier` (see `prettier.config.js`).
- **Indentation**: 4 spaces, no tabs.
- **Type annotations**: required on all production code, checked by `mypy` with strict settings and by `ty` (experimental).
- **Naming**: `snake_case` for functions, methods, and variables; `PascalCase` for classes; `UPPER_CASE` for constants. Test modules follow `test_*.py`, test functions `test_*`, test classes `Test*`.
- **Performance**: core classes should use `__slots__` to reduce memory overhead.
- **Imports**: organised automatically by `ruff` (isort rules in `pyproject.toml`).
- **Error handling**: use specific exception types; avoid bare `except:` clauses (BLE rules).
- **Comments**: avoid hard-wrapping lines, except at full stops, or other punctuation like commas if must be.

Additionally, we follow:

- [Python code best practices from Griffe](https://mkdocstrings.github.io/griffe/guide/users/recommendations/python-code/)
- [Docstrings best practices from Griffe](https://mkdocstrings.github.io/griffe/guide/users/recommendations/docstrings/)

## Documentation and docstrings

Good documentation helps users and contributors understand the exporter without reading source code. We aim for docs that are accurate, discoverable, and maintainable.

### Design goals

- **Docs as code:** user and contributor docs live in version-controlled Markdown alongside the source.
- **API docs in docstrings:** the public API is documented in docstrings so it can be extracted by tools like [Griffe](https://mkdocstrings.github.io/griffe/) and [mkdocstrings](https://mkdocstrings.github.io/) in the future.
- **Consistent style:** all docstrings follow the **Google style** with explicit sections for parameters, return values, raised exceptions, and yielded values.
- **No type duplication:** type information lives in annotations. Docstrings describe semantics, not types.

### Docstring conventions

Follow these conventions for all production code:

- **Every public module, class, method, and function** must have a docstring.
- **Module docstrings** go at the top of the file and briefly describe what the module contains and when to use it.
- **Class docstrings** explain the class’s purpose. List public attributes only when they are not obvious from type annotations.
- **Method and function docstrings** use this structure:

  ```python
  def render(self, content_state: ContentState | None = None) -> str:
      """Render Draft.js ContentState as HTML.

      Parameters:
          content_state: The raw ContentState to render. Defaults to an empty state.

      Returns:
          The rendered HTML string.

      Raises:
          ValueError: If the content state contains unsupported block depths.
      """
  ```

- **Use these sections when applicable:** `Parameters:`, `Returns:`, `Yields:`, `Receives:`, `Raises:`, `Warns:`, `Examples:`.
- **Attributes and type aliases** are documented with a docstring directly below the assignment:

  ```python
  Element: TypeAlias = Any
  """An engine-specific DOM element produced by a renderable component."""
  ```

- **Magic methods** (`__init__`, `__repr__`, etc.) are documented when they are part of the public API.
- **Exceptions:** document exception classes with a short description of when they are raised.

### Prose documentation

- User-facing docs live in `docs/`; the README is the entry point.
- Keep language concise and in **Sentence case** (no Title Case).
- Run `just format` before committing so prettier formats Markdown files consistently.

## Testing

Automated tests are crucial for the quality assurance of this project. We use a layered [testing strategy](./contributing/test-strategy.md). We aim for 100% test coverage on all changes, with coverage at multiple layers. Tests are run with `pytest` and configured in `pyproject.toml`.

## Pull request workflow

1. Create a branch from `main` with a descriptive name.
2. Make your changes, following the coding style and testing guidelines above.
3. Run `just lint` and `just test` locally to verify everything passes.
4. Open a pull request with a clear description of what the change does and why. Include relevant test evidence (commands and their output) and links to related issues.
5. CI will run linting (ruff, mypy, ty, prettier), benchmarks, test coverage, and the compatibility test suite. All checks must pass before merging.
6. Squash merge when approved. Keep the commit message concise, in the imperative mood, and using Sentence case (no Title Case).

## Releases

- Make a new branch for the release of the new version.
- Update the [CHANGELOG](https://github.com/wagtail/draftjs_exporter/CHANGELOG.md).
- Update the version number in `pyproject.toml`, following semver.
- Update the version number in `draftjs_exporter/__init__.py`, following semver.
- Make a PR and squash merge it.
- Back on main with the PR merged, use `just publish` (confirm, and enter your password).
- Finally, go to GitHub and create a release and a tag for the new version.
- Done!

> As a last step, you may want to go update the [Draftail Playground](http://playground.draftail.org/) to this new release to check that all is well in a fully separate project.

## Support guidelines

### Python versions support

- Official support for [supported Python versions](https://devguide.python.org/versions/), communicated via trove classifiers and in the README, tested in CI.
- Tentative support for upcoming Python versions, tested in CI to some degree.
- Case-by-case, unofficial undocumented support for end-of-life Python versions.

### Benchmarks

Consider [building Python for maximum performance](https://github.com/pyenv/pyenv/blob/master/plugins/python-build/README.md#building-for-maximum-performance):

```sh
env PYTHON_CONFIGURE_OPTS='--enable-optimizations --with-lto' PYTHON_CFLAGS='-march=native -mtune=native' pyenv install 3.6.0
```

### Static typing

All exporter code should pass static type checking by [mypy](https://mypy.readthedocs.io/en/latest/index.html), with as strict of a configuration as possible, and tentatively also pass type checks with the [ty](https://docs.astral.sh/ty/) checker.
