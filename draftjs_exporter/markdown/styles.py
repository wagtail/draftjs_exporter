"""Markdown inline style components for bold, italic, code, and strikethrough."""

from draftjs_exporter.markdown.helpers import inline
from draftjs_exporter.types import Component


def inline_style(mark: str) -> Component:
    """Create an inline style component that wraps text in the given mark.

    Parameters:
        mark: The delimiter to place before and after the styled text.

    Returns:
        A component that renders the marked inline style.
    """
    return lambda props: inline([mark, props["children"], mark])
