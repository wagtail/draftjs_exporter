"""Markdown importer: parse Markdown into Draft.js ContentState."""

import logging
import random
import re
import string
from typing import Any, Literal, TypedDict

from draftjs_exporter.constants import BLOCK_TYPES, ENTITY_TYPES, INLINE_STYLES
from draftjs_exporter.types import (
    Block,
    ContentState,
    Entity,
    EntityRange,
    InlineStyleRange,
    Mutability,
)

logger = logging.getLogger(__name__)

HEADING_RE = re.compile(r"^(#{1,6}) (.+)$")
BLOCKQUOTE_RE = re.compile(r"^> (.*)$")
UL_RE = re.compile(r"^(\s*)[*\-+] (.*)$")
OL_RE = re.compile(r"^(\s*)(\d+)[.)] (.*)$")
HR_RE = re.compile(r"^(---|\*\*\*|___)$")
IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)$")

HEADING_TYPES = {
    1: BLOCK_TYPES.HEADER_ONE,
    2: BLOCK_TYPES.HEADER_TWO,
    3: BLOCK_TYPES.HEADER_THREE,
    4: BLOCK_TYPES.HEADER_FOUR,
    5: BLOCK_TYPES.HEADER_FIVE,
    6: BLOCK_TYPES.HEADER_SIX,
}

# Inline HTML tags the Markdown exporter emits for styles that have no
# Markdown marker equivalent. This is the inverse of defaults.STYLE_MAP,
# excluding BOLD/CODE/ITALIC/STRIKETHROUGH which are overridden by
# Markdown marker syntax.
DEFAULT_HTML_STYLE_TAGS: dict[str, str] = {
    "u": INLINE_STYLES.UNDERLINE,
    "sup": INLINE_STYLES.SUPERSCRIPT,
    "sub": INLINE_STYLES.SUBSCRIPT,
    "mark": INLINE_STYLES.MARK,
    "q": INLINE_STYLES.QUOTATION,
    "small": INLINE_STYLES.SMALL,
    "samp": INLINE_STYLES.SAMPLE,
    "ins": INLINE_STYLES.INSERT,
    "del": INLINE_STYLES.DELETE,
    "kbd": INLINE_STYLES.KEYBOARD,
}

_HTML_OPEN_RE = re.compile(r"<(\w+)>")
_HTML_CLOSE_RE = re.compile(r"</(\w+)>")

_KEY_CHARS = string.ascii_lowercase + string.digits

# Characters that can be escaped with a backslash (per CommonMark spec).
_ESCAPE_CHARS = frozenset('\\`*_{}[]()#+-.!|~>"')


class MarkdownImporterOptions(TypedDict, total=False):
    """Options for customizing Markdown importer parsing behavior.

    Only inline style markers are mirrored from the exporter's
    ``MarkdownOptions``: the importer's block-level regexes accept all
    variants polymorphically (any of ``-``/``*``/``+`` for unordered
    lists, ``.``/``)`` for ordered lists, ``---``/``***``/``___`` for
    rules, and `` ``` ``/``~~~`` for fences), so there is no need to
    pass through ``unordered_list_marker`` / ``ordered_list_delimiter``
    / ``horizontal_rule`` / ``code_fence``. The same options dict can
    still be passed to ``markdown_to_content_state`` if it was produced
    by user code for ``build_markdown_config`` — the extra keys are
    simply ignored.

    Attributes:
        bold: The bold marker used by the exporter. Defaults to ``"**"``.
        italic: The italic marker used by the exporter. Defaults to ``"_"``.
        strikethrough: The strikethrough marker. Defaults to ``"~"``.
        html_style_tags: Custom mapping of HTML tag names to Draft.js
            inline style names. Merged with the defaults, so unknown
            tags fall back to plain text.
    """

    bold: Literal["**", "__"]
    italic: Literal["*", "_"]
    strikethrough: Literal["~", "~~"]
    html_style_tags: dict[str, str]


def _build_style_markers(
    options: MarkdownImporterOptions | None,
) -> list[tuple[str, str]]:
    """Build the style marker list from options, ordered longest-first.

    Parameters:
        options: Importer options, or ``None`` for defaults.

    Returns:
        A list of ``(marker, style)`` tuples sorted by marker length
        descending, so longer markers are tried first during parsing.
    """
    opts = options or {}
    markers = [
        (opts.get("bold", "**"), INLINE_STYLES.BOLD),
        (opts.get("italic", "_"), INLINE_STYLES.ITALIC),
        ("`", INLINE_STYLES.CODE),
        (opts.get("strikethrough", "~"), INLINE_STYLES.STRIKETHROUGH),
    ]
    markers.sort(key=lambda m: len(m[0]), reverse=True)
    return markers


