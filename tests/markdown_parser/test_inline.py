"""Tests for inline Markdown parsing."""

import unittest
from typing import Any

from draftjs_exporter.markdown_parser.builder import ContentStateBuilder
from draftjs_exporter.markdown_parser.inline import InlineParser


def make_parser(**overrides: Any) -> InlineParser:
    """Build an InlineParser with all constructs enabled."""
    config: dict[str, Any] = {
        "emphasis": True,
        "code_inline": True,
        "links": True,
        "images": True,
        "line_breaks": True,
        "inline_html_styles": {},
        "link_resolvers": [],
        "image_resolvers": [],
        "builder": ContentStateBuilder(),
    }
    config.update(overrides)
    return InlineParser(**config)


class TestPlainText(unittest.TestCase):
    def test_plain_text_passes_through(self):
        text, styles, entities = make_parser().parse("hello world")
        self.assertEqual(text, "hello world")
        self.assertEqual(styles, [])
        self.assertEqual(entities, [])


class TestEscapes(unittest.TestCase):
    def test_escaped_char_is_literal(self):
        text, styles, _ = make_parser().parse(r"\*not italic\*")
        self.assertEqual(text, "*not italic*")
        self.assertEqual(styles, [])

    def test_backslash_before_non_escapable_is_literal(self):
        text, _, _ = make_parser().parse(r"\a")
        self.assertEqual(text, r"\a")

    def test_line_start_equals_escape_inverts_exporter(self):
        # The exporter escapes a leading '=' so it is not read as Setext.
        text, _, _ = make_parser().parse(r"\===foo")
        self.assertEqual(text, "===foo")

    def test_line_start_tilde_escape_inverts_exporter(self):
        # The exporter escapes a leading '~' so it is not read as a fence.
        text, _, _ = make_parser().parse(r"\~foo")
        self.assertEqual(text, "~foo")

    def test_full_commonmark_punctuation_set(self):
        # Every ASCII punctuation char is backslash-escapable per CommonMark.
        punctuation = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
        for ch in punctuation:
            with self.subTest(ch=ch):
                text, _, _ = make_parser().parse(f"\\{ch}")
                self.assertEqual(text, ch)

    def test_backslash_before_non_ascii_is_literal(self):
        text, _, _ = make_parser().parse(r"\é")
        self.assertEqual(text, r"\é")


class TestCodeSpans(unittest.TestCase):
    def test_code_span(self):
        text, styles, _ = make_parser().parse("a `bc` d")
        self.assertEqual(text, "a bc d")
        self.assertEqual(styles, [{"offset": 2, "length": 2, "style": "CODE"}])

    def test_code_span_contents_are_literal(self):
        text, styles, _ = make_parser().parse("`**not bold**`")
        self.assertEqual(text, "**not bold**")
        self.assertEqual(styles, [{"offset": 0, "length": 12, "style": "CODE"}])

    def test_unmatched_backtick_is_literal(self):
        text, styles, _ = make_parser().parse("a `b")
        self.assertEqual(text, "a `b")
        self.assertEqual(styles, [])

    def test_code_disabled(self):
        text, styles, _ = make_parser(code_inline=False).parse("`x`")
        self.assertEqual(text, "`x`")
        self.assertEqual(styles, [])

    def test_sized_delimiters_for_backtick_content(self):
        # Round-trips the exporter's `` ``a`b`` `` output for a code span
        # whose content contains a backtick.
        text, styles, _ = make_parser().parse("``a`b``")
        self.assertEqual(text, "a`b")
        self.assertEqual(styles, [{"offset": 0, "length": 3, "style": "CODE"}])

    def test_sized_delimiters_with_space_padding(self):
        # Content that is a single backtick: exporter pads with spaces and
        # sizes delimiters to two backticks. CommonMark strips the padding.
        text, styles, _ = make_parser().parse("`` ` ``")
        self.assertEqual(text, "`")
        self.assertEqual(styles, [{"offset": 0, "length": 1, "style": "CODE"}])

    def test_code_span_strips_padded_spaces(self):
        # CommonMark strips one leading/trailing space when the span both
        # begins and ends with a space and is not all spaces.
        text, styles, _ = make_parser().parse("` hi `")
        self.assertEqual(text, "hi")
        self.assertEqual(styles, [{"offset": 0, "length": 2, "style": "CODE"}])

    def test_all_spaces_code_span_not_stripped(self):
        text, styles, _ = make_parser().parse("`  `")
        self.assertEqual(text, "  ")
        self.assertEqual(styles, [{"offset": 0, "length": 2, "style": "CODE"}])

    def test_longer_closer_run_does_not_close_shorter_opener(self):
        # A three-backtick run cannot close a two-backtick opener.
        text, styles, _ = make_parser().parse("``a```")
        self.assertEqual(text, "``a```")
        self.assertEqual(styles, [])

    def test_unmatched_sized_opener_is_literal(self):
        text, styles, _ = make_parser().parse("``a")
        self.assertEqual(text, "``a")
        self.assertEqual(styles, [])


