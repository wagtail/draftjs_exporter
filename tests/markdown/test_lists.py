import unittest

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.blocks import md_ul
from draftjs_exporter.markdown.lists import (
    md_get_block_index,
    md_get_li_suffix,
    md_get_numbered_li_prefix,
    md_list_item,
    md_make_numbered_li_prefix,
)


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


class TestGetNumberedLiPrefix(unittest.TestCase):
    def test_first(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            md_get_numbered_li_prefix(
                {
                    "block": b,
                    "blocks": [b, dict(b, **{"key": "b"})],
                }
            ),
            "1. ",
        )

    def test_last(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            md_get_numbered_li_prefix(
                {
                    "block": b,
                    "blocks": [dict(b, **{"key": "b"}), b],
                }
            ),
            "2. ",
        )

    def test_multiple_lists(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            md_get_numbered_li_prefix(
                {
                    "block": b,
                    "blocks": [
                        dict(b, **{"key": "b"}),
                        dict(b, **{"key": "d"}),
                        dict(b, **{"key": "c", "type": "unstyled"}),
                        b,
                        dict(b, **{"key": "e"}),
                    ],
                }
            ),
            "1. ",
        )

    def test_nested_blocks(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            md_get_numbered_li_prefix(
                {
                    "block": b,
                    "blocks": [
                        dict(b, **{"key": "b"}),
                        dict(b, **{"key": "d"}),
                        dict(b, **{"key": "c", "type": "unstyled"}),
                        dict(b, **{"key": "e"}),
                        dict(b, **{"key": "f", "depth": 1}),
                        b,
                        dict(b, **{"key": "g"}),
                    ],
                }
            ),
            "2. ",
        )

    def test_nested_blocks_complex(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            md_get_numbered_li_prefix(
                {
                    "block": dict(b, **{"depth": 2}),
                    "blocks": [
                        dict(b, **{"key": "b"}),
                        dict(b, **{"key": "d"}),
                        dict(b, **{"key": "c", "type": "unstyled"}),
                        dict(b, **{"key": "e"}),
                        dict(b, **{"key": "f", "depth": 1}),
                        dict(b, **{"depth": 2}),
                        dict(b, **{"key": "g"}),
                    ],
                }
            ),
            "1. ",
        )

    def test_no_key(self):
        b = {
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            md_get_numbered_li_prefix(
                {
                    "block": b,
                    "blocks": [b],
                }
            ),
            " ",
        )

    def test_wrong_key(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            md_get_numbered_li_prefix(
                {
                    "block": b,
                    "blocks": [dict(b, **{"key": "b"})],
                }
            ),
            "2. ",
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
        self.assertEqual(
            DOM.render(
                md_list_item(
                    "- ",
                    {
                        "block": {"depth": 0},
                        "blocks": [],
                        "children": "test",
                    },
                )
            ),
            "- test\n",
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

    def test_list_item_depth(self):
        self.assertEqual(
            DOM.render(
                md_list_item(
                    "- ",
                    {
                        "block": {"depth": 2},
                        "children": "test",
                    },
                )
            ),
            "    - test\n",
        )
