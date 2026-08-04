"""Markdown-specific string DOM engine implementation."""

from html import escape

from draftjs_exporter.engines.base import Attr, DOMEngine
from draftjs_exporter.markdown.escape import (
    code_block_fence,
    code_span_delimiters,
    escape_text,
)
from draftjs_exporter.types import HTML, Tag

# http://w3c.github.io/html/single-page.html#void-elements
# https://github.com/html5lib/html5lib-python/blob/0cae52b2073e3f2220db93a7650901f2200f2a13/html5lib/constants.py#L560
VOID_ELEMENTS = (
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
)


class Elt:
    """A DOM element that the Markdown engine manipulates.

    Identical to the string engine's Elt, with extra Markdown-specific node
    types: ``mark_safe`` (structural syntax rendered verbatim), ``code_span``
    and ``code_block`` (content rendered unescaped with sized delimiters).
    """

    __slots__ = ("type", "attr", "children", "markup")

    def __init__(self, type_: Tag, attr: Attr | None, markup: HTML = ""):
        """Initialize a new element.

        Parameters:
            type_: The tag name of the element.
            attr: A mapping of attribute names to values.
            markup: Raw HTML markup when the element represents escaped HTML.
        """
        self.type = type_
        self.attr = attr
        self.children: list["str | Elt"] = []
        self.markup = markup

    @staticmethod
    def from_html(markup: HTML) -> "Elt":
        """Create an element that holds already-escaped HTML.

        Parameters:
            markup: The raw HTML markup to include verbatim.

        Returns:
            An element wrapping the markup.
        """
        return Elt("escaped_html", None, markup)


class DOMMarkdown(DOMEngine):
    """String concatenation implementation of the DOM API for Markdown output.

    Invariant: a plain ``str`` child in the tree is always user-controlled
    text. Structural Markdown syntax must be wrapped in ``mark_safe``
    elements by components, or it will be escaped as text.
    """

    @staticmethod
    def create_tag(type_: Tag, attr: Attr | None = None) -> Elt:
        """Create and return a new element of the given type and attributes.

        Parameters:
            type_: The tag name of the element.
            attr: A mapping of attribute names to values.

        Returns:
            The newly created element.
        """
        return Elt(type_, attr)

    @staticmethod
    def parse_html(markup: HTML) -> Elt:
        """Parse arbitrary HTML markup into an element.

        Treats the HTML as if it had already been escaped and was safe.

        Parameters:
            markup: The HTML string to parse.

        Returns:
            An element wrapping the markup.
        """
        return Elt.from_html(markup)

    @staticmethod
    def append_child(elt: Elt, child: str | Elt) -> None:
        """Append the given child node to the children of elt.

        Parameters:
            elt: The parent element.
            child: The child element or text to append.
        """
        # This check is necessary because the current wrapper_state implementation
        # has an issue where it inserts elements multiple times.
        # This must be skipped for text, which can be duplicated.
        is_existing_ref = child in elt.children and isinstance(child, Elt)
        if not is_existing_ref:
            elt.children.append(child)

    @staticmethod
    def render_attrs(attr: Attr) -> str:
        """Render a mapping of attributes to a sorted HTML attribute string.

        Parameters:
            attr: The attributes to render.

        Returns:
            The rendered attribute string.
        """
        return "".join(sorted([f' {k}="{escape(v)}"' for k, v in attr.items()]))

    @staticmethod
    def render_children(children: list[HTML | Elt]) -> HTML:
        """Render a list of children, escaping plain strings as user text.

        A plain ``str`` child is always user-controlled text and is escaped.
        Structural syntax wrapped in ``mark_safe`` elements renders verbatim.
        Line-start-sensitive characters are escaped when a string begins a
        line: at the start of the children list, when the output so far ends
        with a newline or carriage return, or right after a ``mark_safe``
        element created with ``block_prefix``.

        Parameters:
            children: A list of strings and elements to render.

        Returns:
            The rendered children.
        """
        out: list[str] = []
        at_line_start = True
        for c in children:
            if isinstance(c, Elt):
                rendered = DOMMarkdown.render(c)
                out.append(rendered)
                if (
                    c.type == "mark_safe"
                    and c.attr
                    and c.attr.get("block_prefix") == "true"
                ):
                    at_line_start = True
                elif rendered:
                    at_line_start = rendered.endswith(("\n", "\r"))
            else:
                out.append(escape_text(c, at_line_start))
                if c:
                    at_line_start = c.endswith(("\n", "\r"))
        return "".join(out)

    @staticmethod
    def flatten_text(children: list["str | Elt"]) -> str:
        """Flatten children to raw text, discarding element structure.

        ``mark_safe`` and ``escaped_html`` markup is included verbatim;
        other elements contribute only their text content.

        Parameters:
            children: A list of strings and elements.

        Returns:
            The concatenated raw text.
        """
        parts = []
        for c in children:
            if isinstance(c, Elt):
                if c.type == "mark_safe":
                    parts.append(c.attr["markup"] if c.attr else "")
                elif c.markup:
                    parts.append(c.markup)
                else:
                    parts.append(DOMMarkdown.flatten_text(c.children))
            else:
                parts.append(c)
        return "".join(parts)

    @staticmethod
    def render(elt: Elt) -> HTML:
        """Render the given element and its children to HTML.

        Fragment nodes are rendered as the concatenation of their children,
        and void elements are rendered as self-closing tags.

        Parameters:
            elt: The element to render.

        Returns:
            The rendered HTML string.
        """
        type_ = elt.type
        attr = DOMMarkdown.render_attrs(elt.attr) if elt.attr else ""
        children = DOMMarkdown.render_children(elt.children) if elt.children else ""

        match type_:
            case "fragment":
                return children
            case "mark_safe":
                return elt.attr["markup"] if elt.attr else ""
            case "escaped_html":
                return elt.markup
            case "code_span":
                content = DOMMarkdown.flatten_text(elt.children)
                opening, closing = code_span_delimiters(content)
                return f"{opening}{content}{closing}"
            case "code_block":
                content = DOMMarkdown.flatten_text(elt.children)
                fence_char = (elt.attr or {}).get("fence", "`")
                fence = code_block_fence(content, fence_char)
                return f"{fence}\n{content}{fence}\n\n"
            case _ if type_ in VOID_ELEMENTS:
                return f"<{type_}{attr}/>"
            case _:
                return f"<{type_}{attr}>{children}</{type_}>"

    @staticmethod
    def render_debug(elt: Elt) -> HTML:
        """Render the given element to HTML for debugging.

        Delegates to render so fragment nodes are expanded.

        Parameters:
            elt: The element to render.

        Returns:
            The rendered HTML string.
        """
        return DOMMarkdown.render(elt)
