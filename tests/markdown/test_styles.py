import unittest

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.styles import md_code_span, md_inline_style


class TestInlineStyle(unittest.TestCase):
    def test_works(self):
        self.assertEqual(
            DOM.render(md_inline_style("*")({"children": "test"})), "*test*"
        )

    def test_inline_style_uses_mark_safe(self):
        elt = md_inline_style("**")({"children": "x"})
        self.assertEqual(elt.children[0].type, "mark_safe")
        self.assertEqual(elt.children[0].attr["markup"], "**")


class TestCodeSpan(unittest.TestCase):
    def test_renders_code_span_node(self):
        elt = md_code_span({"children": "a*b"})
        self.assertEqual(elt.type, "code_span")
        self.assertEqual(DOM.render(elt), "`a*b`")

    def test_backtick_content_sized(self):
        self.assertEqual(DOM.render(md_code_span({"children": "a`b"})), "``a`b``")
