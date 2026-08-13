import unittest

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.entities import (
    md_horizontal_rule,
    md_image,
    md_link,
    md_make_horizontal_rule,
)


class TestEntities(unittest.TestCase):
    def test_horizontal_rule(self):
        self.assertEqual(DOM.render(md_horizontal_rule({})), "---\n\n")

    def test_image(self):
        self.assertEqual(
            DOM.render(md_image({"src": "test.png"})),
            "![](test.png)\n\n",
        )

    def test_image_alt(self):
        self.assertEqual(
            DOM.render(md_image({"src": "test.png", "alt": "test"})),
            "![test](test.png)\n\n",
        )

    def test_link(self):
        self.assertEqual(
            DOM.render(md_link({"url": "http://www.example.com/", "children": "test"})),
            "[test](http://www.example.com/)",
        )

    def test_link_url_escaped(self):
        self.assertEqual(
            DOM.render(md_link({"url": "https://example.com/a(b)", "children": "x"})),
            "[x](https://example.com/a\\(b\\))",
        )

    def test_image_src_escaped(self):
        self.assertEqual(
            DOM.render(md_image({"src": "a b.png"})),
            "![](a%20b.png)\n\n",
        )

    def test_make_horizontal_rule_stars(self):
        self.assertEqual(DOM.render(md_make_horizontal_rule("***")({})), "***\n\n")

    def test_make_horizontal_rule_underscores(self):
        self.assertEqual(DOM.render(md_make_horizontal_rule("___")({})), "___\n\n")
