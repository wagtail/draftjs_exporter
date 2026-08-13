"""Markdown inline style components for bold, italic, code, and strikethrough."""

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.helpers import md_inline, md_mark_safe
from draftjs_exporter.types import Component, Element, Props


def md_inline_style(mark: str) -> Component:
    """Create an inline style component that wraps text in the given mark.

    Parameters:
        mark: The delimiter to place before and after the styled text.

    Returns:
        A component that renders the marked inline style.
    """
    return lambda props: md_inline(
        [md_mark_safe(mark), props["children"], md_mark_safe(mark)]
    )


def md_code_span(props: Props) -> Element:
    """Render inline code as a code span.

    The engine emits the content unescaped, with delimiters sized to the
    content's backtick runs.

    Parameters:
        props: Render properties including ``children``.

    Returns:
        A code_span element.
    """
    return DOM.create_element("code_span", {}, props["children"])
