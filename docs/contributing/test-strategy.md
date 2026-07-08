# Test strategy

We aim for 100% test coverage on all changes, with coverage at multiple layers. Tests are run with `pytest` and configured in `pyproject.toml`.

## Test organization

Tests mirror the source layout:

- `tests/test_<module>.py` – unit tests for each module under `draftjs_exporter/`.
- `tests/engines/test_engines_*.py` – engine-specific unit tests.
- `tests/markdown/test_*.py` – markdown-specific unit tests (auto-switch to the MARKDOWN engine via `conftest.py`).
- `tests/utils/test_*.py` – utility tests.

## Types of tests

The project has a layered test suite to increase the opportunities to catch bugs.

- **Unit tests** – individual classes and functions in isolation (most test files). Use `unittest.TestCase` style with `setUp`/`tearDown`.
- **Integration tests** – `test_output.py` exercises the full pipeline end-to-end with complex content states (49 KB, 1284 lines).
- **Data-driven / snapshot tests** – `test_exports.py` reads `test_exports.json` at module load time via a custom metaclass (`ExportsTestMeta`) and dynamically generates test methods for every engine × test case combination. Add a new test case to `test_exports.json` when you want to verify output across all engines.
- **Engine difference tests** – `test_engines_differences.py` compares outputs between engines to catch regressions.
- **Property-based tests** – `test_properties.py` generates many `ContentState` inputs and checks invariants that should hold for any input, rather than asserting on hand-picked examples. See [Property-based tests](#property-based-tests) below.

## Writing tests

- Add unit tests alongside the module you are changing, following the existing patterns.
- Add cross-engine test cases to `test_exports.json` when adding or modifying output behavior. Each test case needs a `label`, a `content_state`, and expected `output` for all five engines.
- All output changes should be covered with unit tests, and integration tests, and snapshot tests.

## Property-based tests

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
