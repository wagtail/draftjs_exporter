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
    blockquote: bool
    code_fenced: bool
    thematic_break: bool
    unordered_list: bool
    ordered_list: bool
    emphasis: bool
    code_inline: bool
    links: bool
    images: bool
    line_breaks: bool
    link_resolvers: list[EntityResolver]
    image_resolvers: list[EntityResolver]
    inline_html_styles: dict[str, str]


class MarkdownParser:
    """Parse Markdown text into a Draft.js ContentState.

    Supports the CommonMark core: paragraphs, ATX headings, blockquotes,
    fenced code, thematic breaks, lists, emphasis, code spans, links,
    images, and hard line breaks. Every input produces either a
    structurally valid ContentState or a ``MarkdownParseError``.
    """

    __slots__ = ("config",)

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
