"""Markdown parsing engine: converts CommonMark core to Draft.js ContentState."""

from typing import TypedDict

from draftjs_exporter.markdown_parser.blocks import BlockParser
from draftjs_exporter.markdown_parser.builder import ContentStateBuilder
from draftjs_exporter.markdown_parser.inline import InlineParser
from draftjs_exporter.markdown_parser.resolvers import (
    EntityResolution as EntityResolution,
)
from draftjs_exporter.markdown_parser.resolvers import (
    EntityResolver as EntityResolver,
)
from draftjs_exporter.markdown_parser.resolvers import (
    scheme_resolver as scheme_resolver,
)
from draftjs_exporter.types import ContentState


class ParserConfig(TypedDict, total=False):
    """Options controlling which Markdown constructs are recognized."""

    headings: bool
    """Parse ATX headings (default: True)."""

    blockquote: bool
    """Parse ``>`` blockquotes (default: True)."""

    code_fenced: bool
    """Parse fenced code blocks (default: True)."""

    thematic_break: bool
    """Parse thematic breaks (default: True)."""

    unordered_list: bool
    """Parse unordered lists (default: True)."""

    ordered_list: bool
    """Parse ordered lists (default: True)."""

    emphasis: bool
    """Parse bold and italic delimiters (default: True)."""

    code_inline: bool
    """Parse backtick code spans (default: True)."""

    links: bool
    """Parse ``[label](url)`` links (default: True)."""

    images: bool
    """Parse ``![alt](url)`` images (default: True)."""

    line_breaks: bool
    """Strip two-space hard break markers (default: True)."""

    link_resolvers: list[EntityResolver]
    """Resolver chain for link URLs (default: empty, uses ``LINK`` with the URL)."""

    image_resolvers: list[EntityResolver]
    """Resolver chain for image URLs (default: empty, uses ``IMAGE`` with ``src``/``alt``)."""

    inline_html_styles: dict[str, str]
    """Whitelist of HTML tags mapped to inline styles, e.g. ``{"sup": "SUPERSCRIPT"}``."""


class MarkdownParser:
    """Parse Markdown text into a Draft.js ContentState.

    Supports the CommonMark core: paragraphs, ATX headings, blockquotes,
    fenced code, thematic breaks, lists, emphasis, code spans, links,
    images, and hard line breaks. Every input produces either a
    structurally valid ContentState or a ``MarkdownParseError``.
    """

    __slots__ = ("config",)

    config: ParserConfig

    def __init__(self, config: ParserConfig | None = None) -> None:
        """Initialize the parser with the given configuration.

        Parameters:
            config: Feature toggles and entity resolvers. Missing keys
                use defaults that enable all constructs.
        """
        self.config = config if config is not None else ParserConfig()

    def parse(self, markdown: str) -> ContentState:
        """Parse Markdown source into a ContentState.

        Parameters:
            markdown: The Markdown text to parse.

        Returns:
            A structurally valid Draft.js ContentState.

        Raises:
            TypeError: If ``markdown`` is not a string.
            MarkdownParseError: If an entity resolver fails.
        """
        if not isinstance(markdown, str):
            raise TypeError(f"Expected str, got {type(markdown).__name__}")
        text = markdown.replace("\r\n", "\n").replace("\r", "\n")
        builder = ContentStateBuilder()
        images = self.config.get("images", True)
        inline = InlineParser(
            emphasis=self.config.get("emphasis", True),
            code_inline=self.config.get("code_inline", True),
            links=self.config.get("links", True),
            images=images,
            line_breaks=self.config.get("line_breaks", True),
            inline_html_styles=self.config.get("inline_html_styles", {}),
            link_resolvers=self.config.get("link_resolvers", []),
            image_resolvers=self.config.get("image_resolvers", []),
            builder=builder,
        )
        blocks = BlockParser(
            headings=self.config.get("headings", True),
            blockquote=self.config.get("blockquote", True),
            code_fenced=self.config.get("code_fenced", True),
            thematic_break=self.config.get("thematic_break", True),
            unordered_list=self.config.get("unordered_list", True),
            ordered_list=self.config.get("ordered_list", True),
            images=images,
            inline=inline,
            builder=builder,
        )
        blocks.parse(text)
        return builder.build()
