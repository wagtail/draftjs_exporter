"""Property-based tests using Hypothesis.

These tests complement the unit, integration, and snapshot tests.
Instead of asserting on hand-picked examples, they generate many ContentState inputs (see strategies.py).
And assert invariants that should hold for *any* valid input:

- Rendering never raises on any structurally valid ContentState.
- The command-grouping algorithm in HTML.build_command_groups never drops or duplicates a character of block text.

When Hypothesis finds a failing example, it shrinks it to a minimal reproduction and prints it in the test failure.
Pin any real bug found this way as a permanent regression by adding an `@example(...)` with the shrunk input directly above the relevant `@given`,
so it always runs even if Hypothesis's random search would not stumble on it again. See CONTRIBUTING.md for the full workflow.

The `# ty: ignore[missing-argument]` markers below suppress a false positive:
ty doesn't yet model the ParamSpec signature rewrite that `@st.composite` applies (dropping the leading `draw` parameter for callers),
so it thinks `content_states()` is missing arguments. mypy understands this via type stubs.
"""

import re
import unittest
from urllib.parse import unquote

from bs4 import BeautifulSoup
from hypothesis import example, given, settings
from hypothesis import strategies as st

from draftjs_exporter.constants import ENTITY_TYPES
from draftjs_exporter.defaults import BLOCK_MAP, STYLE_MAP
from draftjs_exporter.dom import DOM
from draftjs_exporter.html import HTML, ExporterConfig
from draftjs_exporter.markdown import CONFIG as MARKDOWN_CONFIG
from draftjs_exporter.markdown.escape import escape_text
from tests.strategies import content_states, dangerous_content_states, escapable_text
from tests.test_entities import link

CONFIG: ExporterConfig = {
    "entity_decorators": {ENTITY_TYPES.LINK: link},
    "block_map": BLOCK_MAP,
    "style_map": STYLE_MAP,
}

# The HTML-producing engines (Markdown renders a different output format,
# with its own config, and is checked separately below).
HTML_ENGINES = [DOM.STRING, DOM.STRING_COMPAT, DOM.LXML, DOM.HTML5LIB]


class TestRenderCrashSafety(unittest.TestCase):
    """`HTML.render` must not raise on any structurally valid ContentState.

    ContentState is often deserialized from a rich text editor or a
    database, so the exporter should degrade gracefully (or raise a
    documented exception type) rather than crash unexpectedly, even on
    generated edge cases like empty text, zero-length ranges, or deeply
    overlapping style/entity ranges.
    """

    @given(content_state=content_states())
    @settings(deadline=None)
    def test_html_engines_never_raise(self, content_state):
        # Not using self.subTest: it's incompatible with @given (each of the
        # hundreds of generated examples would be reported as a separate
        # subtest). Hypothesis's own failure report already names which
        # engine and content_state triggered the exception.
        for engine in HTML_ENGINES:
            HTML({**CONFIG, "engine": engine}).render(content_state)

    @given(content_state=content_states())
    @settings(deadline=None)
    # Regression for a block jumping straight to a nested depth (here a
    # list item at depth 1 with no depth-0 item before it) with no
    # preceding wrapper: WrapperState.update_stack had to synthesize an
    # intermediary wrapper node with no children, which crashed the
    # Markdown engine when the wrapper's element is a callable component
    # (e.g. Markdown's list_item) that reads `props["children"]` directly.
    @example(
        content_state={
            "entityMap": {},
            "blocks": [
                {
                    "key": "aaaaa",
                    "text": "",
                    "type": "unstyled",
                    "depth": 0,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                },
                {
                    "key": "aaaaa",
                    "text": "",
                    "type": "unordered-list-item",
                    "depth": 1,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                },
            ],
        }
    )
    def test_markdown_engine_never_raises(self, content_state):
        exporter = HTML({**MARKDOWN_CONFIG, "engine": DOM.MARKDOWN})
        exporter.render(content_state)


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

    @given(content_state=content_states())
    @settings(deadline=None)
    def test_command_groups_preserve_all_text(self, content_state):
        for block in content_state["blocks"]:
            groups = self.exporter.build_command_groups(block)
            reconstructed = "".join(text for text, _commands in groups)
            self.assertEqual(reconstructed, block["text"])


