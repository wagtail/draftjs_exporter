import json
import os
import unittest

from draftjs_exporter.html import HTML
from draftjs_exporter.markdown import CONFIG as MARKDOWN_CONFIG
from draftjs_exporter.markdown import build_markdown_config
from draftjs_exporter.markdown.importer import markdown_to_content_state

fixtures_path = os.path.join(os.path.dirname(__file__), "..", "test_exports.json")
with open(fixtures_path) as f:
    fixtures = json.loads(f.read())

FIXTURES_BY_LABEL = {f["label"]: f for f in fixtures}

# Cases where the markdown output is a lossless representation of the content_state,
# meaning the importer can fully reconstruct block types, text, inline styles,
# entity offsets/lengths, and depth.
LOSSLESS_CASES = [
    "Plain text",
    "Single inline style",
    "Nested inline styles",
    "Nested inline styles (inverted)",
    "Partially nested inline styles",
    "Adjacent inline styles",
    "Adjacent entities",
    "Entity with inline style",
    "Ordered list",
    "All plain HTML elements we need",
    "Style map defaults",
    "HTML entities escaping",
    "Same content multiple times",
]


def _blocks_match(expected, actual):
    """Compare blocks ignoring keys (which are randomly generated)."""
    if len(expected) != len(actual):
        return False, f"block count: expected {len(expected)}, got {len(actual)}"

    for i, (eb, ab) in enumerate(zip(expected, actual)):
        if eb["type"] != ab["type"]:
            return False, f"block {i} type: expected {eb['type']!r}, got {ab['type']!r}"
        if eb["text"] != ab["text"]:
            return False, f"block {i} text: expected {eb['text']!r}, got {ab['text']!r}"
        if eb.get("depth", 0) != ab.get("depth", 0):
            return (
                False,
                f"block {i} depth: expected {eb.get('depth', 0)}, got {ab.get('depth', 0)}",
            )

        exp_styles = sorted(
            eb.get("inlineStyleRanges", []),
            key=lambda s: (s["offset"], s["style"]),
        )
        got_styles = sorted(
            ab.get("inlineStyleRanges", []),
            key=lambda s: (s["offset"], s["style"]),
        )
        if exp_styles != got_styles:
            return False, f"block {i} styles: expected {exp_styles}, got {got_styles}"

        exp_er = eb.get("entityRanges", [])
        got_er = ab.get("entityRanges", [])
        if len(exp_er) != len(got_er):
            return (
                False,
                f"block {i} entity count: expected {len(exp_er)}, got {len(got_er)}",
            )
        for j, (ee, ge) in enumerate(zip(exp_er, got_er)):
            if ee["offset"] != ge["offset"] or ee["length"] != ge["length"]:
                return (
                    False,
                    f"block {i} entity {j}: expected off={ee['offset']} len={ee['length']}, got off={ge['offset']} len={ge['length']}",
                )

    return True, ""


class ImporterTestMeta(type):
    """Generates importer test cases from test_exports.json fixtures."""

    def __new__(mcs, name, bases, tests):
        for fixture in fixtures:
            label = fixture["label"]
            if label not in LOSSLESS_CASES:
                continue
            if "markdown" not in fixture["output"]:
                continue

            test_label = label.lower().replace(" ", "_")
            test_name = f"test_import_{test_label}"

            md = fixture["output"]["markdown"]
            expected = fixture["content_state"]

            def gen_test(markdown, content_state):
                def test(self):
                    result = markdown_to_content_state(markdown)
                    ok, msg = _blocks_match(content_state["blocks"], result["blocks"])
                    self.assertTrue(ok, msg)

                return test

            tests[test_name] = gen_test(md, expected)

        return type.__new__(mcs, name, bases, tests)


class TestImporter(unittest.TestCase, metaclass=ImporterTestMeta):
    """Tests that markdown input produces the expected content_state blocks."""


class TestImporterLossyEntityData(unittest.TestCase):
    """Tests for cases where entity data is partially lost in markdown.

    The markdown link syntax [text](url) only preserves the url, so extra
    entity data (title, rel, data-* attributes) is lost. These tests verify
    that the importer still reconstructs the correct block structure and
    entity offsets/lengths.
    """

    def test_import_entity_preserves_structure(self):
        fix = FIXTURES_BY_LABEL["Entity"]
        md = fix["output"]["markdown"]
        result = markdown_to_content_state(md)
        self.assertEqual(len(result["blocks"]), 1)
        block = result["blocks"][0]
        self.assertEqual(block["text"], "a")
        self.assertEqual(block["type"], "unstyled")
        self.assertEqual(len(block["entityRanges"]), 1)
        self.assertEqual(block["entityRanges"][0]["offset"], 0)
        self.assertEqual(block["entityRanges"][0]["length"], 1)
        self.assertEqual(
            sorted(block["inlineStyleRanges"], key=lambda s: s["offset"]),
            [{"offset": 0, "length": 1, "style": "ITALIC"}],
        )

    def test_import_entity_with_data_star_preserves_structure(self):
        fix = FIXTURES_BY_LABEL["Entity with data-*"]
        md = fix["output"]["markdown"]
        result = markdown_to_content_state(md)
        block = result["blocks"][0]
        self.assertEqual(block["text"], "a")
        entity_key = str(block["entityRanges"][0]["key"])
        self.assertEqual(result["entityMap"][entity_key]["data"], {"url": "/"})


