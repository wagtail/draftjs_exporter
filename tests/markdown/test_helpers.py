import unittest

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.helpers import block, inline, link_destination, mark_safe


class TestHelpers(unittest.TestCase):
    def test_inline(self):
        self.assertEqual(DOM.render(inline(["test"])), "test")

    def test_block(self):
        self.assertEqual(DOM.render(block(["test"])), "test\n\n")


class TestMarkSafe(unittest.TestCase):
    def test_renders_verbatim(self):
        self.assertEqual(DOM.render(inline([mark_safe("# "), "x"])), "# x")

    def test_block_prefix_flag(self):
        elt = mark_safe("- ", block_prefix=True)
        self.assertEqual(elt.type, "mark_safe")
        self.assertEqual(elt.attr["block_prefix"], "true")

    def test_block_prefix_default_false(self):
        elt = mark_safe("# ")
        self.assertEqual(elt.attr["block_prefix"], "false")


class TestLinkDestination(unittest.TestCase):
    def test_renders_escaped_url(self):
        self.assertEqual(
            DOM.render(inline([link_destination("https://example.com/a(b)")])),
            "https://example.com/a\\(b\\)",
        )
