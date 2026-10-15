"""Low-level helper components for inline and block Markdown fragments."""

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.escape import md_escape_link_destination
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


def md_link_destination(url: str | None) -> Element:
    """Create an element holding a link or image URL for ``](…)``.

    Parameters:
        url: The URL to escape and emit, or ``None`` when the destination
            is absent.

    Returns:
        An element rendering the escaped URL without further escaping.
    """
    return md_mark_safe(md_escape_link_destination(url))


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


def _md_split_leading(node: Element) -> tuple[str, Element]:
    """Split the leading spaces and tabs off an inline node.

    Parameters:
        node: A string or fragment element to split.

    Returns:
        A ``(leading, node)`` tuple, where ``node`` no longer has its
        leading spaces.
    """
    if isinstance(node, str):
        stripped = node.lstrip(" \t")
        return node[: len(node) - len(stripped)], stripped

    if getattr(node, "type", None) != "fragment" or not node.children:
        return "", node

    leading, first = _md_split_leading(node.children[0])
    node.children[0] = first
    return leading, node


def _md_split_trailing(node: Element) -> tuple[Element, str]:
    """Split the trailing spaces and tabs off an inline node.

    Parameters:
        node: A string or fragment element to split.

    Returns:
        A ``(node, trailing)`` tuple, where ``node`` no longer has its
        trailing spaces.
    """
    if isinstance(node, str):
        stripped = node.rstrip(" \t")
        return stripped, node[len(stripped) :]

    if getattr(node, "type", None) != "fragment" or not node.children:
        return node, ""

    last, trailing = _md_split_trailing(node.children[-1])
    node.children[-1] = last
    return node, trailing


def md_split_edge_whitespace(node: Element) -> tuple[str, Element, str]:
    """Move leading and trailing spaces out of an inline node.

    Emphasis and link delimiters must not enclose edge whitespace
    (``**bold**``, not ``**bold **``), so styles and links spanning a text
    segment boundary have to push spaces at their edges outside the
    delimiters. Only spaces and tabs are moved: moving a newline out would
    turn a hard line break into plain text.

    Only the outer edges are moved, so spaces between the children of a
    fragment stay where they are.

    Parameters:
        node: A string or fragment element to split.

    Returns:
        A ``(leading, node, trailing)`` tuple. ``node`` is mutated in place
        when it is a fragment, with its outer edges stripped.
    """
    leading, node = _md_split_leading(node)
    node, trailing = _md_split_trailing(node)
    return leading, node, trailing


def md_has_content(node: Element) -> bool:
    """Whether an inline node renders anything other than spaces and tabs.

    Stripping edge whitespace can leave a node that still has children, but
    only whitespace ones, so it renders nothing once the delimiters around
    it are removed. Callers use this to drop those empty delimiters.

    Parameters:
        node: A string or fragment element to inspect.

    Returns:
        ``True`` if ``node`` holds text or markup, ignoring whitespace.
    """
    if isinstance(node, str):
        return bool(node.strip(" \t"))

    if getattr(node, "type", None) != "fragment":
        return True

    children = getattr(node, "children", None)
    if not children:
        return False

    return any(md_has_content(child) for child in children)
