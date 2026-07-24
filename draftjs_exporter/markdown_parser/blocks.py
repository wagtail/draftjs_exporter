"""Block-level Markdown parsing: lines to Draft.js blocks."""

import re
from typing import Any

from draftjs_exporter.constants import BLOCK_TYPES, ENTITY_TYPES
from draftjs_exporter.error import MarkdownParseError
from draftjs_exporter.markdown_parser.builder import ContentStateBuilder
from draftjs_exporter.markdown_parser.inline import InlineParser
from draftjs_exporter.types import Mutability

ATX_RE = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$")
"""ATX heading with optional closing hash sequence."""

HR_RE = re.compile(r"^[ \t]*((\*[ \t]*){3,}|(-[ \t]*){3,}|(_[ \t]*){3,})$")
"""Thematic break: 3+ of the same ``*``, ``-``, or ``_`` marker."""

FENCE_RE = re.compile(r"^[ \t]*(```+|~~~+)(.*)$")
"""Fenced code block opener or closer."""

QUOTE_RE = re.compile(r"^[ \t]*>[ \t]?(.*)$")
"""Blockquote line, capturing the content after the marker."""

ULIST_RE = re.compile(r"^([ \t]*)[-*+][ \t]+(.*)$")
"""Unordered list item, capturing indent and content."""

OLIST_RE = re.compile(r"^([ \t]*)\d{1,9}[.)][ \t]+(.*)$")
"""Ordered list item, capturing indent and content."""

STANDALONE_IMAGE_RE = re.compile(r"^!\[(.*)\]\((.*)\)$")
"""A paragraph consisting of exactly one image."""

HEADING_TYPES = [
    BLOCK_TYPES.HEADER_ONE,
    BLOCK_TYPES.HEADER_TWO,
    BLOCK_TYPES.HEADER_THREE,
    BLOCK_TYPES.HEADER_FOUR,
    BLOCK_TYPES.HEADER_FIVE,
    BLOCK_TYPES.HEADER_SIX,
]
"""Heading block types indexed by ATX level minus one."""


def _indent_width(text: str, tab_size: int = 4) -> int:
    """Compute the column width of indentation, expanding tabs to tab stops.

    Per CommonMark, a tab advances the column position to the next
    multiple of 4 rather than counting as a fixed number of spaces.

    Parameters:
        text: The leading whitespace of a line.
        tab_size: The tab stop interval.

    Returns:
        The column position after the indentation.
    """
    col = 0
    for ch in text:
        if ch == "\t":
            col += tab_size - (col % tab_size)
        else:
            col += 1
    return col


