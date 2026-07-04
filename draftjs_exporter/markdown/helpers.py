"""Low-level helper components for inline and block Markdown fragments."""

from draftjs_exporter.dom import DOM
from draftjs_exporter.types import Element


def inline(children: list[str | Element]) -> Element:
    """Create an inline fragment for inline formatting such as bold, links, and code.

    Parameters:
        children: The strings and elements to group inline.

    Returns:
        A fragment containing the children without extra whitespace.
    """
    return DOM.create_element("fragment", {}, children)


def block(children: list[str | Element]) -> Element:
    """Create a block fragment followed by an empty line.

    Parameters:
        children: The strings and elements that form the block content.

    Returns:
        A fragment containing the children and a trailing blank line.
    """
    return DOM.create_element("fragment", {}, children + ["\n\n"])
