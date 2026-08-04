"""Markdown entity decorators for images, links, and horizontal rules."""

from draftjs_exporter.markdown.helpers import block, inline, link_destination, mark_safe
from draftjs_exporter.types import Component, Element, Props


def image(props: Props) -> Element:
    """Render an image as a Markdown image reference.

    Parameters:
        props: Render properties including ``alt`` and ``src``.

    Returns:
        A block-level image element.
    """
    return block(
        [
            mark_safe("!["),
            props.get("alt", ""),
            mark_safe("]("),
            link_destination(props["src"]),
            mark_safe(")"),
        ]
    )


def link(props: Props) -> Element:
    """Render a link as a Markdown inline reference.

    Parameters:
        props: Render properties including ``children`` and ``url``.

    Returns:
        An inline link element.
    """
    return inline(
        [
            mark_safe("["),
            props["children"],
            mark_safe("]("),
            link_destination(props["url"]),
            mark_safe(")"),
        ]
    )


def make_horizontal_rule(marker: str) -> Component:
    """Create a horizontal rule component using the given marker.

    Parameters:
        marker: The literal marker characters to render.

    Returns:
        A component that renders a horizontal rule.
    """
    return lambda props: block([mark_safe(marker)])


horizontal_rule: Component = make_horizontal_rule("---")