class TestImporterDecoratorCases(unittest.TestCase):
    """Tests for cases where composite decorators add structure during export.

    For example, the linkify decorator auto-links URLs, creating link syntax
    in the markdown output that wasn't an entity in the original content_state.
    The importer correctly parses these as entities.
    """

    def test_import_multiple_decorators(self):
        fix = FIXTURES_BY_LABEL["Multiple decorators"]
        md = fix["output"]["markdown"]
        result = markdown_to_content_state(md)
        block = result["blocks"][0]
        # The original had no entities, but the linkify decorator created a link
        # in the markdown output. The importer correctly parses it as an entity.
        self.assertEqual(
            block["text"],
            "search http://www.google.com#world for the #world",
        )
        self.assertEqual(len(block["entityRanges"]), 1)
        er = block["entityRanges"][0]
        self.assertEqual(er["offset"], 7)
        self.assertEqual(er["length"], 27)
        entity_key = str(er["key"])
        self.assertEqual(
            result["entityMap"][entity_key]["data"]["url"],
            "http://www.google.com#world",
        )


class TestImporterBlockTypes(unittest.TestCase):
    """Direct tests for block types not covered by test_exports.json fixtures."""

    def test_horizontal_rule(self):
        result = markdown_to_content_state("---\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "atomic")
        self.assertEqual(block["text"], " ")
        entity = result["entityMap"][str(block["entityRanges"][0]["key"])]
        self.assertEqual(entity["type"], "HORIZONTAL_RULE")
        self.assertEqual(entity["mutability"], "IMMUTABLE")

    def test_image_with_alt(self):
        result = markdown_to_content_state(
            "![alt text](http://example.com/img.png)\n\n"
        )
        block = result["blocks"][0]
        self.assertEqual(block["type"], "atomic")
        self.assertEqual(block["text"], " ")
        entity = result["entityMap"][str(block["entityRanges"][0]["key"])]
        self.assertEqual(entity["type"], "IMAGE")
        self.assertEqual(entity["data"]["src"], "http://example.com/img.png")
        self.assertEqual(entity["data"]["alt"], "alt text")

    def test_image_without_alt(self):
        result = markdown_to_content_state("![](http://example.com/img.png)\n\n")
        entity = result["entityMap"][str(result["blocks"][0]["entityRanges"][0]["key"])]
        self.assertNotIn("alt", entity["data"])
        self.assertEqual(entity["data"]["src"], "http://example.com/img.png")

    def test_code_block(self):
        result = markdown_to_content_state("```\ndef foo():\n    pass\n```\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "code-block")
        self.assertEqual(block["text"], "def foo():\n    pass")
        self.assertEqual(block["inlineStyleRanges"], [])
        self.assertEqual(block["entityRanges"], [])

    def test_empty_code_block(self):
        result = markdown_to_content_state("```\n```\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "code-block")
        self.assertEqual(block["text"], "")

    def test_code_block_with_surrounding_blank_lines(self):
        result = markdown_to_content_state("```\n\ncontent\n\n```\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "code-block")
        self.assertEqual(block["text"], "\ncontent\n")

    def test_code_block_preserves_markdown_syntax(self):
        result = markdown_to_content_state(
            "```\n**not bold** [not a link](url)\n```\n\n"
        )
        block = result["blocks"][0]
        self.assertEqual(block["type"], "code-block")
        self.assertEqual(block["text"], "**not bold** [not a link](url)")
        self.assertEqual(block["inlineStyleRanges"], [])
        self.assertEqual(block["entityRanges"], [])

    def test_code_block_text_ending_with_newline(self):
        md = "```\ndef foo():\n    pass\n\n```\n\n"
        result = markdown_to_content_state(md)
        block = result["blocks"][0]
        self.assertEqual(block["type"], "code-block")
        self.assertEqual(block["text"], "def foo():\n    pass\n")

    def test_nested_unordered_list_depth(self):
        md = "- depth 0\n  - depth 1\n    - depth 2\n\n"
        result = markdown_to_content_state(md)
        depths = [b["depth"] for b in result["blocks"]]
        self.assertEqual(depths, [0, 1, 2])

    def test_nested_ordered_list_depth(self):
        md = "1. depth 0\n  1. depth 1\n    1. depth 2\n\n"
        result = markdown_to_content_state(md)
        depths = [b["depth"] for b in result["blocks"]]
        self.assertEqual(depths, [0, 1, 2])

    def test_list_item_with_soft_line_break(self):
        md = "- Convert line breaks to `<br>`\nelements.\n\n"
        result = markdown_to_content_state(md)
        self.assertEqual(len(result["blocks"]), 1)
        block = result["blocks"][0]
        self.assertEqual(block["type"], "unordered-list-item")
        self.assertEqual(block["text"], "Convert line breaks to <br>\nelements.")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 23, "length": 4, "style": "CODE"}],
        )

    def test_ordered_list_item_with_soft_line_break(self):
        md = "1. First line\nsecond line\n\n"
        result = markdown_to_content_state(md)
        self.assertEqual(len(result["blocks"]), 1)
        block = result["blocks"][0]
        self.assertEqual(block["type"], "ordered-list-item")
        self.assertEqual(block["text"], "First line\nsecond line")

    def test_blockquote_with_soft_line_break(self):
        md = "> First line\nsecond line\n\n"
        result = markdown_to_content_state(md)
        self.assertEqual(len(result["blocks"]), 1)
        block = result["blocks"][0]
        self.assertEqual(block["type"], "blockquote")
        self.assertEqual(block["text"], "First line\nsecond line")

    def test_blockquote(self):
        result = markdown_to_content_state("> quoted text\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "blockquote")
        self.assertEqual(block["text"], "quoted text")

    def test_heading_levels(self):
        for level in range(1, 7):
            prefix = "#" * level
            result = markdown_to_content_state(f"{prefix} Heading {level}\n\n")
            block = result["blocks"][0]
            self.assertEqual(
                block["type"],
                f"header-{['one', 'two', 'three', 'four', 'five', 'six'][level - 1]}",
            )
            self.assertEqual(block["text"], f"Heading {level}")


class TestImporterInlineStyles(unittest.TestCase):
    """Tests for each inline style marker individually."""

    def test_inline_code(self):
        result = markdown_to_content_state("hello `code` world\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello code world")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 6, "length": 4, "style": "CODE"}],
        )

    def test_inline_strikethrough(self):
        result = markdown_to_content_state("hello ~strike~ world\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello strike world")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 6, "length": 6, "style": "STRIKETHROUGH"}],
        )

    def test_multiple_different_styles(self):
        result = markdown_to_content_state("**bold** and _italic_ text\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "bold and italic text")
        styles = sorted(block["inlineStyleRanges"], key=lambda s: s["offset"])
        self.assertEqual(styles[0], {"offset": 0, "length": 4, "style": "BOLD"})
        self.assertEqual(styles[1], {"offset": 9, "length": 6, "style": "ITALIC"})

    def test_inline_styles_in_heading(self):
        result = markdown_to_content_state("## **bold** heading\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "header-two")
        self.assertEqual(block["text"], "bold heading")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 0, "length": 4, "style": "BOLD"}],
        )

    def test_underscore_inside_word_is_literal(self):
        result = markdown_to_content_state("some_variable_name\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "some_variable_name")
        self.assertEqual(block["inlineStyleRanges"], [])

    def test_underscore_in_url_is_literal(self):
        result = markdown_to_content_state(
            "[link](http://example.com/path_to/page)\n\n"
        )
        block = result["blocks"][0]
        self.assertEqual(block["text"], "link")
        entity = result["entityMap"][str(block["entityRanges"][0]["key"])]
        self.assertEqual(entity["data"]["url"], "http://example.com/path_to/page")

    def test_underscore_at_word_boundary_is_italic(self):
        result = markdown_to_content_state("hello _world_ test\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello world test")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 6, "length": 5, "style": "ITALIC"}],
        )

    def test_inline_styles_in_blockquote(self):
        result = markdown_to_content_state("> _italic_ quote\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "blockquote")
        self.assertEqual(block["text"], "italic quote")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 0, "length": 6, "style": "ITALIC"}],
        )

    def test_inline_styles_in_list_item(self):
        result = markdown_to_content_state("- **bold** item\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "unordered-list-item")
        self.assertEqual(block["text"], "bold item")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 0, "length": 4, "style": "BOLD"}],
        )


