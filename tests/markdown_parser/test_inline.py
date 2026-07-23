"""Tests for inline Markdown parsing."""

import unittest

from draftjs_exporter.markdown_parser.builder import ContentStateBuilder
from draftjs_exporter.markdown_parser.inline import InlineParser


def make_parser(**overrides):
    """Build an InlineParser with all constructs enabled."""
    config = {
        "emphasis": True,
        "code_inline": True,
        "links": True,
        "images": True,
        "line_breaks": True,
        "inline_html_styles": {},
        "link_resolvers": [],
        "image_resolvers": [],
        "builder": ContentStateBuilder(),
    }
    config.update(overrides)
    return InlineParser(**config)


class TestPlainText(unittest.TestCase):
    def test_plain_text_passes_through(self):
        text, styles, entities = make_parser().parse("hello world")
        self.assertEqual(text, "hello world")
        self.assertEqual(styles, [])
        self.assertEqual(entities, [])


class TestEscapes(unittest.TestCase):
    def test_escaped_char_is_literal(self):
        text, styles, _ = make_parser().parse(r"\*not italic\*")
        self.assertEqual(text, "*not italic*")
        self.assertEqual(styles, [])

    def test_backslash_before_non_escapable_is_literal(self):
        text, _, _ = make_parser().parse(r"\a")
        self.assertEqual(text, r"\a")


class TestCodeSpans(unittest.TestCase):
    def test_code_span(self):
        text, styles, _ = make_parser().parse("a `bc` d")
        self.assertEqual(text, "a bc d")
        self.assertEqual(styles, [{"offset": 2, "length": 2, "style": "CODE"}])

    def test_code_span_contents_are_literal(self):
        text, styles, _ = make_parser().parse("`**not bold**`")
        self.assertEqual(text, "**not bold**")
        self.assertEqual(styles, [{"offset": 0, "length": 12, "style": "CODE"}])

    def test_unmatched_backtick_is_literal(self):
        text, styles, _ = make_parser().parse("a `b")
        self.assertEqual(text, "a `b")
        self.assertEqual(styles, [])

    def test_code_disabled(self):
        text, styles, _ = make_parser(code_inline=False).parse("`x`")
        self.assertEqual(text, "`x`")
        self.assertEqual(styles, [])


class TestHardBreaks(unittest.TestCase):
    def test_two_spaces_before_newline_are_stripped(self):
        text, _, _ = make_parser().parse("a  \nb")
        self.assertEqual(text, "a\nb")

    def test_soft_break_kept(self):
        text, _, _ = make_parser().parse("a\nb")
        self.assertEqual(text, "a\nb")

    def test_single_trailing_space_kept(self):
        text, _, _ = make_parser().parse("a \nb")
        self.assertEqual(text, "a \nb")