class TestHardBreaks(unittest.TestCase):
    def test_two_spaces_before_newline_are_stripped(self):
        text, _, _ = make_parser().parse("a  \nb")
        self.assertEqual(text, "a\nb")

    def test_soft_break_kept(self):
        text, _, _ = make_parser().parse("a\nb")
        self.assertEqual(text, "a\nb")

    def test_single_trailing_space_kept(self):
        text, _, _ = make_parser().parse("a \nb")
        self.assertEqual(text, "a \nb")


class TestEmphasis(unittest.TestCase):
    def test_italic_star(self):
        text, styles, _ = make_parser().parse("a *b* c")
        self.assertEqual(text, "a b c")
        self.assertEqual(styles, [{"offset": 2, "length": 1, "style": "ITALIC"}])

    def test_italic_underscore(self):
        text, styles, _ = make_parser().parse("_b_")
        self.assertEqual(styles, [{"offset": 0, "length": 1, "style": "ITALIC"}])

    def test_bold_stars(self):
        text, styles, _ = make_parser().parse("**bold**")
        self.assertEqual(text, "bold")
        self.assertEqual(styles, [{"offset": 0, "length": 4, "style": "BOLD"}])

    def test_bold_underscores(self):
        text, styles, _ = make_parser().parse("__bold__")
        self.assertEqual(styles, [{"offset": 0, "length": 4, "style": "BOLD"}])

    def test_bold_italic_triple(self):
        text, styles, _ = make_parser().parse("***both***")
        self.assertEqual(text, "both")
        self.assertEqual(
            styles,
            [
                {"offset": 0, "length": 4, "style": "BOLD"},
                {"offset": 0, "length": 4, "style": "ITALIC"},
            ],
        )

    def test_nested_italic_in_bold(self):
        text, styles, _ = make_parser().parse("**a *b* c**")
        self.assertEqual(text, "a b c")
        self.assertEqual(
            styles,
            [
                {"offset": 0, "length": 5, "style": "BOLD"},
                {"offset": 2, "length": 1, "style": "ITALIC"},
            ],
        )

    def test_bold_inside_italic(self):
        text, styles, _ = make_parser().parse("*a **b** c*")
        self.assertEqual(text, "a b c")
        self.assertIn({"offset": 0, "length": 5, "style": "ITALIC"}, styles)
        self.assertIn({"offset": 2, "length": 1, "style": "BOLD"}, styles)

    def test_unmatched_delimiter_is_literal(self):
        text, styles, _ = make_parser().parse("a *b")
        self.assertEqual(text, "a *b")
        self.assertEqual(styles, [])

    def test_mismatched_run_length_partially_matches(self):
        # Per CommonMark, `**a*` is a literal star followed by emphasis:
        # the second opener star pairs with the trailing star.
        text, styles, _ = make_parser().parse("**a*")
        self.assertEqual(text, "*a")
        self.assertEqual(styles, [{"offset": 1, "length": 1, "style": "ITALIC"}])

    def test_run_longer_than_three_is_literal(self):
        text, styles, _ = make_parser().parse("****a****")
        self.assertEqual(text, "****a****")
        self.assertEqual(styles, [])

    def test_offsets_after_emphasis(self):
        text, styles, _ = make_parser().parse("**b** x *i*")
        self.assertEqual(text, "b x i")
        self.assertEqual(
            styles,
            [
                {"offset": 0, "length": 1, "style": "BOLD"},
                {"offset": 4, "length": 1, "style": "ITALIC"},
            ],
        )

    def test_emphasis_disabled(self):
        text, styles, _ = make_parser(emphasis=False).parse("**a**")
        self.assertEqual(text, "**a**")
        self.assertEqual(styles, [])


def parse_with_builder(**overrides: Any) -> tuple[InlineParser, ContentStateBuilder]:
    """Build a parser with a fresh builder, returning both."""
    builder = ContentStateBuilder()
    parser = make_parser(builder=builder, **overrides)
    return parser, builder


