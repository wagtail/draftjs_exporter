"""List item utilities: numbering, prefixes, and spacing between consecutive items."""

from collections.abc import Callable

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.helpers import md_mark_safe
from draftjs_exporter.types import Block, Element, Props


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


def md_get_li_suffix(props: Props) -> str:
    r"""Choose a list item suffix based on the following block type.

    Parameters:
        props: Render properties including the current block and all blocks.

    Returns:
        ``"\n\n"`` when the next block is a different type, otherwise ``"\n"``.
    """
    key = props["block"].get("key")

    if not key:
        return "\n"

    blocks = props["blocks"]
    i = md_get_block_index(blocks, key)
    next_block_type = blocks[i + 1]["type"] if i + 1 < len(blocks) else None

    return "\n\n" if next_block_type != props["block"]["type"] else "\n"


def md_make_numbered_li_prefix(delimiter: str) -> Callable[[Props], str]:
    """Create a function that computes an ordered list item prefix.

    The returned function counts preceding list items at the same depth
    within the same list type.

    Parameters:
        delimiter: The delimiter to place after the item number.

    Returns:
        A function accepting props and returning the prefix string.
    """

    def get_prefix(props: Props) -> str:
        type_ = props["block"]["type"]
        depth = props["block"]["depth"]
        key = props["block"].get("key")

        if not key:
            return " "

        index = 1
        for b in props["blocks"]:
            # This is the current block, stop there.
            if b.get("key") == key:
                break

            # The block's list hasn't started yet: reset the index.
            if b.get("type") != type_:
                index = 1
            else:
                b_depth = b.get("depth", 0)
                # We are in the list, but the depth is lower than that of our block: reset.
                if b_depth < depth:
                    index = 1
                # Same list, same depth as our block: increment.
                elif b_depth == depth:
                    index += 1

        return f"{index}{delimiter} "

    return get_prefix


md_get_numbered_li_prefix: Callable[[Props], str] = md_make_numbered_li_prefix(".")


def md_list_item(prefix: str, props: Props) -> Element:
    """Render a single Markdown list item with indentation and suffix.

    Parameters:
        prefix: The list marker prefix, including any trailing space.
        props: Render properties including the current block and all blocks.

    Returns:
        A fragment containing the indented prefix, children, and trailing newline.
    """
    indent = "  " * props["block"]["depth"]
    suffix = md_get_li_suffix(props)

    return DOM.create_element(
        "fragment",
        {},
        [
            md_mark_safe(indent, block_prefix=True),
            md_mark_safe(prefix, block_prefix=True),
            props["children"],
            md_mark_safe(suffix),
        ],
    )
