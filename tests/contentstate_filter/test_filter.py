"""Tests for ContentState filtering."""

import unittest

from draftjs_exporter.contentstate_filter import ContentStateFilter
from draftjs_exporter.types import Block, ContentState, EntityRange, InlineStyleRange


def cs_with_blocks(*blocks: Block) -> ContentState:
    """Build a ContentState from blocks with an empty entity map."""
    return {"blocks": list(blocks), "entityMap": {}}


def make_block(
    type_: str,
    text: str = "x",
    depth: int = 0,
    styles: list[InlineStyleRange] | None = None,
    entities: list[EntityRange] | None = None,
) -> Block:
    """Build a single Draft.js block."""
    return {
        "key": "aaaaa",
        "text": text,
        "type": type_,
        "depth": depth,
        "inlineStyleRanges": styles or [],
        "entityRanges": entities or [],
    }


class TestBlockRules(unittest.TestCase):
    def test_remove_block(self):
        cs = cs_with_blocks(make_block("header-one"), make_block("unstyled"))
        result = ContentStateFilter(
            [{"type": "block", "match": "header-one", "action": "remove"}]
        ).apply(cs)
        self.assertEqual([b["type"] for b in result["blocks"]], ["unstyled"])

    def test_keep_is_noop(self):
        cs = cs_with_blocks(make_block("header-one"))
        result = ContentStateFilter(
            [{"type": "block", "match": "header-one", "action": "keep"}]
        ).apply(cs)
        self.assertEqual(len(result["blocks"]), 1)

    def test_demote_headings(self):
        cs = cs_with_blocks(
            make_block("header-one"),
            make_block("header-three"),
        )
        result = ContentStateFilter(
            [{"type": "block", "match": "header-one", "action": "demote"}]
        ).apply(cs)
        self.assertEqual(
            [b["type"] for b in result["blocks"]], ["header-two", "header-three"]
        )

    def test_unmatched_blocks_kept(self):
        cs = cs_with_blocks(make_block("header-two"))
        result = ContentStateFilter(
            [{"type": "block", "match": "header-one", "action": "remove"}]
        ).apply(cs)
        self.assertEqual(len(result["blocks"]), 1)

    def test_callable_replaces_block(self):
        def replace(block):
            return {**block, "type": "unstyled"}

        cs = cs_with_blocks(make_block("header-one"))
        result = ContentStateFilter(
            [{"type": "block", "match": "header-one", "action": replace}]
        ).apply(cs)
        self.assertEqual(result["blocks"][0]["type"], "unstyled")

    def test_callable_none_removes(self):
        cs = cs_with_blocks(make_block("unstyled"))
        result = ContentStateFilter(
            [{"type": "block", "match": "unstyled", "action": lambda b: None}]
        ).apply(cs)
        self.assertEqual(result["blocks"], [])

    def test_input_not_mutated(self):
        block = make_block("header-one")
        cs = cs_with_blocks(block)
        ContentStateFilter(
            [{"type": "block", "match": "header-one", "action": "demote"}]
        ).apply(cs)
        self.assertEqual(block["type"], "header-one")


class TestInlineStyleRules(unittest.TestCase):
    def test_remove_style(self):
        block = make_block(
            "unstyled",
            text="abc",
            styles=[
                {"offset": 0, "length": 1, "style": "BOLD"},
                {"offset": 1, "length": 1, "style": "ITALIC"},
            ],
        )
        result = ContentStateFilter(
            [{"type": "inline_style", "match": "BOLD", "action": "remove"}]
        ).apply(cs_with_blocks(block))
        self.assertEqual(
            result["blocks"][0]["inlineStyleRanges"],
            [{"offset": 1, "length": 1, "style": "ITALIC"}],
        )

    def test_callable_renames_style(self):
        block = make_block(
            "unstyled", text="a", styles=[{"offset": 0, "length": 1, "style": "X"}]
        )
        result = ContentStateFilter(
            [{"type": "inline_style", "match": "X", "action": lambda style: "BOLD"}]
        ).apply(cs_with_blocks(block))
        self.assertEqual(result["blocks"][0]["inlineStyleRanges"][0]["style"], "BOLD")


