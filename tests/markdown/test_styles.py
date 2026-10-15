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

    def test_whitespace_only_text_is_not_marked(self):
        # Emphasis cannot enclose only whitespace: the spaces are kept, the
        # delimiters are dropped.
        self.assertEqual(DOM.render(md_inline_style("**")({"children": "  "})), "  ")

    def test_whitespace_left_by_a_nested_style_is_not_marked(self):
        # A nested style moves the whitespace outside its own delimiters,
        # leaving the outer style with a fragment that renders nothing. The
        # outer delimiters must be dropped rather than emitted empty.
        inner = md_inline_style("_")({"children": " "})
        children = DOM.create_element("fragment", {}, [inner])
        self.assertEqual(DOM.render(md_inline_style("**")({"children": children})), " ")


class TestCodeSpan(unittest.TestCase):
    def test_renders_code_span_node(self):
        elt = md_code_span({"children": "a*b"})
        self.assertEqual(elt.type, "code_span")
        self.assertEqual(DOM.render(elt), "`a*b`")

    def test_backtick_content_sized(self):
        self.assertEqual(DOM.render(md_code_span({"children": "a`b"})), "``a`b``")
