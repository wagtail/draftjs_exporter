"""List item utilities: numbering, prefixes, indentation, and spacing."""

from collections.abc import Callable

from draftjs_exporter.constants import BLOCK_TYPES
from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.helpers import md_mark_safe
from draftjs_exporter.types import Block, Component, Element, Props

LIST_ITEM_TYPES = (
    BLOCK_TYPES.UNORDERED_LIST_ITEM,
    BLOCK_TYPES.ORDERED_LIST_ITEM,
)
"""Draft.js block types rendered as list items."""


def md_get_block_index(blocks: list[Block], key: str) -> int:
    """Find the index of the block with the given key.

    Parameters:
        blocks: The sequence of blocks to search.
        key: The block key to locate.

    Returns:
        The block index, or ``-1`` if the key is not found.
    """
    keys = [i for i in range(len(blocks)) if blocks[i].get("key") == key]
    return keys[0] if keys else -1


def md_get_li_number(props: Props) -> int:
    """Compute the number of an ordered list item within its list.

    Counts preceding items of the same type and depth, skipping over nested
    items of any type. The scan stops at any block that is not a list item
    (including one without a type), at a shallower item, or at a list of
    another type at the same depth.

    Parameters:
        props: Render properties including the current block and all blocks.

    Returns:
        The one-based item number.
    """
    block = props["block"]
    key = block.get("key")
    blocks = props["blocks"]

    if not key:
        return 1

    index = md_get_block_index(blocks, key)
    # An unknown key is treated as if the block came after every known block,
    # matching the historical behavior of counting all preceding items.
    if index == -1:
        index = len(blocks)

    depth = block.get("depth", 0)
    number = 1
    for previous in reversed(blocks[:index]):
        previous_depth = previous.get("depth", 0)
        if previous.get("type") not in LIST_ITEM_TYPES or previous_depth < depth:
            break
        if previous_depth == depth:
            if previous.get("type") != block.get("type"):
                break
            number += 1

    return number


def md_make_numbered_li_prefix(delimiter: str) -> Callable[[Props], str]:
    """Create a function that computes an ordered list item prefix.

    Parameters:
        delimiter: The delimiter to place after the item number.

    Returns:
        A function accepting props and returning the prefix string.
    """

    def get_prefix(props: Props) -> str:
        if not props["block"].get("key"):
            return " "
        return f"{md_get_li_number(props)}{delimiter} "

    return get_prefix


def md_get_li_suffix(props: Props) -> str:
    r"""Choose a list item suffix based on the following block.

    A blank line ends the list, unless the next item belongs to it: it is
    nested, or continues a list of the same type at its depth.

    Parameters:
        props: Render properties including the current block and all blocks.

    Returns:
        ``"\n\n"`` when the list ends, otherwise ``"\n"``.
    """
    block = props["block"]
    key = block.get("key")
    if not key:
        return "\n"

    blocks = props["blocks"]
    index = md_get_block_index(blocks, key)
    # A key that is not in blocks has no following block to continue the list.
    if index == -1:
        return "\n\n"

    next_block = blocks[index + 1] if index + 1 < len(blocks) else None
    if next_block is None or next_block.get("type") not in LIST_ITEM_TYPES:
        return "\n\n"

    next_depth = next_block.get("depth", 0)
    for previous in reversed(blocks[: index + 1]):
        previous_depth = previous.get("depth", 0)
        if previous.get("type") not in LIST_ITEM_TYPES or previous_depth < next_depth:
            break
        if previous_depth == next_depth:
            return "\n" if previous.get("type") == next_block.get("type") else "\n\n"

    return "\n"


def md_get_li_marker_width(
    block: Block, blocks: list[Block], marker: str, delimiter: str
) -> int:
    """Return the width of a list item marker, including its trailing space.

    Parameters:
        block: The list item block whose marker width to compute.
        blocks: All blocks in the content state.
        marker: The unordered list marker in use.
        delimiter: The ordered list delimiter in use.

    Returns:
        The marker width, used to indent nested items to the content column.
    """
    if block.get("type") == BLOCK_TYPES.ORDERED_LIST_ITEM:
        number = md_get_li_number({"block": block, "blocks": blocks})
        return len(str(number)) + len(delimiter) + 1
    return len(marker) + 1


def md_get_li_indent(props: Props, marker: str, delimiter: str) -> str:
    """Indent a nested list item to its ancestors' content columns.

    Each nesting level is indented by the width of the marker of the item it
    is nested under, which depends on that ancestor's number width
    (``"- "`` vs ``"1. "`` vs ``"10. "``).

    An ancestor that cannot be resolved, because the key is unknown or no
    block sits at that depth, indents by two spaces instead: the width of the
    default unordered marker.

    Parameters:
        props: Render properties including the current block and all blocks.
        marker: The unordered list marker in use.
        delimiter: The ordered list delimiter in use.

    Returns:
        The indentation string for the current item.
    """
    depth: int = int(props["block"].get("depth", 0))
    if not depth:
        return ""

    blocks: list[Block] = props["blocks"]
    index = md_get_block_index(blocks, props["block"].get("key", ""))
    if index == -1:
        return "  " * depth

    widths: dict[int, int] = {}
    for previous in reversed(blocks[:index]):
        if previous.get("type") not in LIST_ITEM_TYPES or len(widths) == depth:
            break
        previous_depth = previous.get("depth", 0)
        if previous_depth < depth and previous_depth not in widths:
            widths[previous_depth] = md_get_li_marker_width(
                previous, blocks, marker, delimiter
            )

    return "".join(" " * widths.get(level, 2) for level in range(depth))


def md_make_list_item(marker: str, delimiter: str) -> Component:
    """Create a list item component with nesting indentation and numbering.

    A block with no usable key renders as plain text, because the exporter
    creates such blocks for the wrapper nodes that nest lists, and those must
    not produce a list item of their own.

    Both values also measure the content column of ancestors, whichever list
    type they belong to, so a component configured for one list type still
    needs the other type's value.

    Parameters:
        marker: The unordered list marker, without its trailing space.
        delimiter: The ordered list delimiter placed after the item number.

    Returns:
        A component that renders one list item.
    """
    get_numbered_prefix = md_make_numbered_li_prefix(delimiter)

    def get_prefix(props: Props) -> str:
        if props["block"].get("type") == BLOCK_TYPES.ORDERED_LIST_ITEM:
            return get_numbered_prefix(props)
        return f"{marker} "

    def component(props: Props) -> Element:
        block = props["block"]
        # Synthetic block used by the exporter for nesting wrappers, with no
        # key. Blocks with no usable key get the same treatment as the other
        # helpers give them.
        if not block.get("key"):
            return DOM.create_element("fragment", {}, [props["children"]])
        return DOM.create_element(
            "fragment",
            {},
            [
                md_mark_safe(
                    md_get_li_indent(props, marker, delimiter), block_prefix=True
                ),
                md_mark_safe(get_prefix(props), block_prefix=True),
                props["children"],
                md_mark_safe(md_get_li_suffix(props)),
            ],
        )

    return component
