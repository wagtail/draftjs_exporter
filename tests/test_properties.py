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

from draftjs_exporter import (
    BLOCK_MAP,
    BLOCK_TYPES,
    DOM,
    ENTITY_TYPES,
    HTML,
    INLINE_STYLES,
    MARKDOWN_CONFIG,
    STYLE_MAP,
    ContentStateFilter,
    ExporterConfig,
    MarkdownImporter,
    md_escape_text,
)
from tests.strategies import (
    content_states,
    dangerous_content_states,
    escapable_text,
    linked_styled_content_states,
    long_list_content_states,
    nested_list_content_states,
    roundtrip_content_states,
    sparse_content_states,
)
from tests.test_entities import link

CONFIG: ExporterConfig = {
    "entity_decorators": {ENTITY_TYPES.LINK: link},
    "block_map": BLOCK_MAP,
    "style_map": STYLE_MAP,
}

# The HTML-producing engines (Markdown renders a different output format,
# with its own config, and is checked separately below).
HTML_ENGINES = [DOM.STRING, DOM.STRING_COMPAT, DOM.LXML, DOM.HTML5LIB]


class TestContentStateContract(unittest.TestCase):
    """Rendering tolerates blocks with the optional keys missing.

    Per the ContentState contract (docs/contributing/architecture.md), a block
    only has to be a mapping: every other key falls back to a default, and the
    text still reaches the output.
    """

    @given(content_state=sparse_content_states())
    @settings(deadline=None)
    # Regression: a blockquote followed by a block with no `type` raised
    # KeyError from the look-up of the following block's type.
    @example(
        content_state={
            "entityMap": {},
            "blocks": [
                {
                    "key": "aaaaa",
                    "text": "",
                    "type": BLOCK_TYPES.BLOCKQUOTE,
                    "depth": 0,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                },
                {
                    "key": "bbbbb",
                    "text": "",
                    "depth": 0,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                },
            ],
        }
    )
    def test_missing_optional_keys_render(self, content_state):
        expected = "".join(block.get("text", "") for block in content_state["blocks"])
        for engine in HTML_ENGINES:
            html = HTML({**CONFIG, "engine": engine}).render(content_state)
            self.assertEqual(BeautifulSoup(html, "html5lib").get_text(), expected)
        # Markdown has its own defaults and fallbacks; the contract promises
        # crash safety rather than identical output.
        HTML(MARKDOWN_CONFIG).render(content_state)


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


