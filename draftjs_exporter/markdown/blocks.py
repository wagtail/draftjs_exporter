"""Markdown block-level components: headings, lists, blockquotes, and plain paragraphs."""

from draftjs_exporter.markdown.helpers import md_block, md_inline, md_mark_safe
from draftjs_exporter.markdown.lists import md_list_item, md_make_numbered_li_prefix
from draftjs_exporter.types import Component, Element, Props


def md_prefixed_block(prefix: str, block_prefix: bool = False) -> Component:
    """Create a block component that prefixes its children with the given string.

    Parameters:
        prefix: The literal prefix to insert before the block's children.
        block_prefix: Whether children can start a nested block after the
            prefix (true for blockquotes, false for headings).

    Returns:
        A component that renders the prefixed block.
    """
    return lambda props: md_block(
        [md_mark_safe(prefix, block_prefix=block_prefix), props["children"]]
    )


def md_make_ul(marker: str) -> Component:
    """Create an unordered list item component using the given marker.

    Parameters:
        marker: The marker character to use for each list item.

    Returns:
        A component that renders one unordered list item.
    """
    prefix = f"{marker} "
    return lambda props: md_list_item(prefix, props)


def md_make_ol(delimiter: str) -> Component:
    """Create an ordered list item component using the given delimiter.

    Parameters:
        delimiter: The delimiter to place after the item number.

    Returns:
        A component that renders one ordered list item.
    """
    get_prefix = md_make_numbered_li_prefix(delimiter)
    return lambda props: md_list_item(get_prefix(props), props)


def md_list_wrapper(props: Props) -> Element:
    """Render a list wrapper as an empty inline fragment.

    Markdown lists are built from individual items, so no extra wrapper
    markup is required.

    Parameters:
        props: Render properties passed by the engine.

    Returns:
        An empty fragment that lets list items sit next to each other.
    """
    return md_inline([])


md_ul: Component = md_make_ul("-")
md_ol: Component = md_make_ol(".")