class TestImporterInlineHtmlTags(unittest.TestCase):
    """Tests for raw inline HTML tag parsing (non-Markdown styles)."""

    def test_underline_tag(self):
        result = markdown_to_content_state("hello <u>under</u> world\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello under world")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 6, "length": 5, "style": "UNDERLINE"}],
        )

    def test_superscript_tag(self):
        result = markdown_to_content_state("x<sup>2</sup> + y\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "x2 + y")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 1, "length": 1, "style": "SUPERSCRIPT"}],
        )

    def test_subscript_tag(self):
        result = markdown_to_content_state("H<sub>2</sub>O\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "H2O")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 1, "length": 1, "style": "SUBSCRIPT"}],
        )

    def test_mark_tag(self):
        result = markdown_to_content_state("hello <mark>world</mark>\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello world")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 6, "length": 5, "style": "MARK"}],
        )

    def test_quotation_tag(self):
        result = markdown_to_content_state("He said <q>hi</q>\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "He said hi")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 8, "length": 2, "style": "QUOTATION"}],
        )

    def test_small_tag(self):
        result = markdown_to_content_state("hello <small>world</small>\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello world")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 6, "length": 5, "style": "SMALL"}],
        )

    def test_sample_tag(self):
        result = markdown_to_content_state("hello <samp>world</samp>\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello world")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 6, "length": 5, "style": "SAMPLE"}],
        )

    def test_insert_tag(self):
        result = markdown_to_content_state("hello <ins>world</ins>\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello world")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 6, "length": 5, "style": "INSERT"}],
        )

    def test_delete_tag(self):
        result = markdown_to_content_state("hello <del>world</del>\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello world")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 6, "length": 5, "style": "DELETE"}],
        )

    def test_keyboard_tag(self):
        result = markdown_to_content_state("Press <kbd>Enter</kbd>\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "Press Enter")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 6, "length": 5, "style": "KEYBOARD"}],
        )

    def test_nested_html_tags(self):
        result = markdown_to_content_state("<u>under <mark>both</mark></u>\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "under both")
        styles = sorted(block["inlineStyleRanges"], key=lambda s: s["offset"])
        self.assertEqual(styles[0], {"offset": 0, "length": 10, "style": "UNDERLINE"})
        self.assertEqual(styles[1], {"offset": 6, "length": 4, "style": "MARK"})

    def test_html_tag_with_markdown_styles(self):
        result = markdown_to_content_state("**bold** <u>under</u> text\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "bold under text")
        styles = sorted(block["inlineStyleRanges"], key=lambda s: s["offset"])
        self.assertEqual(styles[0], {"offset": 0, "length": 4, "style": "BOLD"})
        self.assertEqual(styles[1], {"offset": 5, "length": 5, "style": "UNDERLINE"})

    def test_unknown_html_tag_is_literal(self):
        result = markdown_to_content_state("hello <unknown>tag</unknown>\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello <unknown>tag</unknown>")
        self.assertEqual(block["inlineStyleRanges"], [])

    def test_unmatched_closing_tag_is_literal(self):
        result = markdown_to_content_state("hello </u> world\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello </u> world")
        self.assertEqual(block["inlineStyleRanges"], [])

    def test_html_tags_in_heading(self):
        result = markdown_to_content_state("## <u>Underlined heading</u>\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "header-two")
        self.assertEqual(block["text"], "Underlined heading")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 0, "length": 18, "style": "UNDERLINE"}],
        )

    def test_html_tags_in_blockquote(self):
        result = markdown_to_content_state("> <u>Underlined quote</u>\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "blockquote")
        self.assertEqual(block["text"], "Underlined quote")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 0, "length": 16, "style": "UNDERLINE"}],
        )

    def test_html_tags_in_list_item(self):
        result = markdown_to_content_state("- <u>underlined item</u>\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "unordered-list-item")
        self.assertEqual(block["text"], "underlined item")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 0, "length": 15, "style": "UNDERLINE"}],
        )

    def test_empty_html_tag_pair(self):
        """Adjacent open+close HTML tags (e.g. <u></u>) produce no style range."""
        result = markdown_to_content_state("before<u></u>after\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "beforeafter")
        self.assertEqual(block["inlineStyleRanges"], [])


class TestImporterEscapes(unittest.TestCase):
    """Tests for backslash escape handling."""

    def test_escaped_star_is_literal(self):
        result = markdown_to_content_state("hello \\*world\\* text\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello *world* text")
        self.assertEqual(block["inlineStyleRanges"], [])

    def test_escaped_underscore_is_literal(self):
        result = markdown_to_content_state("hello \\_world\\_ text\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello _world_ text")
        self.assertEqual(block["inlineStyleRanges"], [])

    def test_escaped_backtick_is_literal(self):
        result = markdown_to_content_state("hello \\`code\\` text\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello `code` text")
        self.assertEqual(block["inlineStyleRanges"], [])

    def test_escaped_tilde_is_literal(self):
        result = markdown_to_content_state("hello \\~strike\\~ text\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello ~strike~ text")
        self.assertEqual(block["inlineStyleRanges"], [])

    def test_escaped_hash_is_literal(self):
        result = markdown_to_content_state("\\# Not a heading\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "unstyled")
        self.assertEqual(block["text"], "# Not a heading")

    def test_escaped_brackets_are_literal(self):
        result = markdown_to_content_state("\\[not a link\\](not a url)\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "[not a link](not a url)")
        self.assertEqual(block["entityRanges"], [])

    def test_escaped_backslash_is_literal(self):
        result = markdown_to_content_state("hello \\\\ world\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello \\ world")

    def test_unescaped_backslash_passthrough(self):
        result = markdown_to_content_state("hello \\n world\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello \\n world")

    def test_escape_at_end_of_string(self):
        result = markdown_to_content_state("text\\\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "text\\")


class TestImporterHorizontalRuleVariants(unittest.TestCase):
    """Tests for horizontal rule variants (---, ***, ___)."""

    def test_hr_dashes(self):
        result = markdown_to_content_state("---\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "atomic")
        entity = result["entityMap"][str(block["entityRanges"][0]["key"])]
        self.assertEqual(entity["type"], "HORIZONTAL_RULE")

    def test_hr_asterisks(self):
        result = markdown_to_content_state("***\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "atomic")
        entity = result["entityMap"][str(block["entityRanges"][0]["key"])]
        self.assertEqual(entity["type"], "HORIZONTAL_RULE")

    def test_hr_underscores(self):
        result = markdown_to_content_state("___\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "atomic")
        entity = result["entityMap"][str(block["entityRanges"][0]["key"])]
        self.assertEqual(entity["type"], "HORIZONTAL_RULE")


class TestImporterLinkTitles(unittest.TestCase):
    """Tests for link title attribute parsing."""

    def test_link_with_double_quoted_title(self):
        result = markdown_to_content_state('[link](http://example.com "My Title")\n\n')
        block = result["blocks"][0]
        entity = result["entityMap"][str(block["entityRanges"][0]["key"])]
        self.assertEqual(entity["data"]["url"], "http://example.com")
        self.assertEqual(entity["data"]["title"], "My Title")

    def test_link_with_single_quoted_title(self):
        result = markdown_to_content_state("[link](http://example.com 'My Title')\n\n")
        block = result["blocks"][0]
        entity = result["entityMap"][str(block["entityRanges"][0]["key"])]
        self.assertEqual(entity["data"]["url"], "http://example.com")
        self.assertEqual(entity["data"]["title"], "My Title")

    def test_link_without_title(self):
        result = markdown_to_content_state("[link](http://example.com)\n\n")
        block = result["blocks"][0]
        entity = result["entityMap"][str(block["entityRanges"][0]["key"])]
        self.assertEqual(entity["data"]["url"], "http://example.com")
        self.assertNotIn("title", entity["data"])

    def test_link_with_title_and_special_chars_in_url(self):
        result = markdown_to_content_state(
            '[link](http://example.com/path?a=1&b=2 "Title")\n\n'
        )
        block = result["blocks"][0]
        entity = result["entityMap"][str(block["entityRanges"][0]["key"])]
        self.assertEqual(entity["data"]["url"], "http://example.com/path?a=1&b=2")
        self.assertEqual(entity["data"]["title"], "Title")


class TestImporterCodeFenceVariants(unittest.TestCase):
    """Tests for code fence handling (info strings, ~~~ fences)."""

    def test_code_block_with_info_string(self):
        result = markdown_to_content_state("```python\ndef foo():\n    pass\n```\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "code-block")
        self.assertEqual(block["text"], "def foo():\n    pass")

    def test_tilde_code_fence(self):
        result = markdown_to_content_state("~~~\ncode\n~~~\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "code-block")
        self.assertEqual(block["text"], "code")

    def test_tilde_code_fence_with_info_string(self):
        result = markdown_to_content_state("~~~python\ncode\n~~~\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "code-block")
        self.assertEqual(block["text"], "code")

    def test_empty_code_block_with_info_string(self):
        result = markdown_to_content_state("```python\n```\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["type"], "code-block")
        self.assertEqual(block["text"], "")


class TestImporterMultiLineBlockquotes(unittest.TestCase):
    """Tests for multi-line blockquote handling."""

    def test_two_line_blockquote(self):
        result = markdown_to_content_state("> Line one\n> Line two\n\n")
        blocks = result["blocks"]
        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        self.assertEqual(block["type"], "blockquote")
        self.assertEqual(block["text"], "Line one\nLine two")

    def test_three_line_blockquote(self):
        result = markdown_to_content_state("> First\n> Second\n> Third\n\n")
        blocks = result["blocks"]
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["text"], "First\nSecond\nThird")

    def test_blockquote_with_inline_style_across_lines(self):
        result = markdown_to_content_state("> **bold** line one\n> line two\n\n")
        blocks = result["blocks"]
        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        self.assertEqual(block["type"], "blockquote")
        self.assertEqual(block["text"], "bold line one\nline two")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 0, "length": 4, "style": "BOLD"}],
        )


class TestImporterInlineEdgeCases(unittest.TestCase):
    """Tests for inline parsing edge cases."""

    def test_bracket_not_followed_by_paren(self):
        """A [bracket] without (url) should be treated as plain text."""
        result = markdown_to_content_state("[not a link] here\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "[not a link] here")
        self.assertEqual(block["entityRanges"], [])

    def test_nested_brackets_in_link(self):
        result = markdown_to_content_state("[text [inner]](http://example.com)\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "text [inner]")
        self.assertEqual(len(block["entityRanges"]), 1)

    def test_nested_parens_in_url(self):
        result = markdown_to_content_state("[link](http://example.com/path_(test))\n\n")
        block = result["blocks"][0]
        entity = result["entityMap"][str(block["entityRanges"][0]["key"])]
        self.assertEqual(entity["data"]["url"], "http://example.com/path_(test)")

    def test_empty_style_markers_ignored(self):
        """Adjacent open+close markers (e.g. ****) with no content produce no style range."""
        result = markdown_to_content_state("before****after\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "beforeafter")
        self.assertEqual(block["inlineStyleRanges"], [])

    def test_non_adjacent_same_style_ranges(self):
        result = markdown_to_content_state("**one** middle **two**\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "one middle two")
        styles = sorted(block["inlineStyleRanges"], key=lambda s: s["offset"])
        self.assertEqual(len(styles), 2)
        self.assertEqual(styles[0], {"offset": 0, "length": 3, "style": "BOLD"})
        self.assertEqual(styles[1], {"offset": 11, "length": 3, "style": "BOLD"})

    def test_link_with_inner_styles(self):
        result = markdown_to_content_state("[**bold link**](http://example.com)\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "bold link")
        self.assertEqual(len(block["entityRanges"]), 1)
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 0, "length": 9, "style": "BOLD"}],
        )

    def test_nested_link_in_link_text(self):
        """A link whose text contains another link produces two entities."""
        result = markdown_to_content_state(
            "[before [inner](http://inner.com) after](http://outer.com)\n\n"
        )
        block = result["blocks"][0]
        self.assertEqual(block["text"], "before inner after")
        self.assertEqual(len(block["entityRanges"]), 2)
        # Outer link covers everything.
        outer = block["entityRanges"][0]
        self.assertEqual(outer["offset"], 0)
        self.assertEqual(outer["length"], 18)
        self.assertEqual(
            result["entityMap"][str(outer["key"])]["data"]["url"],
            "http://outer.com",
        )
        # Inner link covers just "inner".
        inner = block["entityRanges"][1]
        self.assertEqual(inner["offset"], 7)
        self.assertEqual(inner["length"], 5)
        self.assertEqual(
            result["entityMap"][str(inner["key"])]["data"]["url"],
            "http://inner.com",
        )


class TestImporterMultiBlock(unittest.TestCase):
    """Tests for multi-block documents with mixed block types."""

    def test_mixed_blocks(self):
        md = "# Title\n\nParagraph\n\n> Quote\n\n- Item\n\n---\n\n"
        result = markdown_to_content_state(md)
        types = [b["type"] for b in result["blocks"]]
        self.assertEqual(
            types,
            [
                "header-one",
                "unstyled",
                "blockquote",
                "unordered-list-item",
                "atomic",
            ],
        )

    def test_code_block_between_paragraphs(self):
        md = "Before\n\n```\ncode\n```\n\nAfter\n\n"
        result = markdown_to_content_state(md)
        self.assertEqual(
            [(b["type"], b["text"]) for b in result["blocks"]],
            [("unstyled", "Before"), ("code-block", "code"), ("unstyled", "After")],
        )

    def test_entity_counter_across_blocks(self):
        md = "[a](http://a.com)\n\n[b](http://b.com)\n\n"
        result = markdown_to_content_state(md)
        keys = [b["entityRanges"][0]["key"] for b in result["blocks"]]
        self.assertEqual(keys[0], 0)
        self.assertEqual(keys[1], 1)
        self.assertEqual(result["entityMap"]["0"]["data"]["url"], "http://a.com")
        self.assertEqual(result["entityMap"]["1"]["data"]["url"], "http://b.com")

    def test_empty_input(self):
        result = markdown_to_content_state("")
        self.assertEqual(result["blocks"], [])
        self.assertEqual(result["entityMap"], {})

    def test_whitespace_only_input(self):
        result = markdown_to_content_state("\n\n\n")
        self.assertEqual(result["blocks"], [])
        self.assertEqual(result["entityMap"], {})

    def test_input_without_trailing_newlines(self):
        result = markdown_to_content_state("hello")
        self.assertEqual(len(result["blocks"]), 1)
        self.assertEqual(result["blocks"][0]["text"], "hello")
        self.assertEqual(result["blocks"][0]["type"], "unstyled")

    def test_consecutive_lines_joined_as_paragraph(self):
        md = "This is a long\nparagraph across\nmultiple lines\n\n"
        result = markdown_to_content_state(md)
        self.assertEqual(len(result["blocks"]), 1)
        self.assertEqual(
            result["blocks"][0]["text"],
            "This is a long paragraph across multiple lines",
        )
        self.assertEqual(result["blocks"][0]["type"], "unstyled")

    def test_consecutive_lines_separated_by_block_level(self):
        md = "First para\nstill first\n\n# Heading\n\nSecond para\nstill second\n\n"
        result = markdown_to_content_state(md)
        self.assertEqual(
            [(b["type"], b["text"]) for b in result["blocks"]],
            [
                ("unstyled", "First para still first"),
                ("header-one", "Heading"),
                ("unstyled", "Second para still second"),
            ],
        )

    def test_paragraph_before_code_block(self):
        md = "First line\nsecond line\n\n```\ncode\n```\n\n"
        result = markdown_to_content_state(md)
        self.assertEqual(
            [(b["type"], b["text"]) for b in result["blocks"]],
            [("unstyled", "First line second line"), ("code-block", "code")],
        )


class TestImporterDirectRoundTrip(unittest.TestCase):
    """Round-trip tests for block types not covered by test_exports.json fixtures."""

    exporter = HTML(MARKDOWN_CONFIG)

    def _roundtrip(self, md: str) -> None:
        content_state = markdown_to_content_state(md)
        re_exported = self.exporter.render(content_state)
        self.assertEqual(re_exported, md)

    def test_roundtrip_horizontal_rule(self):
        self._roundtrip("---\n\n")

    def test_roundtrip_image_with_alt(self):
        self._roundtrip("![alt text](http://example.com/img.png)\n\n")

    def test_roundtrip_image_without_alt(self):
        self._roundtrip("![](http://example.com/img.png)\n\n")

    def test_roundtrip_code_block(self):
        self._roundtrip("```\ndef foo():\n    pass\n```\n\n")

    def test_roundtrip_empty_code_block(self):
        self._roundtrip("```\n\n```\n\n")

    def test_roundtrip_blockquote(self):
        self._roundtrip("> quoted text\n\n")

    def test_roundtrip_heading(self):
        for level in range(1, 7):
            prefix = "#" * level
            self._roundtrip(f"{prefix} Heading\n\n")

    def test_roundtrip_nested_unordered_list(self):
        self._roundtrip("- depth 0\n  - depth 1\n    - depth 2\n\n")

    def test_roundtrip_nested_ordered_list(self):
        self._roundtrip("1. depth 0\n  1. depth 1\n    1. depth 2\n\n")

    def test_roundtrip_inline_code(self):
        self._roundtrip("hello `code` world\n\n")

    def test_roundtrip_inline_strikethrough(self):
        self._roundtrip("hello ~strike~ world\n\n")

    def test_roundtrip_link(self):
        self._roundtrip("[link text](http://example.com)\n\n")

    def test_roundtrip_mixed_document(self):
        self._roundtrip(
            "# Title\n\n"
            "A paragraph with **bold** and _italic_ text.\n\n"
            "> A blockquote\n\n"
            "- Item one\n- Item two\n\n"
            "1. First\n2. Second\n\n"
            "---\n\n"
        )


class RoundTripTestMeta(type):
    """Generates exporter -> importer -> exporter round-trip test cases."""

    def __new__(mcs, name, bases, tests):
        exporter = HTML(MARKDOWN_CONFIG)

        for fixture in fixtures:
            label = fixture["label"]
            if label not in LOSSLESS_CASES:
                continue
            if "markdown" not in fixture["output"]:
                continue

            test_label = label.lower().replace(" ", "_")
            test_name = f"test_roundtrip_{test_label}"

            md = fixture["output"]["markdown"]

            def gen_test(markdown, html_exporter):
                def test(self):
                    # Import the markdown.
                    content_state = markdown_to_content_state(markdown)
                    # Re-export to markdown.
                    re_exported = html_exporter.render(content_state)
                    self.assertEqual(re_exported, markdown)

                return test

            tests[test_name] = gen_test(md, exporter)

        return type.__new__(mcs, name, bases, tests)


class TestRoundTrip(unittest.TestCase, metaclass=RoundTripTestMeta):
    """Tests that export -> import -> export produces identical markdown."""


class TestImporterConfigurableMarkers(unittest.TestCase):
    """Tests for configurable style markers via MarkdownImporterOptions."""

    def test_custom_bold_marker(self):
        result = markdown_to_content_state("__bold__ text\n\n", {"bold": "__"})
        block = result["blocks"][0]
        self.assertEqual(block["text"], "bold text")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 0, "length": 4, "style": "BOLD"}],
        )

    def test_custom_italic_marker(self):
        result = markdown_to_content_state("*italic* text\n\n", {"italic": "*"})
        block = result["blocks"][0]
        self.assertEqual(block["text"], "italic text")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 0, "length": 6, "style": "ITALIC"}],
        )

    def test_custom_strikethrough_marker(self):
        result = markdown_to_content_state(
            "~~strike~~ text\n\n", {"strikethrough": "~~"}
        )
        block = result["blocks"][0]
        self.assertEqual(block["text"], "strike text")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 0, "length": 6, "style": "STRIKETHROUGH"}],
        )

    def test_custom_bold_and_italic_markers(self):
        result = markdown_to_content_state(
            "__bold__ and *italic*\n\n",
            {"bold": "__", "italic": "*"},
        )
        block = result["blocks"][0]
        self.assertEqual(block["text"], "bold and italic")
        styles = sorted(block["inlineStyleRanges"], key=lambda s: s["offset"])
        self.assertEqual(styles[0], {"offset": 0, "length": 4, "style": "BOLD"})
        self.assertEqual(styles[1], {"offset": 9, "length": 6, "style": "ITALIC"})

    def test_default_markers_still_work_without_options(self):
        result = markdown_to_content_state("**bold** _italic_\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "bold italic")
        styles = sorted(block["inlineStyleRanges"], key=lambda s: s["offset"])
        self.assertEqual(styles[0], {"offset": 0, "length": 4, "style": "BOLD"})
        self.assertEqual(styles[1], {"offset": 5, "length": 6, "style": "ITALIC"})

    def test_round_trip_with_custom_bold(self):
        exporter = HTML(build_markdown_config({"bold": "__"}))
        md = "__bold__ text\n\n"
        cs = markdown_to_content_state(md, {"bold": "__"})
        re_exported = exporter.render(cs)
        self.assertEqual(re_exported, md)

    def test_round_trip_with_custom_italic(self):
        exporter = HTML(build_markdown_config({"italic": "*"}))
        md = "*italic* text\n\n"
        cs = markdown_to_content_state(md, {"italic": "*"})
        re_exported = exporter.render(cs)
        self.assertEqual(re_exported, md)

    def test_round_trip_with_custom_strikethrough(self):
        exporter = HTML(build_markdown_config({"strikethrough": "~~"}))
        md = "~~strike~~ text\n\n"
        cs = markdown_to_content_state(md, {"strikethrough": "~~"})
        re_exported = exporter.render(cs)
        self.assertEqual(re_exported, md)


class TestImporterCustomHtmlTags(unittest.TestCase):
    """Tests for custom HTML tag mappings via MarkdownImporterOptions."""

    def test_custom_html_tag_mapping(self):
        result = markdown_to_content_state(
            "hello <custom>tag</custom>\n\n",
            {"html_style_tags": {"custom": "CUSTOM"}},
        )
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello tag")
        self.assertEqual(
            block["inlineStyleRanges"],
            [{"offset": 6, "length": 3, "style": "CUSTOM"}],
        )

    def test_custom_html_tag_extends_defaults(self):
        result = markdown_to_content_state(
            "<u>under</u> and <custom>tag</custom>\n\n",
            {"html_style_tags": {"custom": "CUSTOM"}},
        )
        block = result["blocks"][0]
        self.assertEqual(block["text"], "under and tag")
        styles = sorted(block["inlineStyleRanges"], key=lambda s: s["offset"])
        self.assertEqual(styles[0], {"offset": 0, "length": 5, "style": "UNDERLINE"})
        self.assertEqual(styles[1], {"offset": 10, "length": 3, "style": "CUSTOM"})

    def test_unknown_tag_without_mapping_is_literal(self):
        result = markdown_to_content_state("hello <unknown>tag</unknown>\n\n")
        block = result["blocks"][0]
        self.assertEqual(block["text"], "hello <unknown>tag</unknown>")
        self.assertEqual(block["inlineStyleRanges"], [])


class TestImporterOrderedListItemDelimiters(unittest.TestCase):
    """Tests for ordered list with ) delimiter."""

    def test_ordered_list_with_paren_delimiter(self):
        result = markdown_to_content_state("1) First\n2) Second\n\n")
        blocks = result["blocks"]
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["type"], "ordered-list-item")
        self.assertEqual(blocks[0]["text"], "First")
        self.assertEqual(blocks[1]["type"], "ordered-list-item")
        self.assertEqual(blocks[1]["text"], "Second")


class TestImporterPublicAPI(unittest.TestCase):
    """Tests that the importer is accessible from the top-level package."""

    def test_import_from_top_level(self):
        from draftjs_exporter import markdown_to_content_state as top_level_fn

        result = top_level_fn("hello\n\n")
        self.assertEqual(len(result["blocks"]), 1)
        self.assertEqual(result["blocks"][0]["text"], "hello")

    def test_import_options_from_top_level(self):
        from draftjs_exporter import MarkdownImporterOptions as Options

        opts: Options = {"bold": "__"}
        result = markdown_to_content_state("__bold__\n\n", opts)
        self.assertEqual(
            result["blocks"][0]["inlineStyleRanges"],
            [{"offset": 0, "length": 4, "style": "BOLD"}],
        )


if __name__ == "__main__":
    unittest.main()
