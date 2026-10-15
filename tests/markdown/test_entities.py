import unittest

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.entities import (
    md_horizontal_rule,
    md_image,
    md_link,
    md_make_horizontal_rule,
)
from draftjs_exporter.markdown.styles import md_inline_style


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

    def test_link_text_mixing_text_and_inline_style_keeps_spaces(self):
        styled = md_inline_style("**")({"children": "bold"})
        children = DOM.create_element("fragment", {}, ["click ", styled, " here"])
        self.assertEqual(
            DOM.render(md_link({"url": "http://x", "children": children})),
            "[click **bold** here](http://x)",
        )

    def test_link_text_edges_moved_outside_brackets(self):
        self.assertEqual(
            DOM.render(md_link({"url": "http://x", "children": " spaced "})),
            " [spaced](http://x) ",
        )

    def test_image_src_escaped(self):
        self.assertEqual(
            DOM.render(md_image({"src": "a b.png"})),
            "![](a%20b.png)\n\n",
        )

    def test_image_missing_src(self):
        self.assertEqual(DOM.render(md_image({})), "![]()\n\n")

    def test_image_src_none(self):
        self.assertEqual(DOM.render(md_image({"src": None})), "![]()\n\n")

    def test_link_missing_url(self):
        self.assertEqual(DOM.render(md_link({"children": "test"})), "[test]()")

    def test_link_url_none(self):
        self.assertEqual(
            DOM.render(md_link({"url": None, "children": "test"})), "[test]()"
        )

    def test_make_horizontal_rule_stars(self):
        self.assertEqual(DOM.render(md_make_horizontal_rule("***")({})), "***\n\n")

    def test_make_horizontal_rule_underscores(self):
        self.assertEqual(DOM.render(md_make_horizontal_rule("___")({})), "___\n\n")
