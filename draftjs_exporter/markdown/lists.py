from collections.abc import Callable

from draftjs_exporter.dom import DOM
from draftjs_exporter.types import Block, Element, Props


def get_block_index(blocks: list[Block], key: str) -> int:
    """Retrieves the index at which a given block is, or -1 if not found."""
    keys = [i for i in range(len(blocks)) if blocks[i].get("key") == key]
    return keys[0] if keys else -1


def get_li_suffix(props: Props) -> str:
    """Determines the suffix for list items (newline, or double newline) based on the next block."""
    key = props["block"].get("key")

    if not key:
        return "\n"

    blocks = props["blocks"]
    i = get_block_index(blocks, key)
    next_block_type = blocks[i + 1]["type"] if i + 1 < len(blocks) else None

    return "\n\n" if next_block_type != props["block"]["type"] else "\n"


def make_numbered_li_prefix(delimiter: str) -> Callable[[Props], str]:
    """Returns a prefix function using the given delimiter ('.' or ')')."""

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


get_numbered_li_prefix: Callable[[Props], str] = make_numbered_li_prefix(".")


def list_item(prefix: str, props: Props) -> Element:
    """List item formatting - not really inline, not really a block either."""
    indent = "  " * props["block"]["depth"]
    suffix = get_li_suffix(props)

    return DOM.create_element(
        "fragment", {}, [indent, prefix, props["children"], suffix]
    )
