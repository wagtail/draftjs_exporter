import unittest

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.blocks import (
    list_wrapper,
    make_ol,
    make_ul,
    ol,
    prefixed_block,
    ul,
)


class TestBlocks(unittest.TestCase):
    def test_prefixed_block(self):
        self.assertEqual(
            DOM.render(prefixed_block("> ")({"children": "test"})), "> test\n\n"
        )

    def test_prefixed_block_uses_mark_safe(self):
        elt = prefixed_block("# ")({"children": "x"})
        self.assertEqual(elt.children[0].type, "mark_safe")

    def test_prefixed_block_block_prefix_flag(self):
        elt = prefixed_block("> ", block_prefix=True)({"children": "x"})
        self.assertEqual(elt.children[0].attr["block_prefix"], "true")

    def test_ul(self):
        self.assertEqual(
            DOM.render(
                ul(
                    {
                        "block": {
                            "depth": 0,
                        },
                        "children": "test",
                    }
                )
            ),
            "- test\n",
        )

    def test_ol(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            DOM.render(
                ol(
                    {
                        "block": b,
                        "blocks": [b],
                        "children": "test",
                    }
                )
            ),
            "1. test\n\n",
        )

    def test_ol_numbering(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            DOM.render(
                ol(
                    {
                        "block": b,
                        "blocks": [
                            dict(b, **{"key": "b"}),
                            b,
                        ],
                        "children": "test",
                    }
                )
            ),
            "2. test\n\n",
        )

    def test_make_ul_star(self):
        self.assertEqual(
            DOM.render(
                make_ul("*")(
                    {
                        "block": {"depth": 0},
                        "children": "test",
                    }
                )
            ),
            "* test\n",
        )

    def test_make_ul_plus(self):
        self.assertEqual(
            DOM.render(
                make_ul("+")(
                    {
                        "block": {"depth": 0},
                        "children": "test",
                    }
                )
            ),
            "+ test\n",
        )

    def test_make_ol_paren(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            DOM.render(
                make_ol(")")(
                    {
                        "block": b,
                        "blocks": [b],
                        "children": "test",
                    }
                )
            ),
            "1) test\n\n",
        )

    def test_make_ol_dot(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            DOM.render(
                make_ol(".")(
                    {
                        "block": b,
                        "blocks": [
                            dict(b, **{"key": "b"}),
                            b,
                        ],
                        "children": "test",
                    }
                )
            ),
            "2. test\n\n",
        )

    def test_list_wrapper(self):
        self.assertEqual(DOM.render(list_wrapper({})), "")
