"""Tests for parser feature toggles at the block level."""

import unittest

from tests.markdown_parser.test_blocks import block_types, parse


class TestBlockToggles(unittest.TestCase):
    def test_headings_disabled(self):
        cs = parse("# Title", headings=False)
        self.assertEqual(block_types(cs), ["unstyled"])
        self.assertEqual(cs["blocks"][0]["text"], "# Title")

    def test_blockquote_disabled(self):
        cs = parse("> quote", blockquote=False)
        self.assertEqual(block_types(cs), ["unstyled"])

    def test_code_fenced_disabled(self):
        cs = parse("```\ncode\n```", code_fenced=False)
        self.assertEqual(block_types(cs), ["unstyled"])

    def test_thematic_break_disabled(self):
        cs = parse("a\n---", thematic_break=False)
        self.assertEqual(block_types(cs), ["unstyled"])
        self.assertEqual(cs["blocks"][0]["text"], "a\n---")

    def test_unordered_list_disabled(self):
        cs = parse("- item", unordered_list=False)
        self.assertEqual(block_types(cs), ["unstyled"])
        self.assertEqual(cs["blocks"][0]["text"], "- item")

    def test_ordered_list_disabled(self):
        cs = parse("1. item", ordered_list=False)
        self.assertEqual(block_types(cs), ["unstyled"])

    def test_disabled_construct_does_not_end_paragraph(self):
        cs = parse("text\n# heading", headings=False)
        self.assertEqual(len(cs["blocks"]), 1)
        self.assertEqual(cs["blocks"][0]["text"], "text\n# heading")
