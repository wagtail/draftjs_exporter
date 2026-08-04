"""Markdown escaping utilities for user-controlled text and link destinations.

This module must only depend on the standard library. It is imported by
``draftjs_exporter.engines.markdown`` at module level; importing other
``draftjs_exporter`` modules here would create circular imports.
"""

import re

# Characters escaped anywhere in text, via str.translate.
# Backslash first is handled naturally: translate is a single pass, and "\"
# maps to "\\" so user backslashes are escaped while inserted ones are not
# re-processed.
ANYWHERE_ESCAPES: dict[int, str] = str.maketrans(
    {
        "\\": "\\\\",
        "`": "\\`",
        "*": "\\*",
        "[": "\\[",
        "]": "\\]",
        "<": "\\<",
    }
)
"""Characters that must be escaped everywhere, including mid-line.

Underscores are deliberately absent: they are handled by
``_escape_underscores``, which only escapes runs that could form emphasis.
"""

# Characters escaped only at the start of a line, where they would open a
# block-level construct. None of these are in ANYWHERE_ESCAPES, so applying
# the line-start rule after the anywhere translate never double-escapes.
LINE_START_ESCAPES: dict[str, str] = {
    "#": "\\#",
    "-": "\\-",
    "+": "\\+",
    ">": "\\>",
    "=": "\\=",
    "|": "\\|",
    "~": "\\~",
}
"""Characters that must be escaped at the start of a line."""

# Ordered list markers: 1-9 digits followed by "." or ")" (CommonMark limit).
ORDERED_LIST_MARKER = re.compile(r"^(\d{1,9})([.)])")
"""Matches an ordered list marker at the start of a line."""

# Underscore runs are escaped only when they could form emphasis.
# CommonMark's flanking rules make a run inert when both adjacent
# characters are alphanumeric, so intraword runs like snake_case pass
# through unescaped. Everywhere else, escaping is conservative: some
# inert runs (e.g. between spaces) are escaped harmlessly.
UNDERSCORE_RUN = re.compile(r"_+")
"""Matches a run of underscores."""

# CommonMark line endings: LF, CRLF, and lone CR. The capture group keeps
# the separators in re.split output so the original endings are preserved.
LINE_ENDING = re.compile(r"(\r\n|\r|\n)")
"""Matches a single CommonMark line ending (``\\r\\n``, ``\\r``, or ``\\n``)."""


def escape_text(text: str, at_line_start: bool = False) -> str:
    r"""Escape Markdown metacharacters in user-controlled text.

    Applies CommonMark backslash escapes. Line-start-sensitive characters
    are only escaped at the start of a line: when ``at_line_start`` is true
    for the first line, and after every embedded line ending. All
    CommonMark line endings (``\n``, ``\r\n``, and lone ``\r``) count as
    line starts, and the original endings are preserved in the output.

    Parameters:
        text: The user-controlled text to escape. May contain line endings.
        at_line_start: Whether the first character of ``text`` begins a line.

    Returns:
        The escaped text, safe to emit into Markdown output.
    """
    segments = LINE_ENDING.split(text)
    # re.split with a capture group keeps the separators at odd indices;
    # only the text segments at even indices are escaped.
    for i in range(0, len(segments), 2):
        segments[i] = _escape_line(segments[i], at_line_start or i > 0)
    return "".join(segments)


def _escape_line(line: str, at_line_start: bool) -> str:
    """Escape a single line of text.

    Line-start rules apply after any leading run of spaces: CommonMark
    allows block constructs to be indented, so ``"  # x"`` is just as
    dangerous as ``"# x"``. Tabs are not stripped: a leading tab already
    makes an indented code block, where escaping is unnecessary.

    Parameters:
        line: One line of user text, without line ending characters.
        at_line_start: Whether the line is at the start of a rendered line.

    Returns:
        The escaped line.
    """
    line = line.translate(ANYWHERE_ESCAPES)
    line = _escape_underscores(line)
    if at_line_start:
        content = line.lstrip(" ")
        indent = line[: len(line) - len(content)]
        if content[:1] in LINE_START_ESCAPES:
            content = LINE_START_ESCAPES[content[0]] + content[1:]
        else:
            content = ORDERED_LIST_MARKER.sub(r"\1\\\2", content)
        line = indent + content
    return line


def _escape_underscores(line: str) -> str:
    """Escape underscore runs that could form emphasis.

    A run is left unescaped only when both adjacent characters are
    alphanumeric, where CommonMark's flanking rules guarantee it can
    neither open nor close emphasis.

    Parameters:
        line: The line to process, with other escapes already applied.

    Returns:
        The line with escapable underscore runs backslash-escaped.
    """

    def replace(match: re.Match[str]) -> str:
        run = match.group(0)
        before = line[match.start() - 1] if match.start() > 0 else ""
        after = line[match.end()] if match.end() < len(line) else ""
        if before.isalnum() and after.isalnum():
            return run
        return "\\_" * len(run)

    return UNDERSCORE_RUN.sub(replace, line)


def escape_link_destination(url: str) -> str:
    """Escape a URL for use as an inline link destination inside ``](…)``.

    Backslash-escapes backslashes and parentheses (which would otherwise
    break out of the destination), and percent-encodes ASCII whitespace and
    control characters, which inline destinations may not contain. URL
    scheme validation is out of scope: it is the integrator's
    responsibility (see ``docs/SECURITY.md``).

    Parameters:
        url: The URL to escape.

    Returns:
        The escaped destination.
    """
    escaped = url.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return "".join(
        char if char > " " and char != "\x7f" else f"%{ord(char):02X}"
        for char in escaped
    )


def longest_run(text: str, char: str) -> int:
    """Compute the length of the longest run of a character in a string.

    Parameters:
        text: The string to scan.
        char: The single character to count runs of.

    Returns:
        The longest run length, or ``0`` if the character is absent.
    """
    best = current = 0
    for c in text:
        current = current + 1 if c == char else 0
        best = max(best, current)
    return best


def code_span_delimiters(content: str) -> tuple[str, str]:
    """Compute opening and closing delimiters for an inline code span.

    The delimiter is one backtick longer than the longest backtick run in
    the content. When the content starts or ends with a backtick, a space
    is added inside the delimiters, per CommonMark.

    Parameters:
        content: The raw code span content.

    Returns:
        A tuple of ``(opening, closing)`` delimiter strings.
    """
    ticks = "`" * max(1, longest_run(content, "`") + 1)
    pad = " " if content.startswith("`") or content.endswith("`") else ""
    return ticks + pad, pad + ticks


def code_block_fence(content: str, fence_char: str) -> str:
    """Compute a code fence that cannot be broken by the content.

    The fence is one character longer than the longest run of the fence
    character in the content, and at least three characters long.

    Parameters:
        content: The raw code block content.
        fence_char: The fence character (backtick or tilde).

    Returns:
        The fence string.
    """
    return fence_char * max(3, longest_run(content, fence_char) + 1)