class TestRenderContentInvariants(unittest.TestCase):
    """Block text must survive rendering, whatever the block depths are.

    Blocks are nested into wrapper elements by depth (see `WrapperState`).
    Depths the wrapper stack cannot nest as-is must still be rendered: a
    block at depth > 0 with no preceding parent, a block type without a
    wrapper (a list item's continuation paragraph, a heading, a blockquote),
    and a nested wrapper replacing one of another type at the same depth all
    used to be left out of the document and dropped.
    """

    @given(content_state=content_states())
    @settings(deadline=None)
    # Regression for a nested run starting above depth 0: its top-level
    # wrapper has no depth-0 block to attach to, and was dropped when the run
    # ended before the document did.
    @example(
        content_state={
            "entityMap": {},
            "blocks": [
                {
                    "key": "aaaaa",
                    "text": "a",
                    "type": BLOCK_TYPES.UNORDERED_LIST_ITEM,
                    "depth": 1,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                },
                {
                    "key": "bbbbb",
                    "text": "b",
                    "type": BLOCK_TYPES.UNSTYLED,
                    "depth": 0,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                },
            ],
        }
    )
    # Regression for a list item's continuation paragraph: a block at depth
    # > 0 whose type has no wrapper was never added to the document.
    @example(
        content_state={
            "entityMap": {},
            "blocks": [
                {
                    "key": "aaaaa",
                    "text": "item",
                    "type": BLOCK_TYPES.UNORDERED_LIST_ITEM,
                    "depth": 0,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                },
                {
                    "key": "bbbbb",
                    "text": "continuation",
                    "type": BLOCK_TYPES.UNSTYLED,
                    "depth": 1,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                },
            ],
        }
    )
    # Regression for a nested list changing type at its depth: the
    # replacement wrapper was created but never nested into its parent.
    @example(
        content_state={
            "entityMap": {},
            "blocks": [
                {
                    "key": "aaaaa",
                    "text": "a",
                    "type": BLOCK_TYPES.ORDERED_LIST_ITEM,
                    "depth": 1,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                },
                {
                    "key": "bbbbb",
                    "text": "b",
                    "type": BLOCK_TYPES.UNORDERED_LIST_ITEM,
                    "depth": 1,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                },
            ],
        }
    )
    def test_block_text_is_never_dropped(self, content_state):
        expected = "".join(block["text"] for block in content_state["blocks"])
        for engine in HTML_ENGINES:
            html = HTML({**CONFIG, "engine": engine}).render(content_state)
            self.assertEqual(BeautifulSoup(html, "html5lib").get_text(), expected)


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
        md_escape_text(text, at_line_start=True)
        md_escape_text(text, at_line_start=False)

    @given(escapable_text)
    def test_no_unescaped_angle_bracket(self, text):
        escaped = md_escape_text(text, at_line_start=True)
        self.assertIsNone(re.search(r"(?<!\\)<", escaped))

    @given(escapable_text)
    def test_escape_text_preserves_line_endings(self, text):
        # Escaping may add backslashes but never alters the line endings
        # themselves: \n, \r\n, and lone \r all survive verbatim, in order.
        endings = re.compile(r"\r\n|\r|\n")
        escaped = md_escape_text(text, at_line_start=True)
        self.assertEqual(endings.findall(escaped), endings.findall(text))

    @given(st.sampled_from("#-+>=|~").map(lambda c: c + "x"))
    def test_line_start_char_always_escaped(self, text):
        self.assertTrue(md_escape_text(text, at_line_start=True).startswith("\\"))

    @given(
        st.tuples(
            st.text(alphabet=" ", min_size=1, max_size=5),
            st.sampled_from("#-+>=|~"),
        ).map(lambda t: t[0] + t[1] + "x")
    )
    def test_line_start_char_after_spaces_always_escaped(self, text):
        escaped = md_escape_text(text, at_line_start=True)
        self.assertTrue(escaped.lstrip(" ").startswith("\\"))

    @given(st.from_regex(r"\d{1,9}[.)]x", fullmatch=True))
    def test_ordered_list_marker_always_escaped(self, text):
        m = re.match(r"(\d{1,9})([.)])", text)
        assert m is not None
        escaped = md_escape_text(text, at_line_start=True)
        self.assertTrue(escaped.startswith(f"{m.group(1)}\\{m.group(2)}"))


# A list item line as the Markdown exporter writes it: indentation, marker,
# and a space before the item's content.
_LIST_ITEM_LINE = re.compile(
    r"^(?P<indent> *)(?P<marker>[-*+]|\d{1,9}[.)]) (?P<content>.*)$"
)


def assert_list_items_indented(markdown: str) -> None:
    """Check nested list items are indented past their parent's marker.

    CommonMark nests an item inside the preceding one only when its
    indentation reaches past that item's marker, so indenting by less than the
    parent's marker width silently flattens the list into a new top-level one.
    Blank lines keep a list open; any other line closes it.
    """
    stack: list[tuple[int, int]] = []
    for line in markdown.split("\n"):
        match = _LIST_ITEM_LINE.match(line)
        if match is None:
            if line.strip():
                stack.clear()
            continue
        indent = len(match.group("indent"))
        marker_width = len(match.group("marker")) + 1
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if stack:
            assert indent >= stack[-1][1], f"{line!r} in {markdown!r}"
        stack.append((indent, marker_width))