class TestRenderEscapingInvariants(unittest.TestCase):
    """Block text and entity `data` must never be interpreted as markup.

    ContentState is untrusted (see docs/SECURITY.md#tampering): block text
    and entity `data` may contain literal HTML/JS payload fragments
    (`<script>`, `"><img onerror=...>`, ...). Rendering must escape that
    syntax so a real HTML parser reading the output back never sees a new
    element or attribute that wasn't in the exporter's own markup - i.e. the
    original text/URL round-trips through the rendered HTML unchanged.

    This complements `TestRenderCrashSafety`: that suite checks rendering
    doesn't crash, this one checks its *output* stays inert. It does not,
    and cannot, check URL scheme or CSS safety (e.g. a `javascript:` href) -
    those remain the integrating application's responsibility, as documented
    in docs/SECURITY.md#recommendations-for-integrators.
    """

    @given(content_state=dangerous_content_states())
    @settings(deadline=None)
    def test_dangerous_fragments_never_become_markup(self, content_state):
        block = content_state["blocks"][0]
        text = block["text"]
        has_entity = bool(block["entityRanges"])
        entity_url = content_state["entityMap"]["0"]["data"]["url"]

        for engine in HTML_ENGINES:
            html = HTML({**CONFIG, "engine": engine}).render(content_state)
            parsed = BeautifulSoup(html, "html5lib")

            # No payload fragment was parsed back as a real element.
            self.assertEqual(parsed.find_all("script"), [])
            self.assertEqual(parsed.find_all("img"), [])
            self.assertEqual(parsed.find_all("svg"), [])

            if has_entity:
                links = parsed.find_all("a")
                self.assertEqual(len(links), 1)
                # The href attribute value round-trips: no quote or tag breakout introduced an extra attribute or element.
                # (modulo the lxml engine's own URI normalization on render, which preserves meaning and isn't a breakout).
                # Remove lxml-specific workaround once we stop supporting lxml versions below 6.0.0.
                href = unquote(links[0].get("href"))
                self.assertEqual(href, entity_url)
                self.assertEqual(set(links[0].attrs), {"href"})
                self.assertEqual(links[0].get_text(), text)
            else:
                self.assertEqual(parsed.get_text(), text)


class TestMarkdownEscapingInvariants(unittest.TestCase):
    """Invariants of Markdown escaping of user-controlled text."""

    @given(escapable_text)
    def test_escape_text_never_raises(self, text):
        escape_text(text, at_line_start=True)
        escape_text(text, at_line_start=False)

    @given(escapable_text)
    def test_no_unescaped_angle_bracket(self, text):
        escaped = escape_text(text, at_line_start=True)
        self.assertIsNone(re.search(r"(?<!\\)<", escaped))

    @given(escapable_text)
    def test_escape_text_preserves_line_endings(self, text):
        # Escaping may add backslashes but never alters the line endings
        # themselves: \n, \r\n, and lone \r all survive verbatim, in order.
        endings = re.compile(r"\r\n|\r|\n")
        escaped = escape_text(text, at_line_start=True)
        self.assertEqual(endings.findall(escaped), endings.findall(text))

    @given(st.sampled_from("#-+>=|~").map(lambda c: c + "x"))
    def test_line_start_char_always_escaped(self, text):
        self.assertTrue(escape_text(text, at_line_start=True).startswith("\\"))

    @given(
        st.tuples(
            st.text(alphabet=" ", min_size=1, max_size=5),
            st.sampled_from("#-+>=|~"),
        ).map(lambda t: t[0] + t[1] + "x")
    )
    def test_line_start_char_after_spaces_always_escaped(self, text):
        escaped = escape_text(text, at_line_start=True)
        self.assertTrue(escaped.lstrip(" ").startswith("\\"))

    @given(st.from_regex(r"\d{1,9}[.)]x", fullmatch=True))
    def test_ordered_list_marker_always_escaped(self, text):
        m = re.match(r"(\d{1,9})([.)])", text)
        assert m is not None
        escaped = escape_text(text, at_line_start=True)
        self.assertTrue(escaped.startswith(f"{m.group(1)}\\{m.group(2)}"))
