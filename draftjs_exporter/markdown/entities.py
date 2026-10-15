"""Markdown entity decorators for images, links, and horizontal rules."""

from draftjs_exporter.markdown.helpers import (
    md_block,
    md_inline,
    md_link_destination,
    md_mark_safe,
    md_split_edge_whitespace,
)
from draftjs_exporter.types import Component, Element, Props


def md_image(props: Props) -> Element:
    """Render an image as a Markdown image reference.

    Missing or ``None`` ``src`` renders an image with an empty
    destination (``![alt]()``) rather than raising an error.

    Parameters:
        props: Render properties including ``alt`` and ``src``.

    Returns:
        A block-level image element.
    """
    return md_block(
        [
            md_mark_safe("!["),
            props.get("alt", ""),
            md_mark_safe("]("),
            md_link_destination(props.get("src")),
            md_mark_safe(")"),
        ]
    )


def md_link(props: Props) -> Element:
    """Render a link as a Markdown inline reference.

    Whitespace at the start or end of the link text is moved outside the
    brackets: a link with the text ``" spaced "`` renders as
    ``" [spaced](url) "`` rather than ``"[ spaced ](url)"``.

    Missing or ``None`` ``url`` renders a link with an empty destination
    (``[children]()``) rather than raising an error.

    Parameters:
        props: Render properties including ``children`` and ``url``.

    Returns:
        An inline link element.
    """
    leading, children, trailing = md_split_edge_whitespace(props["children"])
    return md_inline(
        [
            leading,
            md_mark_safe("["),
            children,
            md_mark_safe("]("),
            md_link_destination(props.get("url")),
            md_mark_safe(")"),
            trailing,
        ]
    )


def md_make_horizontal_rule(marker: str) -> Component:
    """Create a horizontal rule component using the given marker.

    Parameters:
        marker: The literal marker characters to render.

    Returns:
        A component that renders a horizontal rule.
    """
    return lambda props: md_block([md_mark_safe(marker)])


md_horizontal_rule: Component = md_make_horizontal_rule("---")
