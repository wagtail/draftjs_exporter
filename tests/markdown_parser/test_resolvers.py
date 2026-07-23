"""Tests for entity resolver chains and default resolvers."""

import unittest

from draftjs_exporter.markdown_parser.resolvers import (
    default_image_resolver,
    default_link_resolver,
    resolve,
)


class TestDefaultLinkResolver(unittest.TestCase):
    def test_returns_link_entity(self):
        self.assertEqual(
            default_link_resolver("https://example.com", "example"),
            {
                "type": "LINK",
                "data": {"url": "https://example.com"},
                "mutability": "MUTABLE",
            },
        )


class TestDefaultImageResolver(unittest.TestCase):
    def test_returns_image_entity(self):
        self.assertEqual(
            default_image_resolver("/media/a.jpg", "an alt"),
            {
                "type": "IMAGE",
                "data": {"src": "/media/a.jpg", "alt": "an alt"},
                "mutability": "IMMUTABLE",
            },
        )


class TestResolve(unittest.TestCase):
    def test_empty_chain_uses_default(self):
        result = resolve([], "/x", "lbl", default_link_resolver)
        self.assertEqual(result["data"], {"url": "/x"})

    def test_first_match_wins(self):
        calls = []

        def first(url, label):
            calls.append("first")
            return {"type": "DOCUMENT", "data": {"id": 1}}

        def second(url, label):
            calls.append("second")
            return {"type": "LINK", "data": {}}

        result = resolve([first, second], "/x", "lbl", default_link_resolver)
        self.assertEqual(result["type"], "DOCUMENT")
        self.assertEqual(calls, ["first"])

    def test_none_defers_to_next(self):
        def defer(url, label):
            return None

        result = resolve([defer], "/x", "lbl", default_link_resolver)
        self.assertEqual(result["type"], "LINK")
