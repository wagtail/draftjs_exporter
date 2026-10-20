import unittest

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.helpers import (
    md_block,
    md_has_content,
    md_inline,
    md_line_break,
    md_link_destination,
    md_mark_safe,
    md_split_edge_whitespace,
)


class TestHelpers(unittest.TestCase):
    def test_inline(self):
        self.assertEqual(DOM.render(md_inline(["test"])), "test")

    def test_block(self):
        self.assertEqual(DOM.render(md_block(["test"])), "test\n\n")


class TestLineBreak(unittest.TestCase):
    def test_hard_break(self):
        elt = md_line_break({"block": {"type": "unstyled"}, "children": ["\n"]})
        self.assertEqual(DOM.render(md_inline([elt])), "\\\n")

    def test_hard_break_in_list_item(self):
        elt = md_line_break(
            {"block": {"type": "unordered-list-item"}, "children": ["\n"]}
        )
        self.assertEqual(DOM.render(md_inline([elt])), "\\\n")

    def test_space_in_header(self):
        for type_ in ("header-one", "header-two", "header-six"):
            elt = md_line_break({"block": {"type": type_}, "children": ["\n"]})
            self.assertEqual(DOM.render(md_inline([elt])), " ", type_)

    def test_passthrough_in_code_block(self):
        children = ["\n"]
        elt = md_line_break({"block": {"type": "code-block"}, "children": children})
        self.assertIs(elt, children)

    def test_missing_block_type(self):
        elt = md_line_break({"block": {}, "children": ["\n"]})
        self.assertEqual(DOM.render(md_inline([elt])), "\\\n")


class TestMarkSafe(unittest.TestCase):
    def test_renders_verbatim(self):
        self.assertEqual(
            DOM.render(md_inline([md_mark_safe("# "), "*x*"])), "# \\*x\\*"
        )

    def test_block_prefix_flag(self):
        elt = md_mark_safe("- ", block_prefix=True)
        self.assertEqual(elt.type, "mark_safe")
        self.assertEqual(elt.attr["block_prefix"], "true")

    def test_block_prefix_default_false(self):
        elt = md_mark_safe("# ")
        self.assertEqual(elt.attr["block_prefix"], "false")


class TestLinkDestination(unittest.TestCase):
    def test_renders_escaped_url(self):
        self.assertEqual(
            DOM.render(md_inline([md_link_destination("https://example.com/a(b)")])),
            "https://example.com/a\\(b\\)",
        )


class TestSplitEdgeWhitespace(unittest.TestCase):
    def test_string(self):
        self.assertEqual(md_split_edge_whitespace("  x  "), ("  ", "x", "  "))

    def test_string_without_edges(self):
        self.assertEqual(md_split_edge_whitespace("x"), ("", "x", ""))

    def test_whitespace_only_string(self):
        self.assertEqual(md_split_edge_whitespace("  "), ("  ", "", ""))

    def test_element(self):
        elt = md_mark_safe("**")
        self.assertEqual(md_split_edge_whitespace(elt), ("", elt, ""))

    def test_fragment_single_child(self):
        elt = DOM.create_element("fragment", {}, ["  x  "])
        leading, node, trailing = md_split_edge_whitespace(elt)
        self.assertEqual((leading, DOM.render(node), trailing), ("  ", "x", "  "))

    def test_fragment_moves_outer_whitespace(self):
        elt = DOM.create_element("fragment", {}, ["  a ", " b  "])
        leading, node, trailing = md_split_edge_whitespace(elt)
        self.assertEqual((leading, DOM.render(node), trailing), ("  ", "a  b", "  "))

    def test_fragment_keeps_whitespace_between_children(self):
        elt = DOM.create_element("fragment", {}, ["a ", " b"])
        leading, node, trailing = md_split_edge_whitespace(elt)
        self.assertEqual((leading, DOM.render(node), trailing), ("", "a  b", ""))


class TestHasContent(unittest.TestCase):
    def test_text(self):
        self.assertTrue(md_has_content("x"))

    def test_whitespace_only_string(self):
        self.assertFalse(md_has_content(" \t "))

    def test_element(self):
        self.assertTrue(md_has_content(md_mark_safe("**")))

    def test_empty_fragment(self):
        self.assertFalse(md_has_content(DOM.create_element("fragment", {}, [])))

    def test_fragment_of_whitespace(self):
        self.assertFalse(md_has_content(DOM.create_element("fragment", {}, [" ", ""])))

    def test_fragment_with_text(self):
        self.assertTrue(md_has_content(DOM.create_element("fragment", {}, [" ", "x"])))
