import unittest

import draftjs_exporter
from draftjs_exporter import (
    BLOCK_TYPES,
    DOM,
    HTML,
    HTML_CONFIG,
    MARKDOWN_CONFIG,
    ContentState,
    Exporter,
    ExporterConfig,
    HTMLExporter,
    code_block,
    md_block,
    md_image,
    md_link,
    md_mark_safe,
    render_children,
)
from draftjs_exporter.defaults import (
    code_block as defaults_code_block,
)
from draftjs_exporter.defaults import (
    render_children as defaults_render_children,
)
from draftjs_exporter.markdown.entities import md_image as entities_md_image
from draftjs_exporter.markdown.entities import md_link as entities_md_link
from draftjs_exporter.markdown.helpers import md_block as helpers_md_block
from draftjs_exporter.markdown.helpers import md_mark_safe as helpers_md_mark_safe


class TestTopLevelAPI(unittest.TestCase):
    def test_exporter_is_html(self):
        self.assertIs(Exporter, HTML)

    def test_html_exporter_is_html(self):
        self.assertIs(HTMLExporter, HTML)

    def test_code_block_reexport(self):
        self.assertIs(code_block, defaults_code_block)

    def test_render_children_reexport(self):
        self.assertIs(render_children, defaults_render_children)

    def test_markdown_helpers_reexport(self):
        self.assertIs(md_block, helpers_md_block)
        self.assertIs(md_mark_safe, helpers_md_mark_safe)
        self.assertIs(md_image, entities_md_image)
        self.assertIs(md_link, entities_md_link)

    def test_all_members_importable(self):
        for name in draftjs_exporter.__all__:
            self.assertTrue(hasattr(draftjs_exporter, name), f"{name} not importable")

    def test_html_config_keys(self):
        self.assertIn("block_map", HTML_CONFIG)
        self.assertIn("style_map", HTML_CONFIG)
        self.assertIn("engine", HTML_CONFIG)

    def test_html_config_engine(self):
        self.assertEqual(HTML_CONFIG["engine"], DOM.STRING)

    def test_markdown_config_keys(self):
        self.assertIn("block_map", MARKDOWN_CONFIG)
        self.assertIn("style_map", MARKDOWN_CONFIG)
        self.assertIn("entity_decorators", MARKDOWN_CONFIG)
        self.assertIn("engine", MARKDOWN_CONFIG)

    def test_markdown_config_engine(self):
        self.assertEqual(MARKDOWN_CONFIG["engine"], DOM.MARKDOWN)


content_state: ContentState = {
    "entityMap": {},
    "blocks": [
        {
            "key": "a",
            "text": "Hello, World!",
            "type": "unstyled",
            "depth": 0,
            "inlineStyleRanges": [],
            "entityRanges": [],
        },
    ],
}


class TestExporterRendering(unittest.TestCase):
    def test_html_config_matches_default(self):
        """HTML_CONFIG should produce the same output as HTML() with no config."""
        default = HTML().render(content_state)
        explicit = Exporter(HTML_CONFIG).render(content_state)
        self.assertEqual(default, explicit)

    def test_html_config_render(self):
        result = Exporter(HTML_CONFIG).render(content_state)
        self.assertEqual(result, "<p>Hello, World!</p>")

    def test_markdown_config_render(self):
        result = Exporter(MARKDOWN_CONFIG).render(content_state)
        self.assertEqual(result, "Hello, World!\n\n")

    def test_html_config_extend(self):
        """Spreading HTML_CONFIG with overrides should work."""
        config: ExporterConfig = {
            **HTML_CONFIG,
            "block_map": {
                **HTML_CONFIG["block_map"],
                BLOCK_TYPES.UNSTYLED: "div",
            },
        }
        result = Exporter(config).render(content_state)
        self.assertEqual(result, "<div>Hello, World!</div>")
