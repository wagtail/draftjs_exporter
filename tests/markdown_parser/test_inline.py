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


class TestEmphasis(unittest.TestCase):
    def test_italic_star(self):
        text, styles, _ = make_parser().parse("a *b* c")
        self.assertEqual(text, "a b c")
        self.assertEqual(styles, [{"offset": 2, "length": 1, "style": "ITALIC"}])

    def test_italic_underscore(self):
        text, styles, _ = make_parser().parse("_b_")
        self.assertEqual(styles, [{"offset": 0, "length": 1, "style": "ITALIC"}])

    def test_bold_stars(self):
        text, styles, _ = make_parser().parse("**bold**")
        self.assertEqual(text, "bold")
        self.assertEqual(styles, [{"offset": 0, "length": 4, "style": "BOLD"}])

    def test_bold_underscores(self):
        text, styles, _ = make_parser().parse("__bold__")
        self.assertEqual(styles, [{"offset": 0, "length": 4, "style": "BOLD"}])

    def test_bold_italic_triple(self):
        text, styles, _ = make_parser().parse("***both***")
        self.assertEqual(text, "both")
        self.assertEqual(
            styles,
            [
                {"offset": 0, "length": 4, "style": "BOLD"},
                {"offset": 0, "length": 4, "style": "ITALIC"},
            ],
        )

    def test_nested_italic_in_bold(self):
        text, styles, _ = make_parser().parse("**a *b* c**")
        self.assertEqual(text, "a b c")
        self.assertEqual(
            styles,
            [
                {"offset": 0, "length": 5, "style": "BOLD"},
                {"offset": 2, "length": 1, "style": "ITALIC"},
            ],
        )

    def test_bold_inside_italic(self):
        text, styles, _ = make_parser().parse("*a **b** c*")
        self.assertEqual(text, "a b c")
        self.assertIn({"offset": 0, "length": 5, "style": "ITALIC"}, styles)
        self.assertIn({"offset": 2, "length": 1, "style": "BOLD"}, styles)

    def test_unmatched_delimiter_is_literal(self):
        text, styles, _ = make_parser().parse("a *b")
        self.assertEqual(text, "a *b")
        self.assertEqual(styles, [])

    def test_mismatched_run_length_partially_matches(self):
        # Per CommonMark, `**a*` is a literal star followed by emphasis:
        # the second opener star pairs with the trailing star.
        text, styles, _ = make_parser().parse("**a*")
        self.assertEqual(text, "*a")
        self.assertEqual(styles, [{"offset": 1, "length": 1, "style": "ITALIC"}])

    def test_run_longer_than_three_is_literal(self):
        text, styles, _ = make_parser().parse("****a****")
        self.assertEqual(text, "****a****")
        self.assertEqual(styles, [])

    def test_offsets_after_emphasis(self):
        text, styles, _ = make_parser().parse("**b** x *i*")
        self.assertEqual(text, "b x i")
        self.assertEqual(
            styles,
            [
                {"offset": 0, "length": 1, "style": "BOLD"},
                {"offset": 4, "length": 1, "style": "ITALIC"},
            ],
        )

    def test_emphasis_disabled(self):
        text, styles, _ = make_parser(emphasis=False).parse("**a**")
        self.assertEqual(text, "**a**")
        self.assertEqual(styles, [])
