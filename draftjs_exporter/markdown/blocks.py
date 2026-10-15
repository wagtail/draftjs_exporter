"""Markdown block-level components: headings, lists, blockquotes, and plain paragraphs."""

from draftjs_exporter.constants import BLOCK_TYPES
from draftjs_exporter.markdown.helpers import md_block, md_inline, md_mark_safe
from draftjs_exporter.markdown.lists import (
    md_get_block_index,
    md_make_list_item,
)
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


def md_blockquote(props: Props) -> Element:
    """Render a blockquote paragraph, joining consecutive quote paragraphs.

    Draft.js quotes are one block per paragraph, but a multi-paragraph quote
    is a single Markdown blockquote: consecutive blockquote blocks are
    separated by an empty quote line (``>``) rather than a blank line, which
    would end the quote.

    Parameters:
        props: Render properties including the current block and all blocks.

    Returns:
        A blockquote paragraph element.
    """
    blocks = props["blocks"]
    # A block with no usable key cannot be looked up: a falsy key would match
    # any other block that lacks one.
    key = props["block"].get("key")
    index = md_get_block_index(blocks, key) if key else -1
    next_type = (
        blocks[index + 1].get("type")
        if 0 <= index and index + 1 < len(blocks)
        else None
    )
    trailing = "\n>\n" if next_type == BLOCK_TYPES.BLOCKQUOTE else "\n\n"
    return md_inline(
        [
            md_mark_safe("> ", block_prefix=True),
            props["children"],
            md_mark_safe(trailing),
        ]
    )


def md_make_ul(marker: str) -> Component:
    """Create an unordered list item component using the given marker.

    The ordered delimiter is only used to measure the content column of
    ordered ancestors, so the default one is enough here.

    Parameters:
        marker: The marker character to use for each list item.

    Returns:
        A component that renders one unordered list item.
    """
    return md_make_list_item(marker, ".")


def md_make_ol(delimiter: str) -> Component:
    """Create an ordered list item component using the given delimiter.

    The unordered marker is only used to measure the content column of
    unordered ancestors, so the default one is enough here.

    Parameters:
        delimiter: The delimiter to place after the item number.

    Returns:
        A component that renders one ordered list item.
    """
    return md_make_list_item("-", delimiter)


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
