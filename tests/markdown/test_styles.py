import unittest

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.styles import inline_style


class TestInlineStyle(unittest.TestCase):
    def test_works(self):
        self.assertEqual(DOM.render(inline_style("*")({"children": "test"})), "*test*")

    def test_inline_style_uses_mark_safe(self):
        elt = inline_style("**")({"children": "x"})
        self.assertEqual(elt.children[0].type, "mark_safe")
        self.assertEqual(elt.children[0].attr["markup"], "**")
