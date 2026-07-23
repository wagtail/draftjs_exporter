"""Tests for the MarkdownImporter public API."""

import unittest

from draftjs_exporter.error import MarkdownParseError
from draftjs_exporter.markdown_importer import MarkdownImporter
from draftjs_exporter.markdown_parser import scheme_resolver


class TestMarkdownImporter(unittest.TestCase):
    def test_default_import(self):
        cs = MarkdownImporter().import_markdown("# Hello\n\nWorld")
        self.assertEqual([b["type"] for b in cs["blocks"]], ["header-one", "unstyled"])

    def test_none_config(self):
        cs = MarkdownImporter(None).import_markdown("text")
        self.assertEqual(cs["blocks"][0]["text"], "text")

    def test_filter_rules_applied(self):
        importer = MarkdownImporter(
            {
                "filter_rules": [
                    {"type": "block", "match": "header-one", "action": "demote"}
                ]
            }
        )
        cs = importer.import_markdown("# Hello")
        self.assertEqual(cs["blocks"][0]["type"], "header-two")

    def test_parser_config_applied(self):
        importer = MarkdownImporter({"parser_config": {"headings": False}})
        cs = importer.import_markdown("# Hello")
        self.assertEqual(cs["blocks"][0]["type"], "unstyled")

    def test_custom_parser_dotted_path(self):
        importer = MarkdownImporter(
            {"parser": "draftjs_exporter.markdown_parser.MarkdownParser"}
        )
        cs = importer.import_markdown("text")
        self.assertEqual(cs["blocks"][0]["text"], "text")

    def test_parse_error_propagates(self):
        def bad(url, label):
            raise RuntimeError("boom")

        importer = MarkdownImporter({"parser_config": {"link_resolvers": [bad]}})
        with self.assertRaises(MarkdownParseError):
            importer.import_markdown("[a](/b)")

    def test_wagtail_style_end_to_end(self):
        importer = MarkdownImporter(
            {
                "parser_config": {
                    "image_resolvers": [
                        scheme_resolver(
                            "wagtail",
                            {"image": "IMAGE"},
                            coerce={"id": int},
                            label_key="alt",
                            mutability="IMMUTABLE",
                        )
                    ]
                }
            }
        )
        cs = importer.import_markdown(
            "![alt](wagtail://image?id=10&alt=alt&format=left)"
        )
        self.assertEqual(
            cs["entityMap"]["0"]["data"],
            {"id": 10, "alt": "alt", "format": "left"},
        )
