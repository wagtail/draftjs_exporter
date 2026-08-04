import unittest

from draftjs_exporter.dom import DOM
from draftjs_exporter.html import HTML
from draftjs_exporter.markdown import CONFIG as MARKDOWN_CONFIG
from draftjs_exporter.markdown.code import (
    code_element,
    code_wrapper,
    make_code_element,
    make_code_wrapper,
)


def render_code_block(text: str) -> str:
    exporter = HTML(MARKDOWN_CONFIG)
    return exporter.render(
        {
            "entityMap": {},
            "blocks": [
                {
                    "key": "a",
                    "text": text,
                    "type": "code-block",
                    "depth": 0,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                }
            ],
        }
    )


class TestCodeElement(unittest.TestCase):
    def test_renders_line_with_newline(self):
        self.assertEqual(
            DOM.render(code_element({"block": {}, "children": "test"})),
            "test\n",
        )


class TestMakeCodeElement(unittest.TestCase):
    def test_renders_line_with_newline(self):
        self.assertEqual(
            DOM.render(make_code_element()({"block": {}, "children": "test"})),
            "test\n",
        )


class TestCodeWrapper(unittest.TestCase):
    def test_renders_code_block_node(self):
        elt = code_wrapper({"block": {}})
        self.assertEqual(elt.type, "code_block")
        self.assertEqual(elt.attr["fence"], "`")


class TestMakeCodeWrapper(unittest.TestCase):
    def test_tilde_fence(self):
        elt = make_code_wrapper("~~~")({"block": {}})
        self.assertEqual(elt.attr["fence"], "~")


class TestCodeBlockExport(unittest.TestCase):
    def test_simple_code_block(self):
        self.assertEqual(render_code_block("foo"), "```\nfoo\n```\n\n")

    def test_content_not_escaped(self):
        self.assertEqual(render_code_block("# <x> & [y]"), "```\n# <x> & [y]\n```\n\n")

    def test_fence_sized_to_content(self):
        self.assertEqual(render_code_block("a```b"), "````\na```b\n````\n\n")
