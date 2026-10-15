import unittest

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.blocks import md_ul
from draftjs_exporter.markdown.lists import (
    md_get_block_index,
    md_get_li_indent,
    md_get_li_number,
    md_get_li_suffix,
    md_make_list_item,
    md_make_numbered_li_prefix,
)
from draftjs_exporter.types import Block


class TestGetBlockIndex(unittest.TestCase):
    def test_get_block_index(self):
        self.assertEqual(
            md_get_block_index(
                [{"key": "a"}, {"key": "b"}, {"key": "c"}],
                "b",
            ),
            1,
        )

    def test_get_block_index_not_found(self):
        self.assertEqual(
            md_get_block_index(
                [{"key": "a"}, {"key": "b"}, {"key": "c"}],
                "h",
            ),
            -1,
        )


class TestGetLiSuffix(unittest.TestCase):
    def test_get_li_suffix(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            md_get_li_suffix(
                {
                    "block": b,
                    "blocks": [b, dict(b, **{"key": "b"})],
                }
            ),
            "\n",
        )

    def test_get_li_suffix_end(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            md_get_li_suffix(
                {
                    "block": b,
                    "blocks": [
                        dict(b, **{"key": "b"}),
                        b,
                        dict(b, **{"key": "c", "type": "unstyled"}),
                    ],
                }
            ),
            "\n\n",
        )

    def test_get_li_suffix_no_key(self):
        b = {
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            md_get_li_suffix(
                {
                    "block": b,
                    "blocks": [b, dict(b)],
                }
            ),
            "\n",
        )

    def test_get_li_suffix_unknown_key(self):
        # A key that isn't in blocks must not resolve to another block: that
        # would end or continue the list based on an unrelated block's type.
        b = {"key": "a", "type": "ordered-list-item", "depth": 0}
        other = {"key": "b", "type": "unordered-list-item", "depth": 0}
        self.assertEqual(
            md_get_li_suffix({"block": b, "blocks": [other]}),
            "\n\n",
        )

    def test_get_li_suffix_next_block_without_type(self):
        # A following block with no type is not a list item, so the list ends.
        b = {"key": "a", "type": "ordered-list-item", "depth": 0}
        other = {"key": "b", "text": "x", "depth": 0}
        self.assertEqual(
            md_get_li_suffix({"block": b, "blocks": [b, other]}),
            "\n\n",
        )


