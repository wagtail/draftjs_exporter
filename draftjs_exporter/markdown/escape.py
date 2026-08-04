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
        "_": "\\_",
        "[": "\\[",
        "]": "\\]",
        "<": "\\<",
        "&": "\\&",
    }
)
"""Characters that must be escaped everywhere, including mid-line."""

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


def escape_text(text: str, at_line_start: bool = False) -> str:
    """Escape Markdown metacharacters in user-controlled text.

    Applies CommonMark backslash escapes. Line-start-sensitive characters
    are only escaped at the start of a line: when ``at_line_start`` is true
    for the first line, and after every embedded newline.

    Parameters:
        text: The user-controlled text to escape. May contain newlines.
        at_line_start: Whether the first character of ``text`` begins a line.

    Returns:
        The escaped text, safe to emit into Markdown output.
    """
    lines = text.split("\n")
    return "\n".join(
        _escape_line(line, at_line_start or i > 0) for i, line in enumerate(lines)
    )


def _escape_line(line: str, at_line_start: bool) -> str:
    """Escape a single line of text.

    Parameters:
        line: One line of user text, without newline characters.
        at_line_start: Whether the line is at the start of a rendered line.

    Returns:
        The escaped line.
    """
    line = line.translate(ANYWHERE_ESCAPES)
    if at_line_start:
        if line[:1] in LINE_START_ESCAPES:
            line = LINE_START_ESCAPES[line[0]] + line[1:]
        else:
            line = ORDERED_LIST_MARKER.sub(r"\1\\\2", line)
    return line
