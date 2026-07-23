"""Tests for the scheme_resolver helper."""

import unittest

from draftjs_exporter.markdown_parser.resolvers import (
    EntityResolution,
    EntityResolver,
    scheme_resolver,
)


def must_resolve(resolver: EntityResolver, url: str, label: str) -> EntityResolution:
    """Resolve a URL, failing the test when the resolver defers."""
    result = resolver(url, label)
    if result is None:
        raise AssertionError(f"Resolver unexpectedly deferred for {url!r}")
    return result


class TestSchemeResolver(unittest.TestCase):
    def setUp(self):
        self.resolve = scheme_resolver(
            "wagtail",
            {"page": "LINK", "document": "DOCUMENT", "image": "IMAGE"},
            coerce={"id": int},
            label_key="alt",
        )

    def test_scheme_mismatch_returns_none(self):
        self.assertIsNone(self.resolve("https://example.com", "x"))

    def test_unmapped_host_returns_none(self):
        self.assertIsNone(self.resolve("wagtail://unknown?id=1", "x"))

    def test_host_maps_to_entity_type(self):
        # Link resolvers are configured without label_key: the label
        # stays link text and never leaks into entity data.
        resolver = scheme_resolver(
            "wagtail", {"page": "LINK", "document": "DOCUMENT"}, coerce={"id": int}
        )
        result = must_resolve(resolver, "wagtail://page?id=3", "label")
        self.assertEqual(result["type"], "LINK")
        self.assertEqual(result["data"], {"id": 3})

    def test_query_params_become_data(self):
        result = must_resolve(
            self.resolve, "wagtail://image?id=10&alt=alt&format=left", "alt"
        )
        self.assertEqual(result["data"], {"id": 10, "alt": "alt", "format": "left"})

    def test_label_fills_label_key_when_absent(self):
        result = must_resolve(self.resolve, "wagtail://image?id=10", "my alt")
        self.assertEqual(result["data"], {"id": 10, "alt": "my alt"})

    def test_label_does_not_override_query_param(self):
        result = must_resolve(
            self.resolve, "wagtail://image?id=10&alt=fromquery", "frommd"
        )
        self.assertEqual(result["data"]["alt"], "fromquery")

    def test_empty_label_not_injected(self):
        result = must_resolve(self.resolve, "wagtail://image?id=10", "")
        self.assertNotIn("alt", result["data"])

    def test_percent_decoding(self):
        result = must_resolve(
            self.resolve, "wagtail://page?id=1&url=https%3A%2F%2Fa.b%2F", "x"
        )
        self.assertEqual(result["data"]["url"], "https://a.b/")

    def test_coercion_error_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.resolve("wagtail://page?id=abc", "x")

    def test_default_mutability(self):
        result = must_resolve(self.resolve, "wagtail://page?id=3", "x")
        self.assertEqual(result["mutability"], "MUTABLE")

    def test_custom_mutability(self):
        resolver = scheme_resolver(
            "wagtail", {"image": "IMAGE"}, mutability="IMMUTABLE"
        )
        result = must_resolve(resolver, "wagtail://image?id=1", "x")
        self.assertEqual(result["mutability"], "IMMUTABLE")
