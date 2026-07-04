"""Apply regex-based composite decorators to text while rendering blocks."""

import re
from collections.abc import Generator
from operator import itemgetter
from typing import Any

from draftjs_exporter.dom import DOM
from draftjs_exporter.engines.base import DOMEngine
from draftjs_exporter.types import Block, CompositeDecorators, Decorator, Element

br = "\n"
"""Line-break character handled by the default decorator strategy."""

br_strategy = re.compile(r"\n")
"""Default decorator strategy matching single line breaks."""


def get_decorations(
    decorators: CompositeDecorators, text: str
) -> list[tuple[int, int, Any, Decorator]]:
    """Collect non-overlapping decorator matches for the given text.

    Parameters:
        decorators: Composite decorator definitions.
        text: The block text to decorate.

    Returns:
        A sorted list of decorations as ``(start, end, match, decorator)`` tuples.
    """
    occupied: dict[int, int] = {}
    decorations = []

    for decorator in decorators:
        for match in decorator["strategy"].finditer(text):
            begin, end = match.span()
            if not any(occupied.get(i) for i in range(begin, end)):
                for i in range(begin, end):
                    occupied[i] = 1
                decorations.append((begin, end, match, decorator))

    decorations.sort(key=itemgetter(0))

    return decorations


def apply_decorators(
    decorators: CompositeDecorators,
    text: str,
    block: Block,
    blocks: list[Block],
) -> Generator[str, None, None]:
    """Yield decorated text segments and decorator elements for a block.

    Parameters:
        decorators: Composite decorator definitions.
        text: The block text to decorate.
        block: The block currently being rendered.
        blocks: All blocks in the content state.

    Yields:
        Plain text or decorator element nodes covering the full block text.
    """
    decorations = get_decorations(decorators, text)

    pointer = 0
    for begin, end, match, decorator in decorations:
        if pointer < begin:
            yield text[pointer:begin]

        yield DOM.create_element(
            decorator["component"],
            {"match": match, "block": block, "blocks": blocks},
            match.group(0),
        )
        pointer = end

    if pointer < len(text):
        yield text[pointer:]


def render_decorators(
    decorators: CompositeDecorators,
    text: str,
    block: Block,
    blocks: list[Block],
    dom: type[DOMEngine],
) -> Element:
    """Render all decorator output for a block into a single element.

    Parameters:
        decorators: Composite decorator definitions.
        text: The block text to decorate.
        block: The block currently being rendered.
        blocks: All blocks in the content state.
        dom: The active DOM engine.

    Returns:
        A single element containing all decorated text, or the text itself.
    """
    decorated_children = list(apply_decorators(decorators, text, block, blocks))

    if len(decorated_children) == 1:
        decorated_node = decorated_children[0]
    else:
        decorated_node = DOM.create_element()
        for decorated_child in decorated_children:
            dom.append_child(decorated_node, decorated_child)

    return decorated_node


def should_render_decorators(
    decorators: CompositeDecorators,
    text: str,
) -> bool:
    """Return whether decorators need to be processed for the given text.

    Parameters:
        decorators: Composite decorator definitions.
        text: The block text to check.

    Returns:
        True when there are decorators and the default newline-only optimization does not apply.
    """
    nb_decorators = len(decorators)

    if nb_decorators == 0:
        return False

    is_skippable_br = (
        nb_decorators == 1
        and decorators[0]["strategy"] == br_strategy
        and br not in text
    )

    return not is_skippable_br
