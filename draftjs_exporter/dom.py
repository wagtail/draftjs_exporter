"""Abstract DOM-building primitives used by the exporter.

The DOM class exposes a React-like element-creation API over pluggable
rendering engines such as HTML5lib, lxml, string, and Markdown.
"""

import re
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, cast

from draftjs_exporter.engines.base import DOMEngine
from draftjs_exporter.types import HTML, Component, Element, Props, RenderableType
from draftjs_exporter.utils.module_loading import import_string

# https://gist.github.com/yahyaKacem/8170675
_first_cap_re = re.compile(r"(.)([A-Z][a-z]+)")
_all_cap_re = re.compile("([a-z0-9])([A-Z])")

_engine_var: ContextVar[type[DOMEngine] | None] = ContextVar("dom_engine", default=None)
_engine_cache: dict[str, type[DOMEngine]] = {}


class DOM:
    """Provide a DOM-building API that abstracts the active engine."""

    HTML5LIB = "draftjs_exporter.engines.html5lib.DOM_HTML5LIB"
    """Identifier for the html5lib DOM engine."""
    LXML = "draftjs_exporter.engines.lxml.DOM_LXML"
    """Identifier for the lxml DOM engine."""
    MARKDOWN = "draftjs_exporter.engines.markdown.DOMMarkdown"
    """Identifier for the Markdown DOM engine."""
    STRING = "draftjs_exporter.engines.string.DOMString"
    """Identifier for the string DOM engine."""
    STRING_COMPAT = "draftjs_exporter.engines.string_compat.DOMStringCompat"
    """Identifier for the string compatibility DOM engine."""

    @staticmethod
    def camel_to_dash(camel_cased_str: str) -> str:
        """Convert a camelCase string to a dashed-case attribute name."""
        sub2 = _first_cap_re.sub(r"\1-\2", camel_cased_str)
        dashed_case_str = _all_cap_re.sub(r"\1-\2", sub2).lower()
        return dashed_case_str.replace("--", "-")

    @classmethod
    def _dom(cls) -> type[DOMEngine]:
        engine = _engine_var.get()
        if engine is None:
            raise RuntimeError(
                "No DOM engine set. Call DOM.use() or use HTML() to configure an engine."
            )
        return engine

    @classmethod
    def use(cls, engine: str) -> None:
        """Select the DOM implementation for the current context."""
        try:
            resolved = _engine_cache[engine]
        except KeyError:
            resolved = _engine_cache[engine] = cast(
                type[DOMEngine], import_string(engine)
            )
        _engine_var.set(resolved)

    @staticmethod
    @contextmanager
    def engine(engine: str) -> Iterator[None]:
        """Temporarily set the DOM engine for the current context."""
        try:
            resolved = _engine_cache[engine]
        except KeyError:
            resolved = _engine_cache[engine] = cast(
                type[DOMEngine], import_string(engine)
            )
        token = _engine_var.set(resolved)
        try:
            yield
        finally:
            _engine_var.reset(token)

    @classmethod
    def create_element(
        cls,
        type_: RenderableType = None,
        props: Props | None = None,
        *elt_children: Element | None,
    ) -> Element:
        """Create an element or document fragment using the current engine.

        The signature mirrors React.createElement: a type, an optional props
        dictionary, and zero or more children.

        Parameters:
            type_: The tag name, component, or ``None`` for a fragment.
            props: Attributes and metadata to pass to the element.
            *elt_children: Child nodes to append to the element.

        Returns:
            The constructed element.
        """
        dom = cls._dom()
        # Create an empty document fragment.
        if not type_:
            return dom.create_tag("fragment")

        if props is None:
            props = {}

        # If the first element of children is a list, we use it as the list.
        if elt_children and isinstance(elt_children[0], (list, tuple)):
            children = elt_children[0]
        else:
            children = elt_children

        children_len = len(children)

        # The children prop is the first child if there is only one.
        props["children"] = children[0] if children_len == 1 else children

        if callable(type_):
            elt = cast(Component, type_)(props)
        else:
            # Raw tag, as a string.
            attributes = {}

            # Never render those attributes on a raw tag.
            props.pop("children", None)
            props.pop("block", None)
            props.pop("blocks", None)
            props.pop("entity", None)
            props.pop("inline_style_range", None)

            # Convert style object to style string, like the DOM would do.
            if "style" in props and isinstance(props["style"], dict):
                rules = [
                    f"{DOM.camel_to_dash(s)}: {v};" for s, v in props["style"].items()
                ]
                props["style"] = "".join(rules)

            # Convert props to HTML attributes.
            for key in props:
                if props[key] is False:
                    props[key] = "false"

                if props[key] is True:
                    props[key] = "true"

                if props[key] is not None:
                    attributes[key] = str(props[key])

            elt = dom.create_tag(type_, attributes)

            # Append the children inside the element.
            for child in children:
                if child not in (None, ""):
                    cls.append_child(elt, child)

        # If elt is "empty", create a fragment anyway to add children.
        if elt in (None, ""):
            elt = dom.create_tag("fragment")

        return elt

    @classmethod
    def parse_html(cls, markup: HTML) -> Element:
        """Parse an HTML string into an element using the current engine."""
        return cls._dom().parse_html(markup)

    @classmethod
    def append_child(cls, elt: Element, child: Element) -> Any:
        """Append a child node to an element."""
        return cls._dom().append_child(elt, child)

    @classmethod
    def render(cls, elt: Element) -> HTML:
        """Render an element tree to its final HTML output."""
        return cls._dom().render(elt)

    @classmethod
    def render_debug(cls, elt: Element) -> HTML:
        """Render an element tree to a debug-friendly representation."""
        return cls._dom().render_debug(elt)
