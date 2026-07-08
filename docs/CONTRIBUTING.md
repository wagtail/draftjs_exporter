# Contribution Guidelines

Thank you for considering to help this project.

We welcome all support, whether on bug reports, code, design, reviews, tests, documentation, and more. Check out the [project roadmap](ROADMAP.md) for high-level ideas that align with the project's goals.

Please note that this project is released with a [Contributor Code of Conduct](https://wagtail.org/code-of-conduct/). By participating in this project you agree to abide by its terms.

## Project architecture

Understanding the high-level architecture will help you navigate the codebase and find where to make changes.

### Module organization

```ba
draftjs_exporter/
    html.py              # Entry point. HTML class orchestrates the full rendering pipeline.
    dom.py               # Virtual DOM abstraction. Static facade over interchangeable engines.
    command.py           # Command model – operations derived from Draft.js ranges.
    entity_state.py      # Entity (link, image, embed) rendering state machine.
    style_state.py       # Inline style (bold, italic) nesting state machine.
    wrapper_state.py     # Block wrapper nesting (e.g. <ul>/<ol> around <li>).
    options.py           # Configuration normalization – converts user config to internal format.
    composite_decorators.py  # Regex-based text decorators (line breaks, mentions, linkify).
    constants.py         # BLOCK_TYPES, ENTITY_TYPES, INLINE_STYLES enums.
    defaults.py          # Default BLOCK_MAP and STYLE_MAP for HTML.
    types.py             # Type aliases and TypedDicts for the public API.
    error.py             # Exception base classes.
    engines/
        base.py          # DOMEngine abstract base class.
        string.py        # String-concatenation engine (fast, no dependencies, default).
        string_compat.py # Backward-compatible variant of the string engine.
        html5lib.py      # BeautifulSoup / html5lib engine.
        lxml.py          # lxml engine.
        markdown.py      # Non-escaping string engine for Markdown output.
    markdown/            # Markdown-specific components, config builder, and helpers.
    utils/
        module_loading.py  # import_string() for dotted-path class resolution.
```

Tests mirror this structure under `tests/`, with sub-packages for `engines/`, `markdown/`, and `utils/`.

### Rendering pipeline

The core flow lives in `HTML.render()` and proceeds as follows:

1. **Engine setup** – `DOM.engine()` resolves the engine string to a class (via `import_string`), caches it, and sets it in a thread-safe `ContextVar`.
2. **Option normalisation** – `Options.map_blocks()`, `Options.map_styles()`, `Options.map_entities()` convert the user-friendly config maps into flat `OptionsMap` dicts of type → normalized `Options` objects.
3. **Block iteration** – `HTML.render()` creates a `WrapperState` instance and an empty document fragment, then iterates over each block.
4. **Per-block rendering** – For each block, `render_block()` extracts text, inline styles, entity ranges, and composite decorators. It builds a sorted list of `Command` objects from the Draft.js ranges, groups consecutive commands by character offset, and processes each group through:
   - **EntityState** – manages an entity stack; on `start_entity`/`stop_entity` pairs it wraps children in entity components.
   - **StyleState** – tracks active inline styles; `render_styles()` wraps text in nested inline elements from innermost to outermost.
   - **Composite decorators** – regex-based text transformations (e.g. `\n` → `<br>`).
5. **Wrapper resolution** – `wrapper_state.element_for()` resolves each block to a DOM element, managing nesting of wrapper elements (e.g. `<ul>`/`<ol>` for list items) based on block depth.
6. **Final rendering** – All block elements are appended to the document fragment, then `DOM.render()` serialises the virtual DOM tree to the output string (HTML or Markdown).

### Engine system

The exporter uses a **Strategy pattern** for output generation. All engines implement the `DOMEngine` interface (five static methods: `create_tag`, `parse_html`, `append_child`, `render`, `render_debug`). The `DOM` class delegates to the active engine, selected at runtime via dotted-path strings stored as class constants (`DOM.STRING`, `DOM.HTML5LIB`, `DOM.LXML`, `DOM.MARKDOWN`, `DOM.STRING_COMPAT`). Engine selection is thread-safe through a `ContextVar`.

Engines share the same interface and general behavior, but **are not guaranteed to produce byte-identical output** for the same input. Each engine delegates serialization to a different underlying library (or none, for `string`), so real, accepted differences exist.

### Key design patterns

- **Strategy** – swappable engines, selected at runtime.
- **Facade** – `DOM` class hides engine-specific details.
- **State machine** – `EntityState` tracks entity open/close via a stack.
- **Command pattern** – operations on text are modelled as `Command` objects, sorted, grouped, and applied in order.
- **Pipeline** – text passes through decorators → inline styles → entity wrapping → wrapper nesting, each stage wrapping the previous.
- **Null object** – `WrapperStack.head()` returns a default `Wrapper(-1)` when the stack is empty.
- **Slots for performance** – core classes use `__slots__` to reduce memory overhead.

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

We aim for 100% test coverage on all changes. Tests are run with `pytest` and configured in `pyproject.toml`.

### Test organization

Tests mirror the source layout:

- `tests/test_<module>.py` – unit tests for each module under `draftjs_exporter/`.
- `tests/engines/test_engines_*.py` – engine-specific unit tests.
- `tests/markdown/test_*.py` – markdown-specific unit tests (auto-switch to the MARKDOWN engine via `conftest.py`).
- `tests/utils/test_*.py` – utility tests.

### Types of tests

The project has a layered test suite to increase the opportunities to catch bugs.

- **Unit tests** – individual classes and functions in isolation (most test files). Use `unittest.TestCase` style with `setUp`/`tearDown`.
- **Integration tests** – `test_output.py` exercises the full pipeline end-to-end with complex content states (49 KB, 1284 lines).
- **Data-driven / snapshot tests** – `test_exports.py` reads `test_exports.json` at module load time via a custom metaclass (`ExportsTestMeta`) and dynamically generates test methods for every engine × test case combination. Add a new test case to `test_exports.json` when you want to verify output across all engines.
- **Engine difference tests** – `test_engines_differences.py` compares outputs between engines to catch regressions.
- **Property-based tests** – `test_properties.py` generates many `ContentState` inputs and checks invariants that should hold for any input, rather than asserting on hand-picked examples. See [Property-based tests](#property-based-tests) below.

### Writing tests

- Add unit tests alongside the module you are changing, following the existing patterns.
- Add cross-engine test cases to `test_exports.json` when adding or modifying output behavior. Each test case needs a `label`, a `content_state`, and expected `output` for all five engines.
- All output changes should be covered with unit tests, and integration tests, and snapshot tests.

### Property-based tests

The rendering pipeline's core logic – merging overlapping `inlineStyleRanges`/`entityRanges` into ordered commands (`HTML.build_commands`/`build_command_groups`), and nesting blocks into wrappers by depth (`WrapperState`) – is an interval/tree algorithm, exactly the kind of code where example-based tests miss offset and overlap combinations nobody thought to write down. Property-based tests with [Hypothesis](https://hypothesis.readthedocs.io/) complements the example-based tests above by generating many `ContentState` inputs and checking invariants that should hold for any of them.

- **Where things live** – `tests/strategies.py` has the shared Hypothesis strategies (`content_states()`, `blocks()`, `style_ranges()`, `entity_ranges()`); `tests/test_properties.py` has the properties themselves, grouped by what they check.
- **What we check today**:
  - **Crash safety** – `HTML.render()` must not raise on any structurally valid `ContentState`, across all five engines. `ContentState` is often deserialized from a rich text editor or a database, so the exporter should degrade gracefully rather than crash on generated edge cases (empty text, zero-length ranges, unicode, deep nesting).
  - **Algorithm invariants** – `HTML.build_command_groups` must never drop or duplicate a character of block text, checked directly against the command-grouping output rather than through rendered HTML, so a failure points at the algorithm instead of at engine-specific serialization.
- **Realistic input, not adversarial fuzzing** – strategies are scoped to input a Draft.js editor could plausibly produce, not arbitrary bytes. For example, entity ranges are generated non-overlapping (in Draft.js's model, each character belongs to at most one entity), and control characters/lone surrogates are excluded from generated text. When a generated case doesn't reflect realistic input, narrow the strategy rather than special-casing the exporter to tolerate it.
- **When Hypothesis finds a failing example**, it shrinks it to a minimal reproduction and prints it in the test failure. First decide whether it represents realistic input:
  - If it's a real bug on realistic input, fix the exporter and pin the shrunk example as a permanent regression with `@example(...)` directly above the relevant `@given`, so it always runs even if Hypothesis's random search wouldn't stumble on it again.
  - If it's unrealistic input a Draft.js editor could never produce, narrow the generating strategy in `tests/strategies.py` instead of loosening the exporter's behavior, and add a comment explaining the constraint (see the entity-range non-overlap note in `strategies.py` for an example).
- **Local vs. CI example counts** – `tests/conftest.py` registers Hypothesis settings profiles. Locally, tests run with the `default` profile (100 examples per property, fast for `just test-watch`). CI sets `HYPOTHESIS_PROFILE=ci` (500 examples) for a more thorough search on every push. Run more examples locally when hunting a rare failure: `HYPOTHESIS_PROFILE=ci just test`, or temporarily add `@settings(max_examples=5000)` to a specific test.
- **The `.hypothesis/` example database** (git-ignored) caches failing examples locally between runs. Don't rely on it for permanent regressions across machines/CI – pin real bugs with an explicit `@example(...)` in source instead, so they're visible in code review and always run everywhere.
- **Where not to reach for property-based tests** – configuration/mapping modules (`options.py`, `defaults.py`) are static and already checked exhaustively by type checkers; property tests add little there. Keep property-based tests scoped to the render pipeline (`html.py`, `command.py`, `entity_state.py`, `style_state.py`, `wrapper_state.py`) and the engines.

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
