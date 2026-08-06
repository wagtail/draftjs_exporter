import json
import os
import unittest
from typing import Any

from draftjs_exporter.markdown_importer import ImporterConfig, MarkdownImporter
from draftjs_exporter.markdown_parser import scheme_resolver
from draftjs_exporter.types import ContentState

fixtures_path = os.path.join(os.path.dirname(__file__), "test_exports.json")
with open(fixtures_path) as f:
    export_fixtures = json.loads(f.read())

imports_path = os.path.join(os.path.dirname(__file__), "test_imports.json")
with open(imports_path) as f:
    import_fixtures = json.loads(f.read())

# Tags the Markdown exporter emits as inline HTML fallback (see the
# exporter's markdown fallbacks module). Whitelisting them lets most
# styles round-trip.
ROUNDTRIP_INLINE_HTML_STYLES = {
    "u": "UNDERLINE",
    "sup": "SUPERSCRIPT",
    "sub": "SUBSCRIPT",
    "mark": "MARK",
    "q": "QUOTATION",
    "small": "SMALL",
    "samp": "SAMPLE",
    "ins": "INSERT",
    "del": "DELETE",
    "kbd": "KEYBOARD",
}


def make_importer() -> MarkdownImporter:
    """Build the importer used for round-trip snapshot tests."""
    return MarkdownImporter(
        {
            "parser_config": {
                "inline_html_styles": ROUNDTRIP_INLINE_HTML_STYLES,
            }
        }
    )


def normalize(content_state: ContentState) -> dict[str, Any]:
    """Rewrite block and entity keys for deterministic comparison.

    Block keys become sequential; entity keys are remapped in order of
    first appearance in entity ranges, and the entity map is rebuilt
    to match.
    """
    entity_map = content_state.get("entityMap", {})
    key_map: dict[str, str] = {}
    blocks = []
    for index, block in enumerate(content_state.get("blocks", [])):
        ranges = []
        for entity_range in block.get("entityRanges", []):
            old_key = str(entity_range["key"])
            if old_key not in key_map:
                key_map[old_key] = str(len(key_map))
            ranges.append({**entity_range, "key": int(key_map[old_key])})
        # Sort ranges canonically: Draft.js does not require a specific
        # order, and the exporter emits ranges in style-application order
        # while the importer emits them in source order.
        styles = sorted(
            block.get("inlineStyleRanges", []),
            key=lambda r: (r["offset"], r["length"], r["style"]),
        )
        ranges.sort(key=lambda r: (r["offset"], r["length"], r["key"]))
        blocks.append(
            {
                "key": f"{index:05d}",
                "text": block.get("text", ""),
                "type": block.get("type", "unstyled"),
                "depth": block.get("depth", 0),
                "inlineStyleRanges": styles,
                "entityRanges": ranges,
                **({"data": block["data"]} if block.get("data") else {}),
            }
        )
    new_map = {}
    for old_key, new_key in key_map.items():
        if old_key in entity_map:
            new_map[new_key] = entity_map[old_key]
    return {"blocks": blocks, "entityMap": new_map}


def build_fixture_importer(fixture: dict[str, Any]) -> MarkdownImporter:
    """Build an importer for a direct-import fixture, expanding shorthands."""
    config = dict(fixture.get("config", {}))
    if config.pop("wagtail_resolvers", False):
        config["parser_config"] = {
            **config.get("parser_config", {}),
            "link_resolvers": [
                scheme_resolver(
                    "wagtail",
                    {"page": "LINK", "document": "DOCUMENT"},
                    coerce={"id": int},
                )
            ],
            "image_resolvers": [
                scheme_resolver(
                    "wagtail",
                    {"image": "IMAGE", "media": "EMBED"},
                    coerce={"id": int},
                    label_key="alt",
                    mutability="IMMUTABLE",
                )
            ],
        }
    return MarkdownImporter(ImporterConfig(**config))


class TestRoundTrip(unittest.TestCase):
    """Import the recorded Markdown output of every export fixture."""

    def test_round_trip(self) -> None:
        importer = make_importer()
        for fixture in export_fixtures:
            markdown = fixture["output"]["markdown"]
            expected = fixture.get("import", fixture["content_state"])
            with self.subTest(fixture=fixture["label"]):
                self.assertEqual(
                    normalize(importer.import_markdown(markdown)),
                    normalize(expected),
                )


class TestDirectImports(unittest.TestCase):
    """Import hand-written Markdown covering importer-only behavior."""

    def test_imports(self) -> None:
        for fixture in import_fixtures:
            importer = build_fixture_importer(fixture)
            with self.subTest(fixture=fixture["label"]):
                self.assertEqual(
                    normalize(importer.import_markdown(fixture["markdown"])),
                    normalize(fixture["content_state"]),
                )


class TestEscapingRoundTrip(unittest.TestCase):
    """Escaped Markdown forms the exporter emits must re-import as text.

    These cases mirror ``draftjs_exporter.markdown.escape`` output so the
    escaping round-trip contract is exercised directly, independent of the
    export snapshot fixtures.
    """

    def test_round_trip(self) -> None:
        importer = make_importer()
        # Each entry is (escaped Markdown, expected plain text). The Markdown
        # is what the exporter emits for the text on the right.
        cases = [
            # Anywhere escapes.
            (r"\*not emphasis\*", "*not emphasis*"),
            (r"\`d\`", "`d`"),
            (r"\[c\]", "[c]"),
            (r"\<b\>", "<b>"),
            # Backslash escape of a backslash.
            (r"a\\b", r"a\b"),
            # Line-start escapes.
            (r"\# Not a heading", "# Not a heading"),
            (r"\- not a list item", "- not a list item"),
            (r"1\. not a list item", "1. not a list item"),
            (r"\> not a quote", "> not a quote"),
            (r"\===foo", "===foo"),
            (r"\~ not a fence", "~ not a fence"),
            (r"\+ not a list item", "+ not a list item"),
        ]
        for markdown, expected in cases:
            with self.subTest(markdown=markdown):
                blocks = importer.import_markdown(markdown)["blocks"]
                self.assertEqual(len(blocks), 1)
                self.assertEqual(blocks[0]["type"], "unstyled")
                self.assertEqual(blocks[0]["inlineStyleRanges"], [])
                self.assertEqual(blocks[0]["entityRanges"], [])
                self.assertEqual(blocks[0]["text"], expected)

    def test_sized_code_spans(self) -> None:
        """Sized code span delimiters round-trip to a CODE range."""
        importer = make_importer()
        # (markdown, expected text) for code spans the exporter emits.
        cases = [
            ("``a`b``", "a`b"),
            ("`` ` ``", "`"),
            ("`code`", "code"),
        ]
        for markdown, expected in cases:
            with self.subTest(markdown=markdown):
                block = importer.import_markdown(markdown)["blocks"][0]
                self.assertEqual(block["type"], "unstyled")
                self.assertEqual(block["text"], expected)
                self.assertEqual(
                    block["inlineStyleRanges"],
                    [{"offset": 0, "length": len(expected), "style": "CODE"}],
                )
                self.assertEqual(block["entityRanges"], [])
