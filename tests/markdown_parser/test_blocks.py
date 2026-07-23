"""Tests for block-level Markdown parsing."""

import unittest
from typing import Any

from draftjs_exporter.markdown_parser.blocks import BlockParser
from draftjs_exporter.markdown_parser.builder import ContentStateBuilder
from draftjs_exporter.markdown_parser.inline import InlineParser
from draftjs_exporter.types import ContentState


def parse(markdown: str, **overrides: Any) -> ContentState:
    """Parse Markdown into a ContentState with all constructs enabled."""
    builder = ContentStateBuilder()
    inline = InlineParser(
        emphasis=True,
        code_inline=True,
        links=True,
        images=overrides.get("images", True),
        line_breaks=True,
        inline_html_styles={},
        link_resolvers=[],
        image_resolvers=[],
        builder=builder,
    )
    config: dict[str, Any] = {
        "headings": True,
        "blockquote": True,
        "code_fenced": True,
        "thematic_break": True,
        "unordered_list": True,
        "ordered_list": True,
        "images": True,
        "inline": inline,
        "builder": builder,
    }
    config.update(overrides)
    BlockParser(**config).parse(markdown)
    return builder.build()


def block_types(cs: ContentState) -> list[str]:
    """Extract the block types of a ContentState."""
    return [b.get("type", "unstyled") for b in cs.get("blocks", [])]


class TestParagraphs(unittest.TestCase):
    def test_single_paragraph(self):
        cs = parse("hello")
        self.assertEqual(block_types(cs), ["unstyled"])
        self.assertEqual(cs["blocks"][0]["text"], "hello")

    def test_blank_lines_split_paragraphs(self):
        cs = parse("a\n\nb")
        self.assertEqual(len(cs["blocks"]), 2)

    def test_soft_wrapped_lines_join_with_newline(self):
        cs = parse("a\nb")
        self.assertEqual(len(cs["blocks"]), 1)
        self.assertEqual(cs["blocks"][0]["text"], "a\nb")

    def test_empty_input_produces_no_blocks(self):
        self.assertEqual(parse("")["blocks"], [])
        self.assertEqual(parse("\n\n\n")["blocks"], [])


class TestHeadings(unittest.TestCase):
    def test_all_levels(self):
        names = ["one", "two", "three", "four", "five", "six"]
        for level in range(1, 7):
            cs = parse(f"{'#' * level} Title")
            self.assertEqual(block_types(cs), [f"header-{names[level - 1]}"])

    def test_heading_content_is_inline_parsed(self):
        cs = parse("## **Bold** title")
        block = cs["blocks"][0]
        self.assertEqual(block["text"], "Bold title")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 0, "length": 4, "style": "BOLD"}],
        )

    def test_closing_hashes_stripped(self):
        cs = parse("# Title #")
        self.assertEqual(cs["blocks"][0]["text"], "Title")

    def test_no_space_after_hash_is_paragraph(self):
        cs = parse("#notaheading")
        self.assertEqual(block_types(cs), ["unstyled"])

    def test_heading_then_paragraph(self):
        cs = parse("# T\n\ntext")
        self.assertEqual(block_types(cs), ["header-one", "unstyled"])


class TestThematicBreaks(unittest.TestCase):
    def test_dashes(self):
        cs = parse("a\n\n---\n\nb")
        self.assertEqual(block_types(cs), ["unstyled", "atomic", "unstyled"])

    def test_atomic_block_shape(self):
        cs = parse("---")
        block = cs["blocks"][0]
        self.assertEqual(block["text"], " ")
        self.assertEqual(block["entityRanges"], [{"offset": 0, "length": 1, "key": 0}])
        self.assertEqual(
            cs["entityMap"]["0"],
            {"type": "HORIZONTAL_RULE", "mutability": "IMMUTABLE", "data": {}},
        )

    def test_stars_and_underscores(self):
        self.assertEqual(block_types(parse("***")), ["atomic"])
        self.assertEqual(block_types(parse("___")), ["atomic"])

    def test_spaced_markers(self):
        self.assertEqual(block_types(parse("- - -")), ["atomic"])
