"""Markdown entity decorators for images, links, and horizontal rules."""

from draftjs_exporter.markdown.helpers import (
    md_block,
    md_inline,
    md_link_destination,
    md_mark_safe,
)
from draftjs_exporter.types import Component, Element, Props


def md_image(props: Props) -> Element:
    """Render an image as a Markdown image reference.

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
            md_link_destination(props["src"]),
            md_mark_safe(")"),
        ]
    )


def md_link(props: Props) -> Element:
    """Render a link as a Markdown inline reference.

    Parameters:
        props: Render properties including ``children`` and ``url``.

    Returns:
        An inline link element.
    """
    return md_inline(
        [
            md_mark_safe("["),
            props["children"],
            md_mark_safe("]("),
            md_link_destination(props["url"]),
            md_mark_safe(")"),
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