class BlockParser:
    """Parse Markdown line by line into Draft.js blocks.

    The parser tracks block constructs that span lines (lists,
    blockquotes, fenced code) and delegates inline content to the
    inline parser. It emits blocks directly onto the builder — there
    is no intermediate AST.
    """

    __slots__ = (
        "headings",
        "blockquote",
        "code_fenced",
        "thematic_break",
        "unordered_list",
        "ordered_list",
        "images",
        "inline",
        "builder",
    )

    def __init__(
        self,
        *,
        headings: bool,
        blockquote: bool,
        code_fenced: bool,
        thematic_break: bool,
        unordered_list: bool,
        ordered_list: bool,
        images: bool,
        inline: InlineParser,
        builder: ContentStateBuilder,
    ) -> None:
        """Initialize the parser with feature toggles and helpers.

        Parameters:
            headings: Parse ATX headings.
            blockquote: Parse ``>`` blockquotes.
            code_fenced: Parse fenced code blocks.
            thematic_break: Parse thematic breaks.
            unordered_list: Parse unordered lists.
            ordered_list: Parse ordered lists.
            images: Convert standalone images to atomic blocks.
            inline: The inline parser for block content.
            builder: The builder blocks are appended to.
        """
        self.headings = headings
        self.blockquote = blockquote
        self.code_fenced = code_fenced
        self.thematic_break = thematic_break
        self.unordered_list = unordered_list
        self.ordered_list = ordered_list
        self.images = images
        self.inline = inline
        self.builder = builder

    def parse(self, text: str) -> None:
        r"""Parse Markdown source, appending blocks to the builder.

        Parameters:
            text: Markdown with line endings normalized to ``\n``.
        """
        lines = text.split("\n")
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            if self.code_fenced and (match := FENCE_RE.match(line)):
                i = self._parse_fence(lines, i, match)
                continue
            if self.headings and (match := ATX_RE.match(line)):
                self._add_text_block(
                    HEADING_TYPES[len(match.group(1)) - 1], match.group(2), i
                )
                i += 1
                continue
            if self.thematic_break and HR_RE.match(line):
                self._add_atomic(ENTITY_TYPES.HORIZONTAL_RULE, {}, "IMMUTABLE")
                i += 1
                continue
            if self.blockquote and QUOTE_RE.match(line):
                i = self._parse_quote(lines, i)
                continue
            if self._is_list_item(line):
                i = self._parse_list(lines, i)
                continue
            i = self._parse_paragraph(lines, i)

    def _add_text_block(
        self, type_: str, source: str, line_index: int, depth: int = 0
    ) -> None:
        """Inline-parse source text and append a block.

        Parameters:
            type_: The Draft.js block type.
            source: The Markdown source of the block's content.
            line_index: 0-based source line, for error reporting.
            depth: Nesting depth for list items.
        """
        try:
            text, styles, entities = self.inline.parse(source)
        except MarkdownParseError as err:
            if err.line is None:
                raise MarkdownParseError(err.message, line=line_index + 1) from err
            raise
        self.builder.add_block(
            type_,
            text,
            depth=depth,
            inline_style_ranges=styles,
            entity_ranges=entities,
        )

    def _add_atomic(
        self, entity_type: str, data: dict[str, Any], mutability: Mutability
    ) -> None:
        """Append an atomic block carrying a single entity.

        Parameters:
            entity_type: The entity type.
            data: The entity data.
            mutability: The entity mutability.
        """
        key = self.builder.add_entity(entity_type, data, mutability)
        self.builder.add_block(
            BLOCK_TYPES.ATOMIC,
            " ",
            entity_ranges=[{"offset": 0, "length": 1, "key": key}],
        )

    def _is_list_item(self, line: str) -> bool:
        """Return whether the line starts an enabled list item."""
        return bool(
            (self.unordered_list and ULIST_RE.match(line))
            or (self.ordered_list and OLIST_RE.match(line))
        )

    def _starts_block(self, line: str) -> bool:
        """Return whether the line starts a block construct."""
        return bool(
            (self.code_fenced and FENCE_RE.match(line))
            or (self.headings and ATX_RE.match(line))
            or (self.thematic_break and HR_RE.match(line))
            or (self.blockquote and QUOTE_RE.match(line))
            or self._is_list_item(line)
        )

    def _parse_paragraph(self, lines: list[str], i: int) -> int:
        """Parse consecutive plain lines into one paragraph block."""
        start = i
        collected = [lines[i]]
        i += 1
        while i < len(lines) and lines[i].strip() and not self._starts_block(lines[i]):
            collected.append(lines[i])
            i += 1
        source = "\n".join(collected)
        image = STANDALONE_IMAGE_RE.match(source.strip()) if self.images else None
        if image is not None:
            key = self.inline.resolve_image_entity(image.group(2), image.group(1))
            self.builder.add_block(
                BLOCK_TYPES.ATOMIC,
                " ",
                entity_ranges=[{"offset": 0, "length": 1, "key": key}],
            )
        else:
            self._add_text_block(BLOCK_TYPES.UNSTYLED, source, start)
        return i

    def _parse_fence(self, lines: list[str], i: int, match: re.Match[str]) -> int:
        """Parse a fenced code block starting at line i.

        Unclosed fences parse to end of input, per CommonMark.

        Parameters:
            lines: All source lines.
            i: Index of the opening fence line.
            match: The fence opener match.

        Returns:
            The index of the first line after the block.
        """
        fence = match.group(1)
        marker = fence[0]
        size = len(fence)
        body: list[str] = []
        i += 1
        while i < len(lines):
            close = FENCE_RE.match(lines[i])
            if (
                close is not None
                and close.group(1)[0] == marker
                and len(close.group(1)) >= size
            ):
                i += 1
                break
            body.append(lines[i])
            i += 1
        self.builder.add_block(BLOCK_TYPES.CODE, "\n".join(body))
        return i

    def _parse_quote(self, lines: list[str], i: int) -> int:
        """Parse consecutive blockquote lines into blockquote blocks.

        Quoted lines join with newlines. A quoted line with no content
        (``>`` alone) splits the quote into separate blocks.

        Parameters:
            lines: All source lines.
            i: Index of the first quoted line.

        Returns:
            The index of the first line after the quote.
        """
        start = i
        quote_lines: list[str] = []
        while i < len(lines):
            match = QUOTE_RE.match(lines[i])
            if match is None:
                break
            quote_lines.append(match.group(1))
            i += 1
        paragraph: list[str] = []
        for offset, content in enumerate(quote_lines):
            if not content.strip():
                if paragraph:
                    self._add_text_block(
                        BLOCK_TYPES.BLOCKQUOTE, "\n".join(paragraph), start + offset
                    )
                    paragraph = []
            else:
                paragraph.append(content)
        if paragraph:
            self._add_text_block(
                BLOCK_TYPES.BLOCKQUOTE,
                "\n".join(paragraph),
                start + len(quote_lines) - 1,
            )
        return i

    def _parse_list(self, lines: list[str], i: int) -> int:
        """Parse consecutive list items with indent-based depth tracking.

        Depth derives from a stack of indent widths: deeper indents
        push, shallower indents pop. Continuation lines (indented
        content without a marker) are not supported — they end the
        list and become paragraphs.

        Parameters:
            lines: All source lines.
            i: Index of the first list item line.

        Returns:
            The index of the first line after the list.
        """
        stack: list[int] = []
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                break
            unordered = ULIST_RE.match(line) if self.unordered_list else None
            ordered = OLIST_RE.match(line) if self.ordered_list else None
            match = unordered or ordered
            if match is None:
                break
            indent = _indent_width(match.group(1))
            while stack and indent < stack[-1]:
                stack.pop()
            if not stack or indent > stack[-1]:
                stack.append(indent)
            type_ = (
                BLOCK_TYPES.UNORDERED_LIST_ITEM
                if unordered
                else BLOCK_TYPES.ORDERED_LIST_ITEM
            )
            self._add_text_block(type_, match.group(2), i, depth=len(stack) - 1)
            i += 1
        return i
