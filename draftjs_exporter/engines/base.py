"""Defines the DOMEngine interface implemented by all DOM engines."""

from typing import Any, TypeAlias

from draftjs_exporter.types import HTML, Element, Tag

Attr: TypeAlias = dict[str, str]


class DOMEngine:
    """Parent class of all DOM implementations."""

    @staticmethod
    def create_tag(type_: Tag, attr: Attr | None = None) -> Any:
        """Create and return a new element of the given type and attributes.

        Parameters:
            type_: The tag name of the element.
            attr: A mapping of attribute names to values.

        Returns:
            The newly created element.
        """
        raise NotImplementedError

    @staticmethod
    def parse_html(markup: HTML) -> Element:
        """Parse arbitrary HTML markup into an element.

        This method is used in component implementations only, and is not
        required for the exporter to operate.

        Parameters:
            markup: The HTML string to parse.

        Returns:
            The parsed element.
        """
        raise NotImplementedError

    @staticmethod
    def append_child(elt: Element, child: Element) -> Any:
        """Append the given child node to the children of elt.

        Parameters:
            elt: The parent element.
            child: The child element to append.

        Returns:
            The parent element, or the value returned by the underlying engine.
        """
        raise NotImplementedError

    @staticmethod
    def render(elt: Element) -> HTML:
        """Render the given element and its children to HTML.

        Parameters:
            elt: The element to render.

        Returns:
            The rendered HTML string.
        """
        raise NotImplementedError

    @staticmethod
    def render_debug(elt: Element) -> HTML:
        """Render the given element to HTML for debugging.

        Used in the exporter's tests, this method is not required for the
        exporter to operate.

        Parameters:
            elt: The element to render.

        Returns:
            The rendered HTML string.
        """
        raise NotImplementedError