class TestMarkdownListInvariants(unittest.TestCase):
    """Invariants of Markdown list rendering.

    The exporter anchors nested items to the content column of the item they
    are nested under, and renders nothing for the wrapper nodes it
    synthesizes when a list starts at a depth with no preceding parent (see
    wrapper_state.py). Both are checked on the rendered Markdown directly,
    independently of the importer or any engine.
    """

    @given(content_state=nested_list_content_states())
    @settings(deadline=None)
    # Regression for the wrapper node of a list starting at depth 1 with no
    # depth-0 item before it: rendering a marker for that wrapper produced a
    # phantom empty list item (``"  - \n  - b"``).
    @example(
        content_state={
            "entityMap": {},
            "blocks": [
                {
                    "key": "aaaaa",
                    "text": "a",
                    "type": BLOCK_TYPES.UNSTYLED,
                    "depth": 0,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                },
                {
                    "key": "bbbbb",
                    "text": "b",
                    "type": BLOCK_TYPES.UNORDERED_LIST_ITEM,
                    "depth": 1,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                },
            ],
        }
    )
    def test_no_empty_list_marker(self, content_state):
        # Every generated block has non-empty text, so any list marker with
        # no content after it can only come from a wrapper node.
        markdown = HTML(MARKDOWN_CONFIG).render(content_state)
        for line in markdown.split("\n"):
            match = _LIST_ITEM_LINE.match(line)
            if match is not None:
                self.assertNotEqual(match.group("content"), "", line)

    @given(content_state=long_list_content_states())
    @settings(deadline=None)
    def test_nested_items_indent_past_their_parent_marker(self, content_state):
        assert_list_items_indented(HTML(MARKDOWN_CONFIG).render(content_state))


class TestImporterProperties(unittest.TestCase):
    @given(roundtrip_content_states())
    def test_round_trip_preserves_block_types_and_text(self, content_state):
        """Export → import keeps block types and text for safe content."""
        markdown = HTML(MARKDOWN_CONFIG).render(content_state)
        result = MarkdownImporter().import_markdown(markdown)
        self.assertEqual(
            [b["type"] for b in result["blocks"]],
            [b["type"] for b in content_state["blocks"]],
        )
        self.assertEqual(
            [b["text"] for b in result["blocks"]],
            [b["text"] for b in content_state["blocks"]],
        )

    @given(content_states())
    def test_filter_produces_valid_content_state(self, content_state):
        """Filtered output never has orphaned entity ranges."""
        filter_ = ContentStateFilter(
            [{"type": "block", "match": BLOCK_TYPES.HEADER_ONE, "action": "remove"}]
        )
        result = filter_.apply(content_state)
        entity_map = result.get("entityMap", {})
        for block in result["blocks"]:
            text_length = len(block.get("text", ""))
            for r in block.get("entityRanges", []):
                self.assertIn(str(r["key"]), entity_map)
                self.assertLessEqual(r["offset"] + r["length"], text_length)
            for style_range in block.get("inlineStyleRanges", []):
                self.assertLessEqual(
                    style_range["offset"] + style_range["length"], text_length
                )

    @given(content_states())
    def test_filter_idempotent(self, content_state):
        """Applying the same filter twice yields the same result."""
        filter_ = ContentStateFilter(
            [{"type": "inline_style", "match": INLINE_STYLES.BOLD, "action": "remove"}]
        )
        once = filter_.apply(content_state)
        twice = filter_.apply(once)
        self.assertEqual(once, twice)

    @given(linked_styled_content_states())
    # Regression for splitting text at link and style boundaries: an inline
    # style left with only the whitespace a nested style had already moved
    # outside its delimiters rendered empty delimiters (``"**0000000** ****0"``),
    # which no longer imports back as the same text.
    @example(
        content_state={
            "entityMap": {},
            "blocks": [
                {
                    "key": "aaaaa",
                    "text": "0000000 0",
                    "type": BLOCK_TYPES.UNSTYLED,
                    "depth": 0,
                    "inlineStyleRanges": [
                        {"offset": 0, "length": 8, "style": INLINE_STYLES.BOLD},
                        {"offset": 7, "length": 1, "style": INLINE_STYLES.ITALIC},
                    ],
                    "entityRanges": [],
                }
            ],
        }
    )
    def test_round_trip_preserves_text_across_link_and_style_boundaries(
        self, content_state
    ):
        """Export → import keeps the text when links and inline styles overlap."""
        markdown = HTML(MARKDOWN_CONFIG).render(content_state)
        result = MarkdownImporter().import_markdown(markdown)
        self.assertEqual(
            [b["text"] for b in result["blocks"]],
            [b["text"] for b in content_state["blocks"]],
        )
