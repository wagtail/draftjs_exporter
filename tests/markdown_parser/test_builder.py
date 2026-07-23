"""Tests for the ContentState builder."""

import unittest

from draftjs_exporter.markdown_parser.builder import ContentStateBuilder


class TestContentStateBuilder(unittest.TestCase):
    def test_empty_build(self):
        builder = ContentStateBuilder()
        self.assertEqual(builder.build(), {"blocks": [], "entityMap": {}})

    def test_block_keys_are_sequential(self):
        builder = ContentStateBuilder()
        builder.add_block("unstyled", "a")
        builder.add_block("unstyled", "b")
        keys = [b["key"] for b in builder.build()["blocks"]]
        self.assertEqual(keys, ["00000", "00001"])
        self.assertEqual(len(set(keys)), 2)

    def test_block_defaults(self):
        builder = ContentStateBuilder()
        builder.add_block("unstyled", "a")
        block = builder.build()["blocks"][0]
        self.assertEqual(block["depth"], 0)
        self.assertEqual(block["inlineStyleRanges"], [])
        self.assertEqual(block["entityRanges"], [])

    def test_add_entity_returns_int_keys(self):
        builder = ContentStateBuilder()
        first = builder.add_entity("LINK", {"url": "/a"})
        second = builder.add_entity("IMAGE", {"src": "/b"}, "IMMUTABLE")
        self.assertEqual((first, second), (0, 1))
        entity_map = builder.build()["entityMap"]
        self.assertEqual(
            entity_map["0"],
            {"type": "LINK", "mutability": "MUTABLE", "data": {"url": "/a"}},
        )
        self.assertEqual(entity_map["1"]["mutability"], "IMMUTABLE")

    def test_full_block(self):
        builder = ContentStateBuilder()
        key = builder.add_entity("LINK", {"url": "/a"})
        builder.add_block(
            "unstyled",
            "text",
            depth=2,
            inline_style_ranges=[{"offset": 0, "length": 2, "style": "BOLD"}],
            entity_ranges=[{"offset": 0, "length": 4, "key": key}],
        )
        block = builder.build()["blocks"][0]
        self.assertEqual(block["depth"], 2)
        self.assertEqual(block["entityRanges"][0]["key"], 0)