class TestMakeNumberedLiPrefix(unittest.TestCase):
    def test_paren_delimiter(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        get_prefix = md_make_numbered_li_prefix(")")
        self.assertEqual(
            get_prefix(
                {
                    "block": b,
                    "blocks": [b, dict(b, **{"key": "b"})],
                }
            ),
            "1) ",
        )

    def test_paren_delimiter_second_item(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        get_prefix = md_make_numbered_li_prefix(")")
        self.assertEqual(
            get_prefix(
                {
                    "block": b,
                    "blocks": [dict(b, **{"key": "b"}), b],
                }
            ),
            "2) ",
        )

    def test_paren_delimiter_resets_after_different_type(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        get_prefix = md_make_numbered_li_prefix(")")
        self.assertEqual(
            get_prefix(
                {
                    "block": b,
                    "blocks": [
                        dict(b, **{"key": "b"}),
                        dict(b, **{"key": "c", "type": "unstyled"}),
                        b,
                    ],
                }
            ),
            "1) ",
        )

    def test_paren_delimiter_resets_after_shallower_depth(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 1,
        }
        get_prefix = md_make_numbered_li_prefix(")")
        self.assertEqual(
            get_prefix(
                {
                    "block": b,
                    "blocks": [
                        dict(b, **{"key": "b", "depth": 1}),
                        dict(b, **{"key": "c", "depth": 0}),
                        b,
                    ],
                }
            ),
            "1) ",
        )

    def test_paren_delimiter_skips_deeper_preceding_block(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        get_prefix = md_make_numbered_li_prefix(")")
        self.assertEqual(
            get_prefix(
                {
                    "block": b,
                    "blocks": [
                        dict(b, **{"key": "b"}),
                        dict(b, **{"key": "c", "depth": 1}),
                        b,
                    ],
                }
            ),
            "2) ",
        )

    def test_paren_delimiter_key_not_found(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        get_prefix = md_make_numbered_li_prefix(")")
        self.assertEqual(
            get_prefix(
                {
                    "block": b,
                    "blocks": [dict(b, **{"key": "b"})],
                }
            ),
            "2) ",
        )

    def test_paren_delimiter_no_key(self):
        b = {
            "type": "ordered-list-item",
            "depth": 0,
        }
        get_prefix = md_make_numbered_li_prefix(")")
        self.assertEqual(
            get_prefix(
                {
                    "block": b,
                    "blocks": [b],
                }
            ),
            " ",
        )


class TestListItem(unittest.TestCase):
    def test_list_item(self):
        component = md_make_list_item("-", ".")
        b = {"key": "a", "type": "unordered-list-item", "depth": 0}
        self.assertEqual(
            DOM.render(
                component(
                    {
                        "block": b,
                        "blocks": [b],
                        "children": "test",
                    }
                )
            ),
            "- test\n\n",
        )

    def test_list_item_with_empty_key_renders_children_only(self):
        # An empty key is unusable, and the helpers treat it like a missing
        # one, so it must not produce a list item either.
        component = md_make_list_item("-", ".")
        self.assertEqual(
            DOM.render(
                component(
                    {
                        "block": {
                            "key": "",
                            "type": "unordered-list-item",
                            "depth": 1,
                        },
                        "blocks": [],
                        "children": "x",
                    }
                )
            ),
            "x",
        )

    def test_synthetic_block_renders_children_only(self):
        # The exporter renders an intermediate wrapper node as an element
        # with no key; it must not produce a phantom empty list item.
        component = md_make_list_item("-", ".")
        self.assertEqual(
            DOM.render(
                component(
                    {
                        "block": {"type": "unordered-list-item", "depth": 1},
                        "blocks": [],
                        "children": "x",
                    }
                )
            ),
            "x",
        )

    def test_list_item_marker_uses_mark_safe(self):
        item = md_ul(
            {
                "block": {"key": "a", "type": "unordered-list-item", "depth": 0},
                "blocks": [],
                "children": "x",
            }
        )
        types = [c.type if hasattr(c, "type") else c for c in item.children]
        self.assertEqual(types, ["mark_safe", "mark_safe", "x", "mark_safe"])
        # children ("x") sits between the prefix and suffix md_mark_safe nodes
        self.assertEqual(item.children[2], "x")


class TestLiNumber(unittest.TestCase):
    def _block(self, key: str, type_: str, depth: int = 0) -> Block:
        return {"key": key, "type": type_, "depth": depth}

    def test_first_item(self):
        b = self._block("a", "ordered-list-item")
        self.assertEqual(md_get_li_number({"block": b, "blocks": [b]}), 1)

    def test_second_item(self):
        a = self._block("a", "ordered-list-item")
        b = self._block("b", "ordered-list-item")
        self.assertEqual(md_get_li_number({"block": b, "blocks": [a, b]}), 2)

    def test_continues_after_nested_list_of_other_type(self):
        a = self._block("a", "ordered-list-item")
        one = self._block("one", "ordered-list-item")
        nested = self._block("n", "unordered-list-item", 1)
        two = self._block("two", "ordered-list-item")
        self.assertEqual(
            md_get_li_number({"block": two, "blocks": [a, one, nested, two]}), 3
        )

    def test_restarts_after_list_of_other_type_at_same_depth(self):
        b = self._block("b", "ordered-list-item")
        other = self._block("o", "unordered-list-item")
        c = self._block("c", "ordered-list-item")
        self.assertEqual(md_get_li_number({"block": c, "blocks": [b, other, c]}), 1)

    def test_no_key(self):
        b = {"type": "ordered-list-item", "depth": 0}
        self.assertEqual(md_get_li_number({"block": b, "blocks": [b]}), 1)

    def test_block_without_type_stops_the_scan(self):
        # A block with no type is not a list item: it ends the scan like any
        # other block outside the list, rather than raising.
        a = {"key": "a", "text": "x", "depth": 0}
        b = self._block("b", "ordered-list-item")
        self.assertEqual(md_get_li_number({"block": b, "blocks": [a, b]}), 1)


class TestLiIndent(unittest.TestCase):
    def _block(self, key: str, type_: str, depth: int = 0) -> Block:
        return {"key": key, "type": type_, "depth": depth}

    def test_top_level(self):
        b = self._block("a", "unordered-list-item")
        self.assertEqual(md_get_li_indent({"block": b, "blocks": [b]}, "-", "."), "")

    def test_under_unordered_parent(self):
        a = self._block("a", "unordered-list-item")
        b = self._block("b", "unordered-list-item", 1)
        self.assertEqual(
            md_get_li_indent({"block": b, "blocks": [a, b]}, "-", "."), "  "
        )

    def test_under_ordered_parent_uses_content_column(self):
        a = self._block("a", "ordered-list-item")
        b = self._block("b", "ordered-list-item", 1)
        self.assertEqual(
            md_get_li_indent({"block": b, "blocks": [a, b]}, "-", "."), "   "
        )

    def test_under_multi_digit_ordered_parent(self):
        blocks = [self._block(str(i), "ordered-list-item") for i in range(1, 10)]
        ten = self._block("ten", "ordered-list-item")
        nested = self._block("n", "unordered-list-item", 1)
        blocks += [ten, nested]
        self.assertEqual(
            md_get_li_indent({"block": nested, "blocks": blocks}, "-", "."), "    "
        )

    def test_two_levels(self):
        a = self._block("a", "unordered-list-item")
        b = self._block("b", "unordered-list-item", 1)
        c = self._block("c", "unordered-list-item", 2)
        self.assertEqual(
            md_get_li_indent({"block": c, "blocks": [a, b, c]}, "-", "."), "    "
        )

    def test_unknown_key_falls_back_to_two_spaces_per_level(self):
        b = self._block("missing", "unordered-list-item", 2)
        self.assertEqual(
            md_get_li_indent(
                {"block": b, "blocks": [self._block("a", "unordered-list-item")]},
                "-",
                ".",
            ),
            "    ",
        )


class TestLiSuffixContinuesList(unittest.TestCase):
    def _block(self, key: str, type_: str, depth: int = 0) -> Block:
        return {"key": key, "type": type_, "depth": depth}

    def test_nested_list_continues_parent_list(self):
        a = self._block("a", "unordered-list-item")
        x = self._block("x", "ordered-list-item", 1)
        self.assertEqual(
            md_get_li_suffix({"block": a, "blocks": [a, x]}),
            "\n",
        )

    def test_blank_line_ends_list(self):
        a = self._block("a", "unordered-list-item")
        p = self._block("p", "unstyled")
        self.assertEqual(
            md_get_li_suffix({"block": a, "blocks": [a, p]}),
            "\n\n",
        )