class TestEntityRules(unittest.TestCase):
    def setUp(self) -> None:
        self.cs: ContentState = {
            "blocks": [
                make_block(
                    "unstyled",
                    text="ab",
                    entities=[{"offset": 0, "length": 1, "key": 0}],
                )
            ],
            "entityMap": {
                "0": {"type": "LINK", "mutability": "MUTABLE", "data": {"url": "/x"}}
            },
        }

    def test_remove_entity(self):
        result = ContentStateFilter(
            [{"type": "entity", "match": "LINK", "action": "remove"}]
        ).apply(self.cs)
        self.assertEqual(result["blocks"][0]["entityRanges"], [])
        self.assertEqual(result["entityMap"], {})

    def test_unmatched_entity_kept(self):
        result = ContentStateFilter(
            [{"type": "entity", "match": "IMAGE", "action": "remove"}]
        ).apply(self.cs)
        self.assertEqual(result["entityMap"], self.cs["entityMap"])

    def test_callable_replaces_entity(self):
        result = ContentStateFilter(
            [
                {
                    "type": "entity",
                    "match": "LINK",
                    "action": lambda e: {**e, "data": {"url": "/y"}},
                }
            ]
        ).apply(self.cs)
        self.assertEqual(result["entityMap"]["0"]["data"], {"url": "/y"})

    def test_orphaned_range_dropped(self):
        self.cs["blocks"][0]["entityRanges"] = [{"offset": 0, "length": 1, "key": 9}]
        result = ContentStateFilter([]).apply(self.cs)
        self.assertEqual(result["blocks"][0]["entityRanges"], [])


class TestDepthNormalization(unittest.TestCase):
    def test_removed_parent_clamps_depth(self):
        cs = cs_with_blocks(
            make_block("unordered-list-item", depth=0),
            make_block("unordered-list-item", depth=1),
            make_block("unordered-list-item", depth=2),
        )
        result = ContentStateFilter(
            [
                {
                    "type": "block",
                    "match": "unordered-list-item",
                    "action": lambda b: None if b["depth"] == 0 else b,
                }
            ]
        ).apply(cs)
        self.assertEqual([b["depth"] for b in result["blocks"]], [0, 1])

    def test_depth_reset_after_non_list_block(self):
        cs = cs_with_blocks(
            make_block("unstyled"),
            make_block("unordered-list-item", depth=2),
        )
        result = ContentStateFilter([]).apply(cs)
        self.assertEqual(result["blocks"][1]["depth"], 0)


class TestEdgeCases(unittest.TestCase):
    def test_chain_stops_after_remove(self):
        block = make_block("unstyled")
        cs = cs_with_blocks(block)
        result = ContentStateFilter(
            [
                {"type": "block", "match": "unstyled", "action": "remove"},
                {"type": "block", "match": "unstyled", "action": "keep"},
            ]
        ).apply(cs)
        self.assertEqual(result["blocks"], [])

    def test_block_callback_without_type_rejected(self):
        from draftjs_exporter.error import ConfigException

        cs = cs_with_blocks(make_block("unstyled"))
        with self.assertRaises(ConfigException):
            ContentStateFilter(
                [{"type": "block", "match": "unstyled", "action": lambda b: {}}]
            ).apply(cs)

    def test_entity_callback_without_type_rejected(self):
        from draftjs_exporter.error import ConfigException

        cs: ContentState = {
            "blocks": [
                make_block(
                    "unstyled",
                    text="a",
                    entities=[{"offset": 0, "length": 1, "key": 0}],
                )
            ],
            "entityMap": {"0": {"type": "LINK", "mutability": "MUTABLE", "data": {}}},
        }
        with self.assertRaises(ConfigException):
            ContentStateFilter(
                [{"type": "entity", "match": "LINK", "action": lambda e: {}}]
            ).apply(cs)


class TestDemoteChainGuards(unittest.TestCase):
    def test_demote_after_callback_returning_bad_block_rejected(self):
        from draftjs_exporter.error import ConfigException

        cs = cs_with_blocks(make_block("header-one"))
        with self.assertRaises(ConfigException):
            ContentStateFilter(
                [
                    {"type": "block", "match": "header-one", "action": lambda b: {}},
                    {"type": "block", "match": "header-one", "action": "demote"},
                ]
            ).apply(cs)

    def test_demote_after_callback_changing_type_rejected(self):
        from draftjs_exporter.error import ConfigException

        cs = cs_with_blocks(make_block("header-one"))
        with self.assertRaises(ConfigException):
            ContentStateFilter(
                [
                    {
                        "type": "block",
                        "match": "header-one",
                        "action": lambda b: {**b, "type": "unstyled"},
                    },
                    {"type": "block", "match": "header-one", "action": "demote"},
                ]
            ).apply(cs)
