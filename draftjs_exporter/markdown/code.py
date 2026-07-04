"""Markdown code block components and fenced code builders."""

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.lists import get_li_suffix
from draftjs_exporter.types import Component, Element, Props


def make_code_element(fence: str) -> Component:
    """Create a code-block element component using the given fence.

    Parameters:
        fence: The delimiter to use at the closing of the code block.

    Returns:
        A component that renders the contents and closing fence of a code block.
    """

    def element(props: Props) -> Element:
        suffix = get_li_suffix(props)
        block_end = f"\n{fence}" if suffix == "\n\n" else ""
        return DOM.create_element(
            "fragment", {}, [props["children"], block_end, suffix]
        )

    return element


def make_code_wrapper(fence: str) -> Component:
    """Create a code-block wrapper component using the given fence.

    Parameters:
        fence: The delimiter to place at the start of the code block.

    Returns:
        A component that renders only the opening fence.
    """
    prefix = f"{fence}\n"
    return lambda props: DOM.create_element("fragment", {}, [prefix])


code_element: Component = make_code_element("```")
code_wrapper: Component = make_code_wrapper("```")
