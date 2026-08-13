"""Low-level helper components for inline and block Markdown fragments."""

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.escape import escape_link_destination
from draftjs_exporter.types import Element


def md_mark_safe(markup: str, block_prefix: bool = False) -> Element:
    """Create an element holding structural Markdown syntax.

    The Markdown engine renders ``mark_safe`` markup verbatim, without the
    escaping applied to plain text children. Every piece of structural
    syntax emitted by Markdown components must be wrapped with this helper.

    Parameters:
        markup: The structural Markdown to emit (markers, fences, spacing).
        block_prefix: Whether text following this markup can start a nested
            block. True for list markers, list indentation, and blockquote
            ``"> "`` prefixes; false for heading prefixes and inline marks.

    Returns:
        An element the Markdown engine renders without escaping.
    """
    return DOM.create_element(
        "mark_safe", {"markup": markup, "block_prefix": block_prefix}
    )


def md_link_destination(url: str) -> Element:
    """Create an element holding a link or image URL for ``](…)``.

    Parameters:
        url: The URL to escape and emit.

    Returns:
        An element rendering the escaped URL without further escaping.
    """
    return md_mark_safe(escape_link_destination(url))


def md_inline(children: list[str | Element]) -> Element:
    """Create an inline fragment for inline formatting such as bold, links, and code.

    Parameters:
        children: The strings and elements to group inline.

    Returns:
        A fragment containing the children without extra whitespace.
    """
    return DOM.create_element("fragment", {}, children)


def md_block(children: list[str | Element]) -> Element:
    """Create a block fragment followed by an empty line.

    Parameters:
        children: The strings and elements that form the block content.

    Returns:
        A fragment containing the children and a trailing blank line.
    """
    return DOM.create_element("fragment", {}, children + [md_mark_safe("\n\n")])
