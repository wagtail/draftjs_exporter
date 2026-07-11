import unittest

from draftjs_exporter.command import Command
from draftjs_exporter.dom import DOM
from draftjs_exporter.options import Options
from draftjs_exporter.style_state import StyleState
from draftjs_exporter.types import Block, ConfigMap, Element, Props


def Important(props):
    return DOM.create_element("strong", {"style": {"color": "red"}}, props["children"])


def Shout(props: Props) -> Element:
    return DOM.create_element(
        "span", {"style": {"textTransform": "uppercase"}}, props["children"]
    )


style_map: ConfigMap = {
    "ITALIC": "em",
    "BOLD": "strong",
    "HIGHLIGHT": {
        "element": "strong",
        "props": {"style": {"textDecoration": "underline"}},
    },
    "KBD": {"element": "kbd", "props": {"class": "o-keyboard-shortcut"}},
    "IMPORTANT": Important,
    "SHOUT": Shout,
}


class TestStyleState(unittest.TestCase):
    def setUp(self):
        DOM.use(DOM.STRING)
        self.style_state = StyleState(Options.map_styles(style_map))

    def test_init(self):
        self.assertIsInstance(self.style_state, StyleState)

    def test_apply_start_inline_style(self):
        self.style_state.apply(Command("start_inline_style", 0, "ITALIC"))
        self.assertEqual(self.style_state.styles, ["ITALIC"])

    def test_apply_stop_inline_style(self):
        self.style_state.apply(Command("start_inline_style", 0, "ITALIC"))
        self.style_state.apply(Command("stop_inline_style", 0, "ITALIC"))
        self.assertEqual(self.style_state.styles, [])

    def test_is_empty_default(self):
        self.assertEqual(self.style_state.is_empty(), True)

    def test_is_empty_styled(self):
        self.style_state.apply(Command("start_inline_style", 0, "ITALIC"))
        self.assertEqual(self.style_state.is_empty(), False)

    def test_render_styles_unstyled(self):
        self.assertEqual(
            self.style_state.render_styles("Test text", {}, []), "Test text"
        )

    def test_render_styles_unicode(self):
        self.assertEqual(self.style_state.render_styles("🍺", {}, []), "🍺")

    def test_render_styles_styled(self):
        self.style_state.apply(Command("start_inline_style", 0, "ITALIC"))
        self.assertEqual(
            DOM.render_debug(self.style_state.render_styles("Test text", {}, [])),
            "<em>Test text</em>",
        )
        self.style_state.apply(Command("stop_inline_style", 9, "ITALIC"))

    def test_render_styles_styled_multiple(self):
        self.style_state.apply(Command("start_inline_style", 0, "BOLD"))
        self.style_state.apply(Command("start_inline_style", 0, "ITALIC"))
        self.assertEqual(
            DOM.render_debug(self.style_state.render_styles("Test text", {}, [])),
            "<strong><em>Test text</em></strong>",
        )

    def test_render_styles_attributes(self):
        self.style_state.apply(Command("start_inline_style", 0, "KBD"))
        self.assertEqual(
            DOM.render_debug(self.style_state.render_styles("Test text", {}, [])),
            '<kbd class="o-keyboard-shortcut">Test text</kbd>',
        )
        self.style_state.apply(Command("stop_inline_style", 9, "KBD"))

    def test_render_styles_component(self):
        self.style_state.apply(Command("start_inline_style", 0, "IMPORTANT"))
        self.assertEqual(
            DOM.render_debug(self.style_state.render_styles("Test text", {}, [])),
            '<strong style="color: red;">Test text</strong>',
        )
        self.style_state.apply(Command("stop_inline_style", 9, "IMPORTANT"))

    def test_render_styles_component_multiple(self):
        self.style_state.apply(Command("start_inline_style", 0, "IMPORTANT"))
        self.style_state.apply(Command("start_inline_style", 0, "SHOUT"))
        self.assertEqual(
            DOM.render_debug(self.style_state.render_styles("Test text", {}, [])),
            '<strong style="color: red;"><span style="text-transform: uppercase;">Test text</span></strong>',
        )
        self.style_state.apply(Command("stop_inline_style", 9, "IMPORTANT"))
        self.style_state.apply(Command("stop_inline_style", 9, "SHOUT"))

    def test_render_styles_component_multiple_invert(self):
        self.style_state.apply(Command("start_inline_style", 0, "SHOUT"))
        self.style_state.apply(Command("start_inline_style", 0, "IMPORTANT"))
        self.assertEqual(
            DOM.render_debug(self.style_state.render_styles("Test text", {}, [])),
            '<strong style="color: red;"><span style="text-transform: uppercase;">Test text</span></strong>',
        )
        self.style_state.apply(Command("stop_inline_style", 9, "SHOUT"))
        self.style_state.apply(Command("stop_inline_style", 9, "IMPORTANT"))

    def test_render_styles_data(self):
        blocks: list[Block] = [
            {
                "key": "5s7g9",
                "text": "test",
                "type": "unstyled",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [],
            }
        ]

        def component(props):
            self.assertEqual(props["blocks"], blocks)
            self.assertEqual(props["block"], blocks[0])
            self.assertEqual(props["inline_style_range"]["style"], "ITALIC")
            return None

        style_state = StyleState(Options.map_styles({"ITALIC": component}))

        style_state.apply(Command("start_inline_style", 0, "ITALIC"))
        style_state.render_styles("Test text", blocks[0], blocks)
        style_state.apply(Command("stop_inline_style", 9, "ITALIC"))

    def test_start_segment_no_styles_returns_content(self):
        block: Block = {
            "key": "5s7g9",
            "text": "test",
            "type": "unstyled",
            "depth": 0,
            "inlineStyleRanges": [],
            "entityRanges": [],
        }
        content = DOM.create_element()
        innermost = self.style_state.start_segment(block, [block], content)
        self.assertIs(innermost, content)
        self.assertEqual(self.style_state.element_stack, [])

    def test_start_segment_open_one_style(self):
        block: Block = {
            "key": "5s7g9",
            "text": "test",
            "type": "unstyled",
            "depth": 0,
            "inlineStyleRanges": [],
            "entityRanges": [],
        }
        content = DOM.create_element()
        self.style_state.apply(Command("start_inline_style", 0, "BOLD"))
        innermost = self.style_state.start_segment(block, [block], content)
        self.assertEqual(len(self.style_state.element_stack), 1)
        self.assertEqual(self.style_state.element_stack[0][0], "BOLD")
        self.assertIs(innermost, self.style_state.element_stack[0][1])
        # The strong element is a child of content
        self.assertEqual(len(content.children), 1)

    def test_start_segment_prefix_match(self):
        """When the prefix of active styles matches the existing stack,
        keep the outer tags open and create only new inner tags."""
        block: Block = {
            "key": "5s7g9",
            "text": "Bold Italic",
            "type": "unstyled",
            "depth": 0,
            "inlineStyleRanges": [],
            "entityRanges": [],
        }
        content = DOM.create_element()

        # First segment: [BOLD]
        self.style_state.apply(Command("start_inline_style", 0, "BOLD"))
        innermost = self.style_state.start_segment(block, [block], content)
        DOM.append_child(innermost, "Bold ")
        self.assertEqual(len(self.style_state.element_stack), 1)

        # Second segment: [BOLD, ITALIC] — BOLD is already open, only ITALIC opens
        self.style_state.apply(Command("start_inline_style", 5, "ITALIC"))
        innermost = self.style_state.start_segment(block, [block], content)
        self.assertEqual(len(self.style_state.element_stack), 2)
        self.assertEqual(self.style_state.element_stack[1][0], "ITALIC")
        DOM.append_child(innermost, "Italic")

        # Third segment: [] — both close
        self.style_state.apply(Command("stop_inline_style", 11, "BOLD"))
        self.style_state.apply(Command("stop_inline_style", 11, "ITALIC"))
        innermost = self.style_state.start_segment(block, [block], content)
        self.assertIs(innermost, content)
        self.assertEqual(self.style_state.element_stack, [])

        # Verify the rendered tree
        self.assertEqual(
            DOM.render_debug(content),
            "<fragment><strong>Bold <em>Italic</em></strong></fragment>",
        )

    def test_start_segment_close_and_reopen(self):
        """Adjacent styles close and reopen since there is no shared prefix."""
        block: Block = {
            "key": "5s7g9",
            "text": "BoldItalic",
            "type": "unstyled",
            "depth": 0,
            "inlineStyleRanges": [],
            "entityRanges": [],
        }
        content = DOM.create_element()

        # Segment 1: [ITALIC]
        self.style_state.apply(Command("start_inline_style", 0, "ITALIC"))
        innermost = self.style_state.start_segment(block, [block], content)
        DOM.append_child(innermost, "Bold")

        # Segment 2: [BOLD] — no prefix match, ITALIC closes, BOLD opens
        self.style_state.apply(Command("stop_inline_style", 4, "ITALIC"))
        self.style_state.apply(Command("start_inline_style", 4, "BOLD"))
        innermost = self.style_state.start_segment(block, [block], content)
        DOM.append_child(innermost, "Italic")

        # Segment 3: []
        self.style_state.apply(Command("stop_inline_style", 10, "BOLD"))
        self.style_state.start_segment(block, [block], content)

        self.assertEqual(
            DOM.render_debug(content),
            "<fragment><em>Bold</em><strong>Italic</strong></fragment>",
        )

    def test_flush_clears_stack(self):
        block: Block = {
            "key": "5s7g9",
            "text": "test",
            "type": "unstyled",
            "depth": 0,
            "inlineStyleRanges": [],
            "entityRanges": [],
        }
        content = DOM.create_element()
        self.style_state.apply(Command("start_inline_style", 0, "BOLD"))
        self.style_state.start_segment(block, [block], content)
        self.assertEqual(len(self.style_state.element_stack), 1)
        self.style_state.flush()
        self.assertEqual(self.style_state.element_stack, [])

    def test_uses_components_false_for_string_tags(self):
        block: Block = {
            "key": "5s7g9",
            "text": "test",
            "type": "unstyled",
            "depth": 0,
            "inlineStyleRanges": [
                {"offset": 0, "length": 4, "style": "ITALIC"},
                {"offset": 0, "length": 4, "style": "BOLD"},
            ],
            "entityRanges": [],
        }
        self.assertFalse(self.style_state.uses_components(block))

    def test_uses_components_true_when_any_is_callable(self):
        block: Block = {
            "key": "5s7g9",
            "text": "test",
            "type": "unstyled",
            "depth": 0,
            "inlineStyleRanges": [
                {"offset": 0, "length": 4, "style": "ITALIC"},
                {"offset": 0, "length": 4, "style": "IMPORTANT"},
            ],
            "entityRanges": [],
        }
        self.assertTrue(self.style_state.uses_components(block))
