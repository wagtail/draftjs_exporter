"""Markdown block-level components: headings, lists, blockquotes, and plain paragraphs."""

from draftjs_exporter.markdown.helpers import block, inline
from draftjs_exporter.markdown.lists import list_item, make_numbered_li_prefix
from draftjs_exporter.types import Component, Element, Props


def prefixed_block(prefix: str) -> Component:
    """Create a block component that prefixes its children with the given string.

    Parameters:
        prefix: The literal prefix to insert before the block's children.

    Returns:
        A component that renders the prefixed block.
    """
    return lambda props: block([prefix, props["children"]])


def make_ul(marker: str) -> Component:
    """Create an unordered list item component using the given marker.

    Parameters:
        marker: The marker character to use for each list item.

    Returns:
        A component that renders one unordered list item.
    """
    prefix = f"{marker} "
    return lambda props: list_item(prefix, props)


def make_ol(delimiter: str) -> Component:
    """Create an ordered list item component using the given delimiter.

    Parameters:
        delimiter: The delimiter to place after the item number.

    Returns:
        A component that renders one ordered list item.
    """
    get_prefix = make_numbered_li_prefix(delimiter)
    return lambda props: list_item(get_prefix(props), props)


def list_wrapper(props: Props) -> Element:
    """Render a list wrapper as an empty inline fragment.

    Markdown lists are built from individual items, so no extra wrapper
    markup is required.

    Parameters:
        props: Render properties passed by the engine.

    Returns:
        An empty fragment that lets list items sit next to each other.
    """
    return inline([])


ul: Component = make_ul("-")
ol: Component = make_ol(".")
