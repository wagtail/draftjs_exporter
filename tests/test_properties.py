"""Property-based tests using Hypothesis.

These tests complement the unit, integration, and snapshot tests.
Instead of asserting on hand-picked examples, they generate many ContentState inputs (see strategies.py).
And assert invariants that should hold for *any* valid input:

- Rendering never raises on any structurally valid ContentState.
- All HTML-producing engines agree on output for the same input and configuration.
- The command-grouping algorithm in HTML.build_command_groups never drops or duplicates a character of block text.

When Hypothesis finds a failing example, it shrinks it to a minimal reproduction and prints it in the test failure.
Pin any real bug found this way as a permanent regression by adding an `@example(...)` with the shrunk input directly above the relevant `@given`,
so it always runs even if Hypothesis's random search would not stumble on it again. See CONTRIBUTING.md for the full workflow.

The `# ty: ignore[missing-argument]` markers below suppress a false positive:
ty doesn't yet model the ParamSpec signature rewrite that `@st.composite`
applies (dropping the leading `draw` parameter for callers), so it thinks
`content_states()` is missing arguments. mypy understands this correctly via
Hypothesis's type stubs.
"""

import unittest

from hypothesis import given, settings

from draftjs_exporter.constants import ENTITY_TYPES
from draftjs_exporter.defaults import BLOCK_MAP, STYLE_MAP
from draftjs_exporter.dom import DOM
from draftjs_exporter.html import HTML, ExporterConfig
from draftjs_exporter.markdown import CONFIG as MARKDOWN_CONFIG
from tests.strategies import content_states
from tests.test_entities import link

CONFIG: ExporterConfig = {
    "entity_decorators": {ENTITY_TYPES.LINK: link},
    "block_map": BLOCK_MAP,
    "style_map": STYLE_MAP,
}

# The engines that all produce comparable HTML output for the same config.
# Markdown is excluded: it renders a different output format (Markdown
# syntax, not HTML), with its own config, so it isn't expected to match.
HTML_ENGINES = [DOM.STRING, DOM.STRING_COMPAT, DOM.LXML, DOM.HTML5LIB]

# Of the HTML engines, string_compat is *intentionally* different: it exists
# specifically to preserve legacy quote-escaping and attribute-ordering
# behavior (see engines/string_compat.py). It's included in crash-safety
# checks but excluded from the strict output-equality property below.
STRICT_EQUALITY_ENGINES = [DOM.STRING, DOM.LXML, DOM.HTML5LIB]


class TestRenderCrashSafety(unittest.TestCase):
    """`HTML.render` must not raise on any structurally valid ContentState.

    ContentState is often deserialized from a rich text editor or a
    database, so the exporter should degrade gracefully (or raise a
    documented exception type) rather than crash unexpectedly, even on
    generated edge cases like empty text, zero-length ranges, or deeply
    overlapping style/entity ranges.
    """

    @given(content_state=content_states())  # ty: ignore[missing-argument]
    @settings(deadline=None)
    def test_html_engines_never_raise(self, content_state):
        # Not using self.subTest: it's incompatible with @given (each of the
        # hundreds of generated examples would be reported as a separate
        # subtest). Hypothesis's own failure report already names which
        # engine and content_state triggered the exception.
        for engine in HTML_ENGINES:
            HTML({**CONFIG, "engine": engine}).render(content_state)

    @given(content_state=content_states())  # ty: ignore[missing-argument]
    @settings(deadline=None)
    def test_markdown_engine_never_raises(self, content_state):
        exporter = HTML({**MARKDOWN_CONFIG, "engine": DOM.MARKDOWN})
        exporter.render(content_state)


class TestEngineEquivalence(unittest.TestCase):
    """All HTML-producing engines must agree on their output.

    This formalizes, as a generated property, the same concern that
    tests/engines/test_engines_differences.py checks with fixed examples:
    the engines are meant to be interchangeable (see the Strategy pattern
    described in docs/CONTRIBUTING.md#engine-system).
    """

    @given(content_state=content_states())  # ty: ignore[missing-argument]
    @settings(deadline=None)
    def test_html_engines_agree(self, content_state):
        outputs = {
            engine: HTML({**CONFIG, "engine": engine}).render(content_state)
            for engine in STRICT_EQUALITY_ENGINES
        }

        reference_engine = STRICT_EQUALITY_ENGINES[0]
        reference_output = outputs[reference_engine]

        for engine, output in outputs.items():
            self.assertEqual(
                output,
                reference_output,
                f"{engine} disagrees with {reference_engine} for {content_state!r}",
            )


class TestCommandGroupingInvariants(unittest.TestCase):
    """Invariants of HTML.build_command_groups, independent of any engine.

    This is the core range-merging algorithm (see
    docs/CONTRIBUTING.md#rendering-pipeline, step 4) that turns overlapping
    inlineStyleRanges/entityRanges into ordered, non-overlapping groups. It is
    exercised directly here (rather than only through rendered HTML) so a
    failure points straight at the algorithm instead of at engine-specific
    serialization.
    """

    def setUp(self):
        self.exporter = HTML(CONFIG)

    @given(content_state=content_states())  # ty: ignore[missing-argument]
    @settings(deadline=None)
    def test_command_groups_preserve_all_text(self, content_state):
        for block in content_state["blocks"]:
            groups = self.exporter.build_command_groups(block)
            reconstructed = "".join(text for text, _commands in groups)
            self.assertEqual(reconstructed, block["text"])
