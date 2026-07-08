"""lxml DOM engine implementation."""

import re
from typing import no_type_check

from lxml import etree, html

from draftjs_exporter.engines.base import Attr, DOMEngine
from draftjs_exporter.types import HTML, Tag

NSMAP = {"xlink": "http://www.w3.org/1999/xlink"}

RENDER_RE = re.compile(r"</?fragment>")


class DOM_LXML(DOMEngine):
    """lxml implementation of the DOM API."""

    @staticmethod
    def create_tag(type_: Tag, attr: Attr | None = None) -> etree.Element:
        """Create and return a new lxml element with the given attributes.

        Parameters:
            type_: The tag name of the element.
            attr: A mapping of attribute names to values.

        Returns:
            The newly created element.
        """
        nsmap = None

        if attr:
            if "xlink:href" in attr:
                attr[f"{{{NSMAP['xlink']}}}href"] = attr.pop("xlink:href")
                nsmap = NSMAP

        elt = etree.Element(type_, attrib=attr, nsmap=nsmap)
        # libxml2's HTML serializer omits the closing tag of some elements
        # (e.g. <li>, <td>) when they have neither text nor children – its
        # `.text` is `None`, not just empty. Void elements (<hr>, <img>, …)
        # are unaffected, so this keeps output consistent with the other
        # engines without needing to track which tags are void ourselves.
        elt.text = ""

        return elt

    @staticmethod
    def parse_html(markup: HTML) -> etree.Element:
        """Parse arbitrary HTML markup into an lxml element.

        Parameters:
            markup: The HTML string to parse.

        Returns:
            The parsed element.
        """
        return html.fromstring(markup)

    # Remove soon - see below.
    @no_type_check
    @staticmethod
    # def append_child(elt: etree.Element, child: etree.Element) -> None:
    def append_child(elt: etree.Element, child: etree.Element) -> None:
        """Append the given child node to the children of elt.

        Text children are wrapped in a fragment element before appending.

        Parameters:
            elt: The parent element.
            child: The child element or text to append.
        """
        # Compatibility with lxml below 6.0.0 on Python 3.10. Revert once we drop support for Python 3.10.
        # if isinstance(child, etree.Element):
        if hasattr(child, "tag"):
            elt.append(child)
        else:
            c = etree.Element("fragment")
            c.text = child
            elt.append(c)

    @staticmethod
    def render(elt: etree.Element) -> HTML:
        """Render the given element and its children to HTML.

        Fragment wrappers used for text nodes are stripped from the output.

        Parameters:
            elt: The element to render.

        Returns:
            The rendered HTML string.
        """
        return RENDER_RE.sub("", etree.tostring(elt, method="html", encoding="unicode"))

    @staticmethod
    def render_debug(elt: etree.Element) -> HTML:
        """Render the given element to HTML for debugging.

        Fragment wrappers used for text nodes are preserved so the tree
        structure is easier to inspect.

        Parameters:
            elt: The element to render.

        Returns:
            The rendered HTML string.
        """
        return etree.tostring(elt, method="html", encoding="unicode")
