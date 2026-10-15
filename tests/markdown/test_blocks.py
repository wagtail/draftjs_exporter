import unittest

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.blocks import (
    md_blockquote,
    md_list_wrapper,
    md_make_ol,
    md_make_ul,
    md_ol,
    md_prefixed_block,
    md_ul,
)


class TestBlocks(unittest.TestCase):
    def test_prefixed_block(self):
        self.assertEqual(
            DOM.render(md_prefixed_block("> ")({"children": "test"})), "> test\n\n"
        )

    def test_prefixed_block_uses_mark_safe(self):
        elt = md_prefixed_block("# ")({"children": "x"})
        self.assertEqual(elt.children[0].type, "mark_safe")

    def test_prefixed_block_block_prefix_flag(self):
        elt = md_prefixed_block("> ", block_prefix=True)({"children": "x"})
        self.assertEqual(elt.children[0].attr["block_prefix"], "true")

    def test_ul(self):
        b = {"key": "a", "type": "unordered-list-item", "depth": 0}
        self.assertEqual(
            DOM.render(
                md_ul(
                    {
                        "block": b,
                        "blocks": [b],
                        "children": "test",
                    }
                )
            ),
            "- test\n\n",
        )

    def test_ol(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            DOM.render(
                md_ol(
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
                md_ol(
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
        b = {"key": "a", "type": "unordered-list-item", "depth": 0}
        self.assertEqual(
            DOM.render(
                md_make_ul("*")(
                    {
                        "block": b,
                        "blocks": [b],
                        "children": "test",
                    }
                )
            ),
            "* test\n\n",
        )

    def test_make_ul_plus(self):
        b = {"key": "a", "type": "unordered-list-item", "depth": 0}
        self.assertEqual(
            DOM.render(
                md_make_ul("+")(
                    {
                        "block": b,
                        "blocks": [b],
                        "children": "test",
                    }
                )
            ),
            "+ test\n\n",
        )

    def test_make_ol_paren(self):
        b = {
            "key": "a",
            "type": "ordered-list-item",
            "depth": 0,
        }
        self.assertEqual(
            DOM.render(
                md_make_ol(")")(
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
                md_make_ol(".")(
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
        self.assertEqual(DOM.render(md_list_wrapper({})), "")


class TestBlockquote(unittest.TestCase):
    def test_single_blockquote(self):
        b = {"key": "q", "type": "blockquote", "depth": 0}
        self.assertEqual(
            DOM.render(md_blockquote({"block": b, "blocks": [b], "children": "test"})),
            "> test\n\n",
        )

    def test_consecutive_blockquotes_share_one_quote(self):
        q1 = {"key": "q1", "type": "blockquote", "depth": 0}
        q2 = {"key": "q2", "type": "blockquote", "depth": 0}
        self.assertEqual(
            DOM.render(
                md_blockquote({"block": q1, "blocks": [q1, q2], "children": "one"})
            ),
            "> one\n>\n",
        )
        self.assertEqual(
            DOM.render(
                md_blockquote({"block": q2, "blocks": [q1, q2], "children": "two"})
            ),
            "> two\n\n",
        )

    def test_quote_followed_by_other_block_ends_quote(self):
        q = {"key": "q", "type": "blockquote", "depth": 0}
        p = {"key": "p", "type": "unstyled", "depth": 0}
        self.assertEqual(
            DOM.render(md_blockquote({"block": q, "blocks": [q, p], "children": "x"})),
            "> x\n\n",
        )

    def test_quote_without_key(self):
        # A block with no key cannot continue a quote, since there is no key
        # to look up the following block by.
        b = {"type": "blockquote", "depth": 0}
        self.assertEqual(
            DOM.render(md_blockquote({"block": b, "blocks": [b], "children": "x"})),
            "> x\n\n",
        )

    def test_quote_with_falsy_key(self):
        # A present but falsy key must not be looked up either: it would match
        # another key-less block and continue the quote from it.
        b = {"key": None, "type": "blockquote", "depth": 0}
        other = {"key": None, "type": "blockquote", "depth": 0}
        self.assertEqual(
            DOM.render(
                md_blockquote({"block": b, "blocks": [b, other], "children": "x"})
            ),
            "> x\n\n",
        )