def _build_html_style_tags(
    options: MarkdownImporterOptions | None,
) -> dict[str, str]:
    """Build the HTML tag mapping from options.

    Parameters:
        options: Importer options, or ``None`` for defaults.

    Returns:
        A dict mapping HTML tag names to Draft.js inline style names.
    """
    opts = options or {}
    tags = dict(DEFAULT_HTML_STYLE_TAGS)
    if "html_style_tags" in opts:
        tags.update(opts["html_style_tags"])
    return tags


def _gen_key() -> str:
    # Draft.js assigns keys client-side when content is loaded into an
    # editor; the importer's keys are decorative and only need to be
    # unique within a single ContentState. Random choices are sufficient
    # and let us avoid a module-level counter that would leak state
    # across calls.
    return "".join(random.choices(_KEY_CHARS, k=5))  # noqa: S311


class _InlineParser:
    """Parses inline markdown (styles and entities) from a text string.

    Walks through the text character by character, tracking opening/closing
    of style markers and link syntax, and builds up the plain text,
    style ranges, entity ranges, and entity definitions.
    """

    __slots__ = (
        "plain",
        "styles",
        "entity_ranges",
        "entities",
        "entity_counter",
        "_open_styles",
        "_style_markers",
        "_html_tags",
    )

    def __init__(
        self,
        entity_counter: int = 0,
        style_markers: list[tuple[str, str]] | None = None,
        html_tags: dict[str, str] | None = None,
    ) -> None:
        self.plain = ""
        self.styles: list[InlineStyleRange] = []
        self.entity_ranges: list[EntityRange] = []
        self.entities: dict[str, Entity] = {}
        self.entity_counter = entity_counter
        self._open_styles: dict[str, int] = {}
        self._style_markers = style_markers or _DEFAULT_STYLE_MARKERS
        self._html_tags = html_tags or DEFAULT_HTML_STYLE_TAGS

    def parse(self, text: str) -> None:
        i = 0
        while i < len(text):
            consumed = self._try_escape(text, i)
            if consumed:
                i += consumed
                continue

            consumed = self._try_link(text, i)
            if consumed:
                i += consumed
                continue

            consumed = self._try_html_tag(text, i)
            if consumed:
                i += consumed
                continue

            consumed = self._try_style_marker(text, i)
            if consumed:
                i += consumed
                continue

            self.plain += text[i]
            i += 1

    def _try_escape(self, text: str, i: int) -> int:
        """Try to parse a backslash escape at position i.

        A backslash followed by an escapable punctuation character emits
        the character literally into the plain text.

        Parameters:
            text: The text being parsed.
            i: Current position in the text.

        Returns:
            Number of characters consumed, or 0 if no escape matched.
        """
        if text[i] != "\\" or i + 1 >= len(text):
            return 0
        if text[i + 1] not in _ESCAPE_CHARS:
            return 0
        self.plain += text[i + 1]
        return 2

    def _try_link(self, text: str, i: int) -> int:
        """Try to parse a [text](url) link at position i. Returns chars consumed, or 0."""
        if text[i] != "[":
            return 0

        depth = 1
        j = i + 1
        while j < len(text) and depth > 0:
            if text[j] == "[":
                depth += 1
            elif text[j] == "]":
                depth -= 1
            j += 1

        if j >= len(text) or text[j] != "(":
            return 0

        k = j + 1
        paren_depth = 1
        while k < len(text) and paren_depth > 0:
            if text[k] == "(":
                paren_depth += 1
            elif text[k] == ")":
                paren_depth -= 1
            k += 1

        link_text = text[i + 1 : j - 1]
        raw_url = text[j + 1 : k - 1]

        # Parse optional title: url "title" or url 'title'.
        url = raw_url
        title: str | None = None
        for quote_char in ('"', "'"):
            if raw_url.endswith(quote_char) and " " + quote_char in raw_url:
                space_pos = raw_url.rfind(" " + quote_char)
                url = raw_url[:space_pos]
                title = raw_url[space_pos + 2 : -1]
                break

        start = len(self.plain)

        # Parse the link text first so any nested entities claim their
        # keys before we reserve one for the outer link. This avoids the
        # pre-increment dance of guessing the outer key before parsing.
        inner = _InlineParser(self.entity_counter, self._style_markers, self._html_tags)
        inner.parse(link_text)
        entity_key = inner.entity_counter
        self.entity_counter = entity_key + 1

        link_data: dict[str, Any] = {"url": url}
        if title is not None:
            link_data["title"] = title
        self.entities[str(entity_key)] = {
            "type": ENTITY_TYPES.LINK,
            "mutability": "MUTABLE",
            "data": link_data,
        }
        self.entity_ranges.append(
            {"offset": start, "length": len(inner.plain), "key": entity_key}
        )

        for s in inner.styles:
            self.styles.append(
                {
                    "offset": s["offset"] + start,
                    "length": s["length"],
                    "style": s["style"],
                }
            )

        for ek, ev in inner.entities.items():
            self.entities[ek] = ev
        self.entity_ranges.extend(inner.entity_ranges)

        self.plain += inner.plain
        return k - i

    def _try_html_tag(self, text: str, i: int) -> int:
        """Try to parse an inline HTML style tag at position i.

        Matches ``<tag>`` opening and ``</tag>`` closing tags against the
        configured HTML tag mapping. Uses the same open/close tracking
        as style markers (``_open_styles`` dict).

        Parameters:
            text: The text being parsed.
            i: Current position in the text.

        Returns:
            Number of characters consumed, or 0 if no HTML tag matched.
        """
        m = _HTML_CLOSE_RE.match(text, i)
        if m and m.group(1) in self._html_tags:
            style = self._html_tags[m.group(1)]
            if style in self._open_styles:
                start = self._open_styles.pop(style)
                length = len(self.plain) - start
                if length > 0:
                    self.styles.append(
                        {"offset": start, "length": length, "style": style}
                    )
                return m.end() - i
            return 0

        m = _HTML_OPEN_RE.match(text, i)
        if m and m.group(1) in self._html_tags:
            style = self._html_tags[m.group(1)]
            self._open_styles[style] = len(self.plain)
            return m.end() - i

        return 0

    def _try_style_marker(self, text: str, i: int) -> int:
        """Try to match a style marker at position i. Returns chars consumed, or 0."""
        for marker, style in self._style_markers:
            if text[i : i + len(marker)] != marker:
                continue

            # Single-char markers like _ must be at a word boundary to avoid
            # matching inside words like some_var_name or URLs with underscores.
            if marker == "_":
                prev_is_word = i > 0 and (text[i - 1].isalnum() or text[i - 1] == "_")
                next_is_word = i + 1 < len(text) and (
                    text[i + 1].isalnum() or text[i + 1] == "_"
                )
                if prev_is_word and next_is_word:
                    return 0

            if style in self._open_styles:
                start = self._open_styles.pop(style)
                length = len(self.plain) - start
                if length > 0:
                    self.styles.append(
                        {"offset": start, "length": length, "style": style}
                    )
                return len(marker)
            else:
                self._open_styles[style] = len(self.plain)
                return len(marker)

        return 0


