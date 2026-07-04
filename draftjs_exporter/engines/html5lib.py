"""html5lib DOM engine implementation based on BeautifulSoup."""

import re

from draftjs_exporter.engines.base import Attr, DOMEngine
from draftjs_exporter.types import HTML, Element, Tag

try:
    from bs4 import BeautifulSoup

    # Cache empty soup so we can create tags in isolation without the performance overhead.
    soup = BeautifulSoup("", "html5lib")
except ImportError:
    pass

RENDER_RE = re.compile(r"</?(fragment|body|html|head)>")
RENDER_DEBUG_RE = re.compile(r"</?(body|html|head)>")


class DOM_HTML5LIB(DOMEngine):
    """html5lib implementation of the DOM API."""

    @staticmethod
    def create_tag(type_: Tag, attr: Attr | None = None) -> Element:
        """Create and return a new BeautifulSoup tag with the given attributes.

        Parameters:
            type_: The tag name of the element.
            attr: A mapping of attribute names to values.

        Returns:
            The newly created element.
        """
        if not attr:
            attr = {}

        return soup.new_tag(type_, attrs=attr)

    @staticmethod
    def parse_html(markup: HTML) -> Element:
        """Parse arbitrary HTML markup into an element.

        Parameters:
            markup: The HTML string to parse.

        Returns:
            The parsed element.
        """
        return BeautifulSoup(markup, "html5lib")

    @staticmethod
    def append_child(elt: Element, child: Element) -> None:
        """Append the given child node to the children of elt.

        Parameters:
            elt: The parent element.
            child: The child element to append.
        """
        elt.append(child)

    @staticmethod
    def render(elt: Element) -> HTML:
        """Render the given element and its children to HTML.

        Fragment, body, html and head wrappers introduced by BeautifulSoup are
        stripped from the output.

        Parameters:
            elt: The element to render.

        Returns:
            The rendered HTML string.
        """
        return RENDER_RE.sub("", str(elt))

    @staticmethod
    def render_debug(elt: Element) -> HTML:
        """Render the given element to HTML for debugging.

        Only the body, html and head wrappers introduced by BeautifulSoup are
        stripped, leaving fragment tags in place for inspection.

        Parameters:
            elt: The element to render.

        Returns:
            The rendered HTML string.
        """
        return RENDER_DEBUG_RE.sub("", str(elt))
