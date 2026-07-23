"""Tests for the assembled MarkdownParser."""

import unittest

from draftjs_exporter.markdown_parser import MarkdownParser
from draftjs_exporter.markdown_parser.resolvers import scheme_resolver


class TestMarkdownParser(unittest.TestCase):
    def test_empty_config_uses_defaults(self):
        cs = MarkdownParser().parse("# Hi\n\nSome **bold** text.")
        self.assertEqual([b["type"] for b in cs["blocks"]], ["header-one", "unstyled"])

    def test_none_config_uses_defaults(self):
        cs = MarkdownParser(None).parse("text")
        self.assertEqual(cs["blocks"][0]["text"], "text")

    def test_crlf_normalized(self):
        cs = MarkdownParser().parse("a\r\n\r\nb")
        self.assertEqual(len(cs["blocks"]), 2)

    def test_non_string_input_raises_type_error(self):
        with self.assertRaises(TypeError):
            MarkdownParser().parse(None)  # type: ignore[arg-type]

    def test_config_toggle_passed_through(self):
        cs = MarkdownParser({"headings": False}).parse("# Title")
        self.assertEqual(cs["blocks"][0]["type"], "unstyled")

    def test_resolvers_passed_through(self):
        parser = MarkdownParser(
            {
                "link_resolvers": [
                    scheme_resolver("wagtail", {"page": "LINK"}, coerce={"id": int})
                ]
            }
        )
        cs = parser.parse("[label](wagtail://page?id=3)")
        self.assertEqual(cs["entityMap"]["0"]["data"], {"id": 3})

    def test_structural_invariants(self):
        cs = MarkdownParser().parse(
            "# T\n\n- a\n  - b\n\n[link](/x) and ![img](/y)\n\n---"
        )
        keys = [b["key"] for b in cs["blocks"]]
        self.assertEqual(len(keys), len(set(keys)))
        referenced = {str(r["key"]) for b in cs["blocks"] for r in b["entityRanges"]}
        self.assertEqual(set(cs["entityMap"].keys()), referenced)
        for block in cs["blocks"]:
            text_length = len(block["text"])
            for r in block["inlineStyleRanges"] + block["entityRanges"]:
                self.assertGreaterEqual(r["offset"], 0)
                self.assertLessEqual(r["offset"] + r["length"], text_length)
