"""Tests for the inline HTML style whitelist."""

import unittest

from tests.markdown_parser.test_inline import make_parser

SUP_SUB = {"sup": "SUPERSCRIPT", "sub": "SUBSCRIPT"}


class TestInlineHtml(unittest.TestCase):
    def test_whitelisted_tag_produces_style(self):
        text, styles, _ = make_parser(inline_html_styles=SUP_SUB).parse(
            "a <sup>2</sup> b"
        )
        self.assertEqual(text, "a 2 b")
        self.assertEqual(styles, [{"offset": 2, "length": 1, "style": "SUPERSCRIPT"}])

    def test_recursive_content(self):
        text, styles, _ = make_parser(inline_html_styles=SUP_SUB).parse(
            "<sup>**bold**</sup>"
        )
        self.assertEqual(text, "bold")
        self.assertIn({"offset": 0, "length": 4, "style": "SUPERSCRIPT"}, styles)
        self.assertIn({"offset": 0, "length": 4, "style": "BOLD"}, styles)

    def test_tag_with_attributes_is_literal(self):
        text, styles, _ = make_parser(inline_html_styles=SUP_SUB).parse(
            '<sup class="x">2</sup>'
        )
        self.assertEqual(text, '<sup class="x">2</sup>')
        self.assertEqual(styles, [])

    def test_non_whitelisted_tag_is_literal(self):
        text, styles, _ = make_parser(inline_html_styles=SUP_SUB).parse("<b>bold</b>")
        self.assertEqual(text, "<b>bold</b>")
        self.assertEqual(styles, [])

    def test_unclosed_tag_is_literal(self):
        text, styles, _ = make_parser(inline_html_styles=SUP_SUB).parse("<sup>2")
        self.assertEqual(text, "<sup>2")
        self.assertEqual(styles, [])

    def test_empty_whitelist_means_literal(self):
        text, styles, _ = make_parser().parse("<sup>2</sup>")
        self.assertEqual(text, "<sup>2</sup>")
        self.assertEqual(styles, [])


class TestNestingDepth(unittest.TestCase):
    def test_depth_guard_rejects_excessive_recursion(self):
        from draftjs_exporter.error import MarkdownParseError
        from draftjs_exporter.markdown_parser.inline import MAX_INLINE_DEPTH

        # The parser's find-first-closer semantics make deep nesting
        # unreachable from real input (mis-paired constructs fall back to
        # literal text), so the guard is exercised directly.
        parser = make_parser(inline_html_styles=SUP_SUB)
        with self.assertRaises(MarkdownParseError):
            parser._parse("x", depth=MAX_INLINE_DEPTH + 1)

    def test_moderate_nesting_still_parses(self):
        text, styles, _ = make_parser(inline_html_styles=SUP_SUB).parse(
            "<sup><sub>x</sub></sup>"
        )
        self.assertEqual(text, "x")
        self.assertEqual(len(styles), 2)
