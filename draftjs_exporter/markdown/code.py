"""Markdown code block components and fenced code builders."""

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.helpers import md_mark_safe
from draftjs_exporter.types import Component, Element, Props


def md_make_code_element() -> Component:
    """Create a code-block line component.

    Each Draft.js code block contributes one line to the shared code_block
    node created by the wrapper.

    Returns:
        A component that renders one line of code block content.
    """

    def element(props: Props) -> Element:
        return DOM.create_element(
            "fragment", {}, [props["children"], md_mark_safe("\n")]
        )

    return element


def md_make_code_wrapper(fence: str) -> Component:
    """Create a code-block wrapper component using the given fence.

    Parameters:
        fence: The fence delimiter; its first character sizes the rendered
            fence (`` ``` `` or ``~~~``).

    Returns:
        A component that creates the code_block node holding all lines.
    """
    fence_char = fence[0]
    return lambda props: DOM.create_element("code_block", {"fence": fence_char})


md_code_element: Component = md_make_code_element()
md_code_wrapper: Component = md_make_code_wrapper("```")