# Default style markers, ordered longest-first for correct matching.
_DEFAULT_STYLE_MARKERS = _build_style_markers(None)

_BLOCK_PATTERNS = [HEADING_RE, BLOCKQUOTE_RE, UL_RE, OL_RE, HR_RE, IMAGE_RE]


def _is_block_level(line: str) -> bool:
    """Check if a line is a standalone block-level element (not a plain paragraph)."""
    return any(p.match(line) for p in _BLOCK_PATTERNS)


def _split_blocks(markdown: str) -> list[str]:
    r"""Split markdown into raw block strings.

    Handles code fences, joins consecutive plain lines into a single
    paragraph block (standard markdown soft line breaks), and attaches
    continuation lines to the preceding block-level element (preserving
    ``\n`` in block text for soft line breaks within list items, etc.).
    """
    blocks: list[str] = []
    in_code = False
    code_lines: list[str] = []
    paragraph_lines: list[str] = []
    # Whether the last emitted block was block-level (heading, list, etc.)
    # and no blank line has appeared since — continuation lines should be
    # appended to it rather than starting a new paragraph.
    continuation = False

    def flush_paragraph() -> None:
        if paragraph_lines:
            blocks.append(" ".join(paragraph_lines))
            paragraph_lines.clear()

    for line in markdown.split("\n"):
        if not in_code and (line.startswith("```") or line.startswith("~~~")):
            flush_paragraph()
            continuation = False
            in_code = True
            code_lines = [line]
            continue

        if in_code and (line == "```" or line == "~~~"):
            code_lines.append(line)
            blocks.append("\n".join(code_lines))
            code_lines = []
            in_code = False
            continue

        if in_code:
            code_lines.append(line)
            continue

        if line == "":
            flush_paragraph()
            continuation = False
            continue

        if _is_block_level(line):
            # Consecutive blockquote lines (each starting with "> ") are
            # treated as a continuation of the same block rather than
            # separate blocks.
            if (
                continuation
                and blocks
                and blocks[-1].startswith("> ")
                and line.startswith("> ")
            ):
                blocks[-1] += "\n" + line
            else:
                flush_paragraph()
                blocks.append(line)
                continuation = True
        elif continuation:
            # Continuation of a block-level element (e.g. list item with
            # a soft line break in the text). Join with \n to preserve the
            # original line break.
            blocks[-1] += "\n" + line
        else:
            paragraph_lines.append(line)

    flush_paragraph()
    return blocks


