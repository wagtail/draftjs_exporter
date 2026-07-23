"""Tests for filter rule validation."""

import unittest

from draftjs_exporter.contentstate_filter import ContentStateFilter
from draftjs_exporter.error import ConfigException
from draftjs_exporter.types import ContentState


class TestRuleValidation(unittest.TestCase):
    def test_invalid_rule_type(self):
        with self.assertRaises(ConfigException):
            ContentStateFilter([{"type": "nope", "match": "x", "action": "keep"}])  # type: ignore[typeddict-item]  # ty: ignore[invalid-argument-type]

    def test_invalid_action(self):
        with self.assertRaises(ConfigException):
            ContentStateFilter([{"type": "block", "match": "x", "action": "nope"}])  # type: ignore[typeddict-item]  # ty: ignore[invalid-argument-type]

    def test_demote_requires_header_block(self):
        with self.assertRaises(ConfigException):
            ContentStateFilter(
                [{"type": "block", "match": "unstyled", "action": "demote"}]
            )

    def test_demote_header_six_rejected(self):
        with self.assertRaises(ConfigException):
            ContentStateFilter(
                [{"type": "block", "match": "header-six", "action": "demote"}]
            )

    def test_demote_on_non_block_rejected(self):
        with self.assertRaises(ConfigException):
            ContentStateFilter(
                [{"type": "entity", "match": "header-one", "action": "demote"}]
            )

    def test_no_rules_is_identity(self):
        cs: ContentState = {"blocks": [], "entityMap": {}}
        self.assertEqual(ContentStateFilter().apply(cs), cs)
        self.assertEqual(ContentStateFilter(None).apply(cs), cs)

    def test_callable_returning_garbage_rejected(self):
        cs: ContentState = {
            "blocks": [
                {
                    "key": "a",
                    "text": "x",
                    "type": "unstyled",
                    "depth": 0,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                }
            ],
            "entityMap": {},
        }
        with self.assertRaises(ConfigException):
            ContentStateFilter(
                [{"type": "block", "match": "unstyled", "action": lambda b: 42}]
            ).apply(cs)
