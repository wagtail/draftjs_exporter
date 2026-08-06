"""Inline Markdown parsing: emphasis, code spans, links, images, inline HTML."""

import re
from collections.abc import Callable
from typing import TypeAlias

from draftjs_exporter.constants import INLINE_STYLES
from draftjs_exporter.error import MarkdownParseError
from draftjs_exporter.markdown_parser.builder import ContentStateBuilder
from draftjs_exporter.markdown_parser.resolvers import (
    EntityResolution,
    EntityResolver,
    default_image_resolver,
    default_link_resolver,
    resolve,
)
from draftjs_exporter.types import EntityRange, InlineStyleRange

Span: TypeAlias = tuple[int, int, str, "str | int"]
"""An inline annotation: ``(offset, length, kind, payload)``.

``kind`` is ``"style"`` (payload: style name) or ``"entity"`` (payload:
integer entity key).
"""

# The full set of ASCII punctuation characters that CommonMark permits
# to be backslash-escaped ("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"). The
# exporter only emits escapes for a subset, but the importer accepts any
# valid backslash-escaped punctuation so user-authored Markdown round-trips.
ESCAPABLE = frozenset("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
"""ASCII punctuation that can be backslash-escaped per CommonMark."""

TAG_RE = re.compile(r"<([a-zA-Z][a-zA-Z0-9]*)>")
"""Matches an HTML opening tag without attributes."""

MAX_INLINE_DEPTH = 100
"""Maximum nesting depth for inline constructs before rejecting input."""


class InlineParser:
    """Parse inline Markdown constructs into text with style/entity ranges.

    The parser is a character-by-character recursive descent scanner.
    Delimiter runs (``*``, ``_``) match by exact length: ``**`` only
    closes ``**``, not two adjacent ``*`` runs. Intraword emphasis and
    other flanking-rule subtleties are intentionally not supported.
    """

    __slots__ = (
        "emphasis",
        "code_inline",
        "links",
        "images",
        "line_breaks",
        "inline_html_styles",
        "link_resolvers",
        "image_resolvers",
        "builder",
    )

    def __init__(
        self,
        *,
        emphasis: bool,
        code_inline: bool,
        links: bool,
        images: bool,
        line_breaks: bool,
        inline_html_styles: dict[str, str],
        link_resolvers: list[EntityResolver],
        image_resolvers: list[EntityResolver],
        builder: ContentStateBuilder,
    ) -> None:
        """Initialize the parser with feature toggles and resolvers.

        Parameters:
            emphasis: Parse ``*italic*`` / ``**bold**`` constructs.
            code_inline: Parse backtick code spans.
            links: Parse ``[label](url)`` links.
            images: Parse ``![alt](url)`` images.
            line_breaks: Strip two-space hard break markers.
            inline_html_styles: Whitelist of HTML tags to inline styles.
            link_resolvers: Resolver chain for link URLs.
            image_resolvers: Resolver chain for image URLs.
            builder: The builder entities are registered on.
        """
        self.emphasis = emphasis
        self.code_inline = code_inline
        self.links = links
        self.images = images
        self.line_breaks = line_breaks
        self.inline_html_styles = inline_html_styles
        self.link_resolvers = link_resolvers
        self.image_resolvers = image_resolvers
        self.builder = builder

    def parse(self, text: str) -> tuple[str, list[InlineStyleRange], list[EntityRange]]:
        """Convert Markdown inline syntax to plain text plus ranges.

        Parameters:
            text: The Markdown source of a single block.

        Returns:
            The plain text, its inline style ranges, and its entity ranges.
        """
        plain, spans = self._parse(text)
        styles: list[InlineStyleRange] = []
        entities: list[EntityRange] = []
        for offset, length, kind, payload in spans:
            if kind == "style":
                styles.append(
                    {"offset": offset, "length": length, "style": str(payload)}
                )
            else:
                entities.append(
                    {"offset": offset, "length": length, "key": int(payload)}
                )
        styles.sort(key=lambda r: r["offset"])
        entities.sort(key=lambda r: r["offset"])
        return plain, styles, entities

    def resolve_image_entity(self, url: str, alt: str) -> int:
        """Register an image entity through the resolver chain.

        Parameters:
            url: The image URL.
            alt: The image alt text.

        Returns:
            The integer key of the newly registered entity.
        """
        return self._resolve_entity(
            url, alt, self.image_resolvers, default_image_resolver
        )

    def _resolve_entity(
        self,
        url: str,
        label: str,
        resolvers: list[EntityResolver],
        default: Callable[[str, str], EntityResolution],
    ) -> int:
        """Resolve a URL into an entity and register it on the builder."""
        try:
            resolution: EntityResolution = resolve(resolvers, url, label, default)
        except MarkdownParseError:
            # Propagate without wrapping; unexpected exceptions are wrapped below.
            raise
        except Exception as err:
            raise MarkdownParseError(
                f"Entity resolver failed for URL {url!r}: {err}"
            ) from err
        entity_type = resolution.get("type")
        if not isinstance(entity_type, str) or not entity_type:
            raise MarkdownParseError(
                f"Entity resolver for URL {url!r} must return a 'type'"
            )
        data = resolution.get("data", {})
        if not isinstance(data, dict):
            raise MarkdownParseError(
                f"Entity resolver for URL {url!r} must return dict 'data'"
            )
        return self.builder.add_entity(
            entity_type, data, resolution.get("mutability", "MUTABLE")
        )

    def _parse(self, text: str, depth: int = 0) -> tuple[str, list[Span]]:
        """Scan text, returning output characters and annotation spans.

        Parameters:
            text: The text to scan.
            depth: Current recursion depth for nested constructs.

        Raises:
            MarkdownParseError: If nesting exceeds ``MAX_INLINE_DEPTH``.
        """
        if depth > MAX_INLINE_DEPTH:
            raise MarkdownParseError("Inline nesting too deep")
        out: list[str] = []
        spans: list[Span] = []
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]

            # Backslash escapes.
            if ch == "\\" and i + 1 < n and text[i + 1] in ESCAPABLE:
                out.append(text[i + 1])
                i += 2
                continue

            # Code spans: a backtick run opens; an equal-length run closes.
            if ch == "`" and self.code_inline:
                run = 1
                while i + run < n and text[i + run] == "`":
                    run += 1
                close = InlineParser._find_code_closer(text, i + run, run)
                if close != -1:
                    raw = text[i + run : close]
                    content = InlineParser._normalize_code_content(raw)
                    start = len(out)
                    out.extend(content)
                    spans.append((start, len(content), "style", INLINE_STYLES.CODE))
                    i = close + run
                    continue

            # Images: ![alt](url)
            if ch == "!" and i + 1 < n and text[i + 1] == "[":
                result = self._link_target(text, i + 1)
                if result is not None:
                    alt, url, end = result
                    if not self.images:
                        # Disabled: keep the whole construct literal rather
                        # than letting the bracket parse as a link.
                        out.extend(text[i:end])
                        i = end
                        continue
                    start = len(out)
                    out.extend(alt)
                    key = self._resolve_entity(
                        url, alt, self.image_resolvers, default_image_resolver
                    )
                    spans.append((start, len(alt), "entity", key))
                    i = end
                    continue

            # Links: [label](url)
            if self.links and ch == "[":
                result = self._link_target(text, i)
                if result is not None:
                    label_src, url, end = result
                    label_plain, label_spans = self._parse(label_src, depth + 1)
                    start = len(out)
                    out.extend(label_plain)
                    spans.extend(
                        (s + start, length, kind, payload)
                        for s, length, kind, payload in label_spans
                    )
                    key = self._resolve_entity(
                        url, label_plain, self.link_resolvers, default_link_resolver
                    )
                    spans.append((start, len(label_plain), "entity", key))
                    i = end
                    continue

            # Emphasis: * _ ** __ *** ___
            if self.emphasis and ch in "*_":
                consumed = self._parse_emphasis(text, i, out, spans, depth)
                if consumed is not None:
                    i = consumed
                    continue

            # Whitelisted inline HTML tags.
            if ch == "<" and self.inline_html_styles:
                consumed = self._parse_inline_html(text, i, out, spans, depth)
                if consumed is not None:
                    i = consumed
                    continue

            # Hard line breaks: strip 2+ trailing spaces before newline.
            if ch == "\n" and self.line_breaks:
                spaces = 0
                j = len(out) - 1
                while j >= 0 and out[j] == " ":
                    spaces += 1
                    j -= 1
                if spaces >= 2:
                    del out[j + 1 :]
                out.append("\n")
                i += 1
                continue

            out.append(ch)
            i += 1

        return "".join(out), spans

    @staticmethod
    def _link_target(text: str, i: int) -> tuple[str, str, int] | None:
        r"""Parse ``[label](url)`` starting at the opening bracket.

        Parameters:
            text: The full source text.
            i: Index of the ``[`` character.

        Returns:
            ``(label, url, end_index)`` or None when the construct does
            not parse. Labels containing ``](`` are not supported. URLs
            may contain escaped parentheses (``\\(``, ``\\)``), which
            are unescaped in the returned URL.
        """
        close = text.find("](", i)
        if close == -1:
            return None
        paren = InlineParser._find_unescaped_paren(text, close + 2)
        if paren == -1:
            return None
        url = InlineParser._unescape_destination(text[close + 2 : paren])
        return text[i + 1 : close], url, paren + 1

    @staticmethod
    def _find_code_closer(text: str, start: int, n: int) -> int:
        """Find a backtick run of exactly length ``n`` at or after ``start``.

        Per CommonMark, a code span opener only closes on a backtick
        string of equal length: a shorter or longer run is part of the
        content. Skips backslash-escaped backticks.

        Parameters:
            text: The full source text.
            start: Index to begin scanning from.
            n: The exact backtick run length to match.

        Returns:
            The start index of the closing run, or -1 when none is found.
        """
        i = start
        length = len(text)
        while i < length:
            if text[i] == "\\" and i + 1 < length:
                i += 2
                continue
            if text[i] != "`":
                i += 1
                continue
            run = 0
            j = i
            while j < length and text[j] == "`":
                run += 1
                j += 1
            if run == n:
                return i
            i = j
        return -1

    @staticmethod
    def _normalize_code_content(raw: str) -> str:
        """Normalize raw code span content per CommonMark.

        Newlines become spaces. When the content both begins and ends
        with a space and is not entirely spaces, one leading and one
        trailing space are stripped (so delimiters can pad content that
        starts or ends with a backtick).

        Parameters:
            raw: The text between the opening and closing backtick runs.

        Returns:
            The normalized code span content.
        """
        content = raw.replace("\n", " ")
        if (
            len(content) >= 2
            and content[0] == " "
            and content[-1] == " "
            and content.strip()
        ):
            content = content[1:-1]
        return content

    @staticmethod
    def _find_unescaped_paren(text: str, start: int) -> int:
        """Find the next ``)`` not preceded by a backslash escape.

        Parameters:
            text: The full source text.
            start: Index to begin scanning from.

        Returns:
            The index of the closing paren, or -1 when none is found.
        """
        i = start
        n = len(text)
        while i < n:
            ch = text[i]
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == ")":
                return i
            i += 1
        return -1

    @staticmethod
    def _unescape_destination(url: str) -> str:
        """Unescape backslash escapes in an inline link destination.

        Mirrors the exporter's ``escape_link_destination``: backslash
        before ASCII punctuation yields the punctuation, a backslash
        before any other character is kept literal. Percent-encoded
        bytes (whitespace and control characters the exporter encoded
        for validity) are left intact — they are not a Markdown escape.

        Parameters:
            url: The raw destination text between ``](`` and ``)``.

        Returns:
            The unescaped URL.
        """
        out: list[str] = []
        i = 0
        n = len(url)
        while i < n:
            if url[i] == "\\" and i + 1 < n and url[i + 1] in ESCAPABLE:
                out.append(url[i + 1])
                i += 2
                continue
            out.append(url[i])
            i += 1
        return "".join(out)

    def _parse_emphasis(
        self, text: str, i: int, out: list[str], spans: list[Span], depth: int
    ) -> int | None:
        """Parse an emphasis delimiter run at index i.

        Delimiter runs match by exact length: a run of 2 only closes a
        run of 2. Runs longer than 3 are treated as literal text.

        Parameters:
            text: The full source text.
            i: Index of the first delimiter character.
            out: Output characters accumulated so far.
            spans: Spans accumulated so far.
            depth: Current recursion depth for nested constructs.

        Returns:
            The index after the closing delimiter, or None when the run
            does not form emphasis (it is then emitted literally).
        """
        ch = text[i]
        n = len(text)
        run = 1
        while i + run < n and text[i + run] == ch:
            run += 1
        if run > 3:
            # Runs longer than 3 are not emphasis: emit them literally.
            out.extend(ch * run)
            return i + run
        marker = ch * run
        end = self._find_closing(text, i + run, marker)
        if end == -1:
            return None
        inner_plain, inner_spans = self._parse(text[i + run : end], depth + 1)
        start = len(out)
        out.extend(inner_plain)
        spans.extend(
            (s + start, length, kind, payload)
            for s, length, kind, payload in inner_spans
        )
        styles_by_run = {
            1: [INLINE_STYLES.ITALIC],
            2: [INLINE_STYLES.BOLD],
            3: [INLINE_STYLES.BOLD, INLINE_STYLES.ITALIC],
        }
        for style in styles_by_run[run]:
            spans.append((start, len(inner_plain), "style", style))
        return end + run

    @staticmethod
    def _find_closing(text: str, start: int, marker: str) -> int:
        """Find the closing delimiter, skipping longer runs for singles.

        Parameters:
            text: The full source text.
            start: Index to start searching from.
            marker: The exact delimiter run to find.

        Returns:
            The index of the closing delimiter, or -1 when absent.
        """
        i = start
        while True:
            end = text.find(marker, i)
            if end == -1:
                return -1
            if len(marker) == 1:
                ch = marker
                part_of_longer_run = (end > 0 and text[end - 1] == ch) or (
                    end + 1 < len(text) and text[end + 1] == ch
                )
                if part_of_longer_run:
                    i = end + 1
                    continue
            return end

    def _parse_inline_html(
        self, text: str, i: int, out: list[str], spans: list[Span], depth: int
    ) -> int | None:
        """Parse a whitelisted inline HTML tag at index i.

        Only exact ``<tag>`` openers (no attributes) with a matching
        ``</tag>`` closer are recognized. Anything else is literal text,
        so unwhitelisted or malformed HTML carries no markup semantics.

        Parameters:
            text: The full source text.
            i: Index of the ``<`` character.
            out: Output characters accumulated so far.
            spans: Spans accumulated so far.
            depth: Current recursion depth for nested constructs.

        Returns:
            The index after the closing tag, or None when the tag does
            not parse as a whitelisted construct.
        """
        match = TAG_RE.match(text, i)
        if match is None:
            return None
        tag = match.group(1)
        style = self.inline_html_styles.get(tag)
        if style is None:
            return None
        closing = f"</{tag}>"
        end = text.find(closing, match.end())
        if end == -1:
            return None
        inner_plain, inner_spans = self._parse(text[match.end() : end], depth + 1)
        start = len(out)
        out.extend(inner_plain)
        spans.extend(
            (s + start, length, kind, payload)
            for s, length, kind, payload in inner_spans
        )
        spans.append((start, len(inner_plain), "style", style))
        return end + len(closing)