def _inline_block(
    text: str,
    block_type: str,
    depth: int,
    entity_counter: int,
    style_markers: list[tuple[str, str]] | None = None,
    html_tags: dict[str, str] | None = None,
) -> tuple[Block, dict[str, Entity], int]:
    """Parse inline content and build a block with the given type and depth.

    Parameters:
        text: The raw text to parse.
        block_type: The Draft.js block type.
        depth: The block nesting depth.
        entity_counter: The current entity key counter.
        style_markers: Configurable style markers, or ``None`` for defaults.
        html_tags: Configurable HTML tag mapping, or ``None`` for defaults.

    Returns:
        A tuple of (block, entities, updated entity counter).
    """
    parser = _InlineParser(entity_counter, style_markers, html_tags)
    parser.parse(text)
    block: Block = {
        "key": _gen_key(),
        "text": parser.plain,
        "type": block_type,
        "depth": depth,
        "inlineStyleRanges": _merge_style_ranges(parser.styles),
        "entityRanges": parser.entity_ranges,
    }
    return block, parser.entities, parser.entity_counter


def _atomic_block(
    entity_type: str,
    mutability: Mutability,
    data: dict[str, Any],
    entity_counter: int,
) -> tuple[Block, dict[str, Entity], int]:
    """Build an atomic block with a single entity (HR, IMAGE, etc.).

    Parameters:
        entity_type: The Draft.js entity type.
        mutability: The entity mutability.
        data: The entity data dict.
        entity_counter: The current entity key counter.

    Returns:
        A tuple of (block, entities, updated entity counter).
    """
    block: Block = {
        "key": _gen_key(),
        "text": " ",
        "type": BLOCK_TYPES.ATOMIC,
        "depth": 0,
        "inlineStyleRanges": [],
        "entityRanges": [{"offset": 0, "length": 1, "key": entity_counter}],
    }
    entities: dict[str, Entity] = {
        str(entity_counter): {
            "type": entity_type,
            "mutability": mutability,
            "data": data,
        }
    }
    return block, entities, entity_counter + 1


def _parse_block(
    raw: str,
    entity_counter: int,
    style_markers: list[tuple[str, str]] | None = None,
    html_tags: dict[str, str] | None = None,
) -> tuple[Block, dict[str, Entity], int]:
    """Parse a raw block string into a Block, entities, and updated entity counter.

    Parameters:
        raw: The raw block string to parse.
        entity_counter: The current entity key counter.
        style_markers: Configurable style markers, or ``None`` for defaults.
        html_tags: Configurable HTML tag mapping, or ``None`` for defaults.

    Returns:
        A tuple of (block, entities, updated entity counter).
    """
    if HR_RE.match(raw):
        return _atomic_block(
            ENTITY_TYPES.HORIZONTAL_RULE, "IMMUTABLE", {}, entity_counter
        )

    m = IMAGE_RE.match(raw)
    if m:
        alt = m.group(1)
        src = m.group(2)
        data: dict[str, Any] = {"src": src}
        if alt:
            data["alt"] = alt
        return _atomic_block(ENTITY_TYPES.IMAGE, "IMMUTABLE", data, entity_counter)

    is_backtick_fence = raw.startswith("```") and raw.endswith("```")
    is_tilde_fence = raw.startswith("~~~") and raw.endswith("~~~")
    if is_backtick_fence or is_tilde_fence:
        lines = raw.split("\n")
        # Strip opening fence (+ optional info string) and closing fence.
        content = "\n".join(lines[1:-1]) if len(lines) >= 3 else ""
        block: Block = {
            "key": _gen_key(),
            "text": content,
            "type": BLOCK_TYPES.CODE,
            "depth": 0,
            "inlineStyleRanges": [],
            "entityRanges": [],
        }
        return block, {}, entity_counter

    # For block-level elements, the regex matches the first line only.
    # Any continuation lines after \n are appended to preserve soft line breaks.
    newline_pos = raw.find("\n")
    first_line = raw[:newline_pos] if newline_pos != -1 else raw
    rest = raw[newline_pos:] if newline_pos != -1 else ""

    m = HEADING_RE.match(first_line)
    if m:
        level = len(m.group(1))
        return _inline_block(
            m.group(2) + rest,
            HEADING_TYPES[level],
            0,
            entity_counter,
            style_markers,
            html_tags,
        )

    m = BLOCKQUOTE_RE.match(first_line)
    if m:
        # Strip "> " prefix from continuation lines (multi-line blockquotes).
        if rest:
            rest = rest.replace("\n> ", "\n")
        return _inline_block(
            m.group(1) + rest,
            BLOCK_TYPES.BLOCKQUOTE,
            0,
            entity_counter,
            style_markers,
            html_tags,
        )

    m = UL_RE.match(first_line)
    if m:
        depth = len(m.group(1)) // 2
        return _inline_block(
            m.group(2) + rest,
            BLOCK_TYPES.UNORDERED_LIST_ITEM,
            depth,
            entity_counter,
            style_markers,
            html_tags,
        )

    m = OL_RE.match(first_line)
    if m:
        depth = len(m.group(1)) // 2
        return _inline_block(
            m.group(3) + rest,
            BLOCK_TYPES.ORDERED_LIST_ITEM,
            depth,
            entity_counter,
            style_markers,
            html_tags,
        )

    # Any non-empty text that doesn't match a block-level pattern becomes a
    # plain paragraph. This is the expected path for hand-written Markdown,
    # so we log at debug level rather than warning (a paragraph isn't an
    # anomaly). Malformed block-level syntax (e.g. "#NoSpace") also lands
    # here and is treated as a paragraph.
    logger.debug('Treating markdown as unstyled paragraph: "%s"', first_line)
    return _inline_block(
        raw,
        BLOCK_TYPES.UNSTYLED,
        0,
        entity_counter,
        style_markers,
        html_tags,
    )


