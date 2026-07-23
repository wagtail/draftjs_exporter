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


class TestBlockquotes(unittest.TestCase):
    def test_single_line_quote(self):
        cs = parse("> quoted")
        self.assertEqual(block_types(cs), ["blockquote"])
        self.assertEqual(cs["blocks"][0]["text"], "quoted")

    def test_multiline_quote_joins(self):
        cs = parse("> a\n> b")
        self.assertEqual(len(cs["blocks"]), 1)
        self.assertEqual(cs["blocks"][0]["text"], "a\nb")

    def test_empty_quote_line_splits_blocks(self):
        cs = parse("> a\n>\n> b")
        self.assertEqual(block_types(cs), ["blockquote", "blockquote"])

    def test_quote_content_is_inline_parsed(self):
        cs = parse("> **bold**")
        self.assertEqual(cs["blocks"][0]["text"], "bold")
        self.assertEqual(
            cs["blocks"][0]["inlineStyleRanges"],
            [{"offset": 0, "length": 4, "style": "BOLD"}],
        )

    def test_quote_without_space(self):
        cs = parse(">quoted")
        self.assertEqual(cs["blocks"][0]["text"], "quoted")


class TestFencedCode(unittest.TestCase):
    def test_backtick_fence(self):
        cs = parse("```\ncode line\n```")
        self.assertEqual(block_types(cs), ["code-block"])
        self.assertEqual(cs["blocks"][0]["text"], "code line")

    def test_tilde_fence(self):
        cs = parse("~~~\ncode\n~~~")
        self.assertEqual(block_types(cs), ["code-block"])

    def test_info_string_ignored(self):
        cs = parse("```python\nx = 1\n```")
        self.assertEqual(cs["blocks"][0]["text"], "x = 1")

    def test_multiline_code(self):
        cs = parse("```\na\nb\n```")
        self.assertEqual(cs["blocks"][0]["text"], "a\nb")

    def test_unclosed_fence_parses_to_eof(self):
        cs = parse("```\ncode")
        self.assertEqual(block_types(cs), ["code-block"])
        self.assertEqual(cs["blocks"][0]["text"], "code")

    def test_code_content_not_inline_parsed(self):
        cs = parse("```\n**not bold**\n```")
        self.assertEqual(cs["blocks"][0]["text"], "**not bold**")
        self.assertEqual(cs["blocks"][0]["inlineStyleRanges"], [])

    def test_closing_fence_must_match_marker(self):
        cs = parse("```\na\n~~~\nb\n```")
        self.assertEqual(cs["blocks"][0]["text"], "a\n~~~\nb")


class TestLists(unittest.TestCase):
    def test_unordered_flat(self):
        cs = parse("- a\n- b")
        self.assertEqual(
            block_types(cs), ["unordered-list-item", "unordered-list-item"]
        )
        self.assertEqual([b["depth"] for b in cs["blocks"]], [0, 0])

    def test_ordered_flat(self):
        cs = parse("1. a\n2. b")
        self.assertEqual(block_types(cs), ["ordered-list-item"] * 2)

    def test_ordered_with_paren_delimiter(self):
        cs = parse("1) a")
        self.assertEqual(block_types(cs), ["ordered-list-item"])

    def test_all_bullet_markers(self):
        for marker in "*+-":
            cs = parse(f"{marker} item")
            self.assertEqual(block_types(cs), ["unordered-list-item"])

    def test_nested_unordered(self):
        cs = parse("- a\n  - b\n    - c")
        self.assertEqual([b["depth"] for b in cs["blocks"]], [0, 1, 2])

    def test_nested_then_back_to_top(self):
        cs = parse("- a\n  - b\n- c")
        self.assertEqual([b["depth"] for b in cs["blocks"]], [0, 1, 0])

    def test_mixed_kinds_by_indent(self):
        cs = parse("- a\n  1. b")
        self.assertEqual(
            block_types(cs), ["unordered-list-item", "ordered-list-item"]
        )
        self.assertEqual(cs["blocks"][1]["depth"], 1)

    def test_list_content_is_inline_parsed(self):
        cs = parse("- **bold**")
        self.assertEqual(cs["blocks"][0]["text"], "bold")

    def test_blank_line_ends_list(self):
        cs = parse("- a\n\nparagraph")
        self.assertEqual(block_types(cs), ["unordered-list-item", "unstyled"])

    def test_paragraph_after_list_without_blank_line(self):
        cs = parse("- a\nparagraph")
        self.assertEqual(block_types(cs), ["unordered-list-item", "unstyled"])

    def test_list_between_paragraphs(self):
        cs = parse("intro\n\n- item\n\noutro")
        self.assertEqual(
            block_types(cs), ["unstyled", "unordered-list-item", "unstyled"]
        )
