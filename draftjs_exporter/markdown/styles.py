"""Markdown inline style components for bold, italic, code, and strikethrough."""

from draftjs_exporter.dom import DOM
from draftjs_exporter.markdown.helpers import (
    md_has_content,
    md_inline,
    md_mark_safe,
    md_split_edge_whitespace,
)
from draftjs_exporter.types import Component, Element, Props


def md_inline_style(mark: str) -> Component:
    """Create an inline style component that wraps text in the given mark.

    Whitespace at the edges of the styled text is moved outside the marks:
    a style spanning a link is rendered per text segment, so an edge space
    would otherwise sit inside the delimiters (``**bold **``), where it is
    not valid emphasis. Styled text that is only whitespace renders without
    the marks, which would otherwise be empty.

    Parameters:
        mark: The delimiter to place before and after the styled text.

    Returns:
        A component that renders the marked inline style.
    """

    def component(props: Props) -> Element:
        leading, children, trailing = md_split_edge_whitespace(props["children"])
        if not md_has_content(children):
            return md_inline([leading, children, trailing])
        return md_inline(
            [leading, md_mark_safe(mark), children, md_mark_safe(mark), trailing]
        )

    return component


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