def _merge_style_ranges(
    styles: list[InlineStyleRange],
) -> list[InlineStyleRange]:
    """Merge adjacent or overlapping ranges of the same style.

    This compensates for the exporter's inline style nesting behavior.
    When styles partially overlap (e.g. bold 0-5, italic 3-8), the
    exporter must close and reopen the outer marker to produce valid
    Markdown (e.g. ``**Bold ****_Italic_**``). This produces two BOLD
    ranges that should be a single continuous range.

    This is an intentional round-trip trade-off: the importer repairs
    the exporter's marker-emission quirks so that
    ``ContentState -> Markdown -> ContentState`` preserves the original
    style ranges.
    """
    if not styles:
        return styles

    by_style: dict[str, list[InlineStyleRange]] = {}
    for s in styles:
        by_style.setdefault(s["style"], []).append(s)

    merged: list[InlineStyleRange] = []
    for style, ranges in by_style.items():
        sorted_ranges = sorted(ranges, key=lambda r: r["offset"])
        cur_offset = sorted_ranges[0]["offset"]
        cur_length = sorted_ranges[0]["length"]
        for r in sorted_ranges[1:]:
            cur_end = cur_offset + cur_length
            if r["offset"] <= cur_end:
                new_end = max(cur_end, r["offset"] + r["length"])
                cur_length = new_end - cur_offset
            else:
                merged.append(
                    {"offset": cur_offset, "length": cur_length, "style": style}
                )
                cur_offset = r["offset"]
                cur_length = r["length"]
        merged.append({"offset": cur_offset, "length": cur_length, "style": style})

    return merged


def markdown_to_content_state(
    markdown: str,
    options: MarkdownImporterOptions | None = None,
) -> ContentState:
    """Convert a Markdown string to a Draft.js ContentState.

    Supports the same subset of Markdown that the exporter produces:
    block-level formatting, inline styles, and entities.

    Parameters:
        markdown: The Markdown string to parse.
        options: Optional importer options mirroring the exporter's
            ``MarkdownOptions``. Pass the same options used with
            ``build_markdown_config`` to round-trip customized output.

    Returns:
        A Draft.js ContentState dict with blocks and entityMap.
    """
    markdown = markdown.rstrip()

    raw_blocks = _split_blocks(markdown)

    style_markers = _build_style_markers(options)
    html_tags = _build_html_style_tags(options)

    blocks: list[Block] = []
    entity_map: dict[str, Entity] = {}
    entity_counter = 0

    for raw in raw_blocks:
        block, block_entities, entity_counter = _parse_block(
            raw, entity_counter, style_markers, html_tags
        )
        blocks.append(block)
        entity_map.update(block_entities)

    return {"blocks": blocks, "entityMap": entity_map}