class TestLinks(unittest.TestCase):
    def test_simple_link(self):
        parser, builder = parse_with_builder()
        text, styles, entities = parser.parse("[example](https://example.com)")
        self.assertEqual(text, "example")
        self.assertEqual(styles, [])
        self.assertEqual(entities, [{"offset": 0, "length": 7, "key": 0}])
        self.assertEqual(
            builder.entity_map["0"],
            {
                "type": "LINK",
                "mutability": "MUTABLE",
                "data": {"url": "https://example.com"},
            },
        )

    def test_link_with_styled_label(self):
        parser, builder = parse_with_builder()
        text, styles, entities = parser.parse("[**bold**](/url)")
        self.assertEqual(text, "bold")
        self.assertEqual(styles, [{"offset": 0, "length": 4, "style": "BOLD"}])
        self.assertEqual(entities, [{"offset": 0, "length": 4, "key": 0}])

    def test_link_offsets_in_text(self):
        parser, builder = parse_with_builder()
        text, _, entities = parser.parse("see [docs](/d) now")
        self.assertEqual(text, "see docs now")
        self.assertEqual(entities, [{"offset": 4, "length": 4, "key": 0}])

    def test_links_disabled(self):
        parser, builder = parse_with_builder(links=False)
        text, _, entities = parser.parse("[a](/b)")
        self.assertEqual(text, "[a](/b)")
        self.assertEqual(entities, [])

    def test_custom_link_resolver(self):
        def wagtail(url, label):
            if url.startswith("wagtail://"):
                return {"type": "DOCUMENT", "data": {"id": 1}}
            return None

        parser, builder = parse_with_builder(link_resolvers=[wagtail])
        text, _, entities = parser.parse("[file](wagtail://document?id=1)")
        self.assertEqual(builder.entity_map["0"]["type"], "DOCUMENT")

    def test_resolver_deferring_falls_back_to_default(self):
        parser, builder = parse_with_builder(link_resolvers=[lambda url, label: None])
        parser.parse("[a](/b)")
        self.assertEqual(builder.entity_map["0"]["type"], "LINK")

    def test_link_destination_unescapes_parens(self):
        # Round-trips the exporter's md_escape_link_destination output.
        parser, builder = parse_with_builder()
        text, _, _ = parser.parse(r"[a](https://example.com/a\(b\))")
        self.assertEqual(text, "a")
        self.assertEqual(
            builder.entity_map["0"]["data"]["url"],
            "https://example.com/a(b)",
        )

    def test_link_destination_unescapes_backslash(self):
        parser, builder = parse_with_builder()
        # Markdown source: [a](https://example.com/a\\b) -> two backslashes.
        parser.parse(r"[a](https://example.com/a\\b)")
        self.assertEqual(
            builder.entity_map["0"]["data"]["url"],
            r"https://example.com/a\b",
        )

    def test_link_destination_keeps_percent_encoding(self):
        # Percent-encoding is not a Markdown escape and is left intact.
        parser, builder = parse_with_builder()
        parser.parse("[a](https://example.com/a%20b)")
        self.assertEqual(
            builder.entity_map["0"]["data"]["url"],
            "https://example.com/a%20b",
        )

    def test_link_destination_escaped_paren_does_not_close(self):
        parser, builder = parse_with_builder()
        text, _, entities = parser.parse(r"[a](https://example.com/a\)c)")
        self.assertEqual(text, "a")
        self.assertEqual(len(entities), 1)
        self.assertEqual(
            builder.entity_map["0"]["data"]["url"],
            "https://example.com/a)c",
        )


class TestImages(unittest.TestCase):
    def test_inline_image(self):
        parser, builder = parse_with_builder()
        text, _, entities = parser.parse("a ![alt](/img.jpg) b")
        self.assertEqual(text, "a alt b")
        self.assertEqual(entities, [{"offset": 2, "length": 3, "key": 0}])
        self.assertEqual(
            builder.entity_map["0"],
            {
                "type": "IMAGE",
                "mutability": "IMMUTABLE",
                "data": {"src": "/img.jpg", "alt": "alt"},
            },
        )

    def test_images_disabled(self):
        parser, _ = parse_with_builder(images=False)
        text, _, entities = parser.parse("![a](/b)")
        self.assertEqual(text, "![a](/b)")
        self.assertEqual(entities, [])

    def test_resolve_image_entity(self):
        parser, builder = parse_with_builder()
        key = parser.resolve_image_entity("/x.jpg", "alt text")
        self.assertEqual(key, 0)
        self.assertEqual(builder.entity_map["0"]["type"], "IMAGE")


class TestMalformedConstructs(unittest.TestCase):
    def test_unclosed_link_bracket_is_literal(self):
        parser, _ = parse_with_builder()
        text, _, entities = parser.parse("[a")
        self.assertEqual(text, "[a")
        self.assertEqual(entities, [])

    def test_unclosed_link_paren_is_literal(self):
        parser, _ = parse_with_builder()
        text, _, entities = parser.parse("[a](/b")
        self.assertEqual(text, "[a](/b")
        self.assertEqual(entities, [])

    def test_unclosed_image_is_literal(self):
        parser, _ = parse_with_builder()
        text, _, entities = parser.parse("![a")
        self.assertEqual(text, "![a")
        self.assertEqual(entities, [])

    def test_resolver_raising_parse_error_propagates(self):
        from draftjs_exporter.error import MarkdownParseError

        def bad(url, label):
            raise MarkdownParseError("direct failure")

        parser, _ = parse_with_builder(link_resolvers=[bad])
        with self.assertRaises(MarkdownParseError):
            parser.parse("[a](/b)")
