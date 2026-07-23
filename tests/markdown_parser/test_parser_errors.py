"""Tests for MarkdownParseError surfaces in the inline parser."""

import unittest

from draftjs_exporter.error import MarkdownParseError
from draftjs_exporter.markdown_parser.builder import ContentStateBuilder
from tests.markdown_parser.test_inline import make_parser


class TestResolverErrors(unittest.TestCase):
    def test_raising_resolver_wrapped(self):
        def bad(url, label):
            raise RuntimeError("boom")

        parser = make_parser(builder=ContentStateBuilder(), link_resolvers=[bad])
        with self.assertRaises(MarkdownParseError) as ctx:
            parser.parse("[a](/b)")
        self.assertIn("boom", str(ctx.exception))

    def test_resolution_without_type_rejected(self):
        parser = make_parser(
            builder=ContentStateBuilder(),
            link_resolvers=[lambda url, label: {"data": {}}],
        )
        with self.assertRaises(MarkdownParseError):
            parser.parse("[a](/b)")

    def test_resolution_with_non_dict_data_rejected(self):
        parser = make_parser(
            builder=ContentStateBuilder(),
            link_resolvers=[lambda url, label: {"type": "LINK", "data": "nope"}],
        )
        with self.assertRaises(MarkdownParseError):
            parser.parse("[a](/b)")


class TestLineNumbers(unittest.TestCase):
    def test_resolver_error_gets_line_number(self):
        from draftjs_exporter.markdown_parser import MarkdownParser

        def bad(url, label):
            raise RuntimeError("boom")

        parser = MarkdownParser({"link_resolvers": [bad]})
        with self.assertRaises(MarkdownParseError) as ctx:
            parser.parse("first\n\nsecond [a](/b)")
        self.assertEqual(ctx.exception.line, 3)
