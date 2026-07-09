# Agent guidelines

> For the human-readable contributor guide, see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). This file is a concise quick-reference for the AI assistant.

## Project structure & module organization

Source code lives in `draftjs_exporter/`. Tests are in `tests/`. Contributor and user docs are in `docs/`. Type-checking stubs live in `stubs/`. The root also contains `example.py` and `benchmark.py` for local runs and performance checks.

See [docs/CONTRIBUTING.md#project-architecture](docs/CONTRIBUTING.md#project-architecture) for the full architecture walkthrough.

## Development commands

See [docs/CONTRIBUTING.md#commands](docs/CONTRIBUTING.md#commands) for the full list. Key recipes:

- `just init` – install dependencies
- `just lint` – lint + type-check
- `just format` – auto-format
- `just test *args` – run tests (strict mode) over project or a specific file (like `just test tests/test_dom.py`)
- `just test-coverage *args` – run with coverage

## Project tools

- `uv` for dependency management
- `ruff` for linting and formatting
- `mypy` for type checking
- `ty` for additional type checking (experimental)
- `uv` for package publication
- `GitHub Actions` for continuous integration
- `pytest` for unit tests
- `hypothesis` for property-based tests

## Coding style & naming conventions

See [docs/CONTRIBUTING.md#coding-style--conventions](docs/CONTRIBUTING.md#coding-style--conventions) for the full guide. Quick points:

- Python uses 4-space indentation, [PEP 8](https://peps.python.org/pep-0008/) style, enforced with `ruff`.
- Type annotations required on production code (checked by mypy, ty). Test code is exempt.
- Formatting: `ruff format` for Python, `prettier` for all other files.
- Test modules follow `test_*.py`, with test functions named `test_*`, test classes `Test*`.
- Core classes must use `__slots__`.
- **Docstrings are required for all public modules, classes, methods, and functions.** Use Google-style sections (`Parameters:`, `Returns:`, `Raises:`, `Yields:`, `Examples:`) and place type information in annotations, not docstrings.
- Document attributes and type aliases with a docstring directly below the assignment.
- See [docs/CONTRIBUTING.md#documentation-and-docstrings](docs/CONTRIBUTING.md#documentation-and-docstrings) for the full guide.
- For prose documentation (README, MkDocs pages), follow the [documentation style guide](docs/style-guide.md): tone, terminology, headings, linking, and British English spelling.

## Testing guidelines

See [docs/CONTRIBUTING.md#testing](docs/CONTRIBUTING.md#testing) for the full guide. Quick points:

- Target of 100% test coverage for all improvements.
- Write tests at the unit level, integration level (`test_output.py`), and snapshot level (`test_exports.json`).
- Add or update test cases in `test_exports.json` when output behavior changes across engines.
- `tests/test_properties.py` (strategies in `tests/strategies.py`) checks Hypothesis-generated properties: crash safety and command-grouping invariants. See [docs/CONTRIBUTING.md#property-based-tests](docs/CONTRIBUTING.md#property-based-tests) for the full guide on where / when to use this approach.

## Commit & pull request guidelines

See [docs/CONTRIBUTING.md#pull-request-workflow](docs/CONTRIBUTING.md#pull-request-workflow). Quick points:

- Be concise and to the point. Explain rationales that aren't obvious.
- No Title Case usage ever. Always use Sentence case.
- Recent commit messages use short, capitalized, imperative summaries (e.g., "Enforce additional mypy check").
- PRs should include a clear description, relevant test evidence (command + result), links to any related issues.
