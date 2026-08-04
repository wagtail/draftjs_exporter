"""Integration tests for Markdown escaping at the exporter level."""

import unittest
from typing import Any

from draftjs_exporter.html import HTML
from draftjs_exporter.markdown import CONFIG as MARKDOWN_CONFIG
from draftjs_exporter.types import (
    Block,
    ContentState,
    EntityMap,
    EntityRange,
    InlineStyleRange,
)


def content_state(
    text: str,
    type_: str = "unstyled",
    depth: int = 0,
    inline_style_ranges: list[InlineStyleRange] | None = None,
    entity_ranges: list[EntityRange] | None = None,
    entity_map: EntityMap | None = None,
) -> ContentState:
    """Build a single-block ContentState for testing."""
    return blocks_state(
        [
            make_block(
                text,
                key="a",
                type_=type_,
                depth=depth,
                inline_style_ranges=inline_style_ranges,
                entity_ranges=entity_ranges,
            )
        ],
        entity_map=entity_map,
    )


def make_block(
    text: str,
    key: str,
    type_: str = "unstyled",
    depth: int = 0,
    inline_style_ranges: list[InlineStyleRange] | None = None,
    entity_ranges: list[EntityRange] | None = None,
) -> Block:
    """Build a single ContentState block for testing."""
    return {
        "key": key,
        "text": text,
        "type": type_,
        "depth": depth,
        "inlineStyleRanges": inline_style_ranges or [],
        "entityRanges": entity_ranges or [],
    }


def blocks_state(
    blocks: list[Block], entity_map: EntityMap | None = None
) -> ContentState:
    """Build a multi-block ContentState for testing."""
    return {
        "entityMap": entity_map or {},
        "blocks": blocks,
    }


class TestMarkdownEscaping(unittest.TestCase):
    def setUp(self):
        self.exporter = HTML(MARKDOWN_CONFIG)

    def render(self, *args: Any, **kwargs: Any) -> str:
        return self.exporter.render(content_state(*args, **kwargs))

    def test_heading_like_text(self):
        self.assertEqual(self.render("# Not a heading"), "\\# Not a heading\n\n")

    def test_unordered_list_like_text(self):
        self.assertEqual(self.render("- not an item"), "\\- not an item\n\n")

    def test_ordered_list_like_text(self):
        self.assertEqual(self.render("1. not an item"), "1\\. not an item\n\n")

    def test_blockquote_like_text(self):
        self.assertEqual(self.render("> not a quote"), "\\> not a quote\n\n")

    def test_thematic_break_like_text(self):
        self.assertEqual(self.render("---"), "\\---\n\n")

    def test_inline_html(self):
        self.assertEqual(
            self.render("<script>alert(1)</script>"),
            "\\<script>alert(1)\\</script>\n\n",
        )

    def test_entity_reference(self):
        self.assertEqual(self.render("&copy;"), "\\&copy;\n\n")

    def test_link_syntax_in_prose(self):
        self.assertEqual(
            self.render("[click](javascript:alert(1))"),
            "\\[click\\](javascript:alert(1))\n\n",
        )

    def test_mid_line_hash_not_escaped(self):
        self.assertEqual(self.render("a # b"), "a # b\n\n")

    def test_soft_break_line_start(self):
        self.assertEqual(self.render("a\n# b"), "a\n\\# b\n\n")

    def test_line_start_in_list_item(self):
        self.assertEqual(
            self.render("# x", type_="unordered-list-item"),
            "- \\# x\n\n",
        )

    def test_line_start_in_blockquote(self):
        self.assertEqual(
            self.render("# x", type_="blockquote"),
            "> \\# x\n\n",
        )

    def test_hash_in_heading_not_escaped(self):
        # ATX heading content cannot start a nested block: no escape needed.
        self.assertEqual(
            self.render("#tag", type_="header-one"),
            "# #tag\n\n",
        )

    def test_code_block_not_escaped(self):
        self.assertEqual(
            self.render("# <x> & [y]", type_="code-block"),
            "```\n# <x> & [y]\n```\n\n",
        )

    def test_code_block_fence_breakout_impossible(self):
        self.assertEqual(
            self.render("```", type_="code-block"),
            "````\n```\n````\n\n",
        )

    def test_multi_line_code_block_shares_one_wrapper(self):
        self.assertEqual(
            self.exporter.render(
                blocks_state(
                    [
                        make_block("foo", key="a", type_="code-block"),
                        make_block("bar", key="b", type_="code-block"),
                    ]
                )
            ),
            "```\nfoo\nbar\n```\n\n",
        )

    def test_inline_code_not_escaped(self):
        self.assertEqual(
            self.render(
                "x a*b y",
                inline_style_ranges=[{"offset": 2, "length": 3, "style": "CODE"}],
            ),
            "x `a*b` y\n\n",
        )

    def test_inline_code_backtick_sizing(self):
        self.assertEqual(
            self.render(
                "x a`b y",
                inline_style_ranges=[{"offset": 2, "length": 3, "style": "CODE"}],
            ),
            "x ``a`b`` y\n\n",
        )

    def test_link_url_parenthesis_escaped(self):
        self.assertEqual(
            self.render(
                "click",
                entity_ranges=[{"offset": 0, "length": 5, "key": 0}],
                entity_map={
                    "0": {
                        "type": "LINK",
                        "mutability": "MUTABLE",
                        "data": {"url": "https://example.com/a(b)"},
                    }
                },
            ),
            "[click](https://example.com/a\\(b\\))\n\n",
        )

    def test_link_text_escaped(self):
        self.assertEqual(
            self.render(
                "a&b",
                entity_ranges=[{"offset": 0, "length": 3, "key": 0}],
                entity_map={
                    "0": {
                        "type": "LINK",
                        "mutability": "MUTABLE",
                        "data": {"url": "https://example.com/"},
                    }
                },
            ),
            "[a\\&b](https://example.com/)\n\n",
        )

    def test_image_alt_bracket_escaped(self):
        # Images live in atomic blocks in Draft.js; atomic renders children
        # only, so the image's own block spacing is the whole output.
        self.assertEqual(
            self.render(
                " ",
                type_="atomic",
                entity_ranges=[{"offset": 0, "length": 1, "key": 0}],
                entity_map={
                    "0": {
                        "type": "IMAGE",
                        "mutability": "IMMUTABLE",
                        "data": {"src": "x.png", "alt": "a]b"},
                    }
                },
            ),
            "![a\\]b](x.png)\n\n",
        )


if __name__ == "__main__":
    unittest.main()
