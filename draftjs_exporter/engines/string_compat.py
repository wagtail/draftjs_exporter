"""Backwards-compatible variant of the string DOM engine."""

from html import escape

from draftjs_exporter.engines.base import Attr
from draftjs_exporter.engines.string import VOID_ELEMENTS, DOMString, Elt
from draftjs_exporter.types import HTML


class DOMStringCompat(DOMString):
    """String DOM engine that preserves legacy rendering behavior."""

    @staticmethod
    def render_attrs(attr: Attr) -> str:
        """Render attributes with backwards-compatible alphabetical ordering.

        Parameters:
            attr: The attributes to render.

        Returns:
            The rendered attribute string.
        """
        attrs = [f' {k}="{escape(v)}"' for k, v in attr.items()]
        # Compat: reverts "Remove HTML attributes alphabetical sorting of default string engine ([#129](https://github.com/wagtail/draftjs_exporter/pull/129))"
        attrs.sort()
        return "".join(attrs)

    @staticmethod
    def render_children(children: list[HTML | Elt]) -> HTML:
        """Render children with backwards-compatible quote escaping.

        Parameters:
            children: A list of strings and elements to render.

        Returns:
            The concatenated child content.
        """
        return "".join(
            [
                DOMStringCompat.render(c)
                if isinstance(c, Elt)
                # Compat: reverts "Disable single and double quotes escaping outside of attributes for string engine ([#129](https://github.com/wagtail/draftjs_exporter/pull/129))"
                else escape(c, quote=True)
                for c in children
            ]
        )

    @staticmethod
    def render(elt: Elt) -> HTML:
        """Render the given element to HTML, expanding fragments into children.

        Parameters:
            elt: The element to render.

        Returns:
            The rendered HTML string.
        """
        type_ = elt.type
        attr = DOMStringCompat.render_attrs(elt.attr) if elt.attr else ""
        children = DOMStringCompat.render_children(elt.children) if elt.children else ""

        if type_ == "fragment":
            return children

        if type_ in VOID_ELEMENTS:
            return f"<{type_}{attr}/>"

        if type_ == "escaped_html":
            return elt.markup

        return f"<{type_}{attr}>{children}</{type_}>"

    @staticmethod
    def render_debug(elt: Elt) -> HTML:
        """Render the given element to HTML for debugging without removing fragment wrappers.

        Parameters:
            elt: The element to render.

        Returns:
            The rendered HTML string.
        """
        type_ = elt.type
        attr = DOMStringCompat.render_attrs(elt.attr) if elt.attr else ""
        children = DOMStringCompat.render_children(elt.children) if elt.children else ""

        if type_ in VOID_ELEMENTS:
            return f"<{type_}{attr}/>"

        if type_ == "escaped_html":
            return elt.markup

        return f"<{type_}{attr}>{children}</{type_}>"
