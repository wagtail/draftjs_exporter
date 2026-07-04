"""Shared type aliases and TypedDict structures for Draft.js data.

Use these types when annotating custom components, decorators, or
configuration maps consumed by the exporter.
"""

import re
from collections.abc import Callable
from typing import Any, Literal, TypeAlias, TypedDict

Element: TypeAlias = Any
"""Engine-specific element produced by a renderable."""

Props: TypeAlias = dict[str, Any]
"""Dictionary of string attribute keys to arbitrary values."""

Tag: TypeAlias = str
"""HTML tag name."""

Component: TypeAlias = Callable[[Props], Element]
"""Render a component from props and return an element."""

RenderableType: TypeAlias = Component | Tag | None
"""A tag name, component function, or ``None`` for a fragment."""

HTML = str
"""Final rendered output of the exporter."""


class RenderableConfig(TypedDict, total=False):
    """Configuration describing how to render a single renderable."""

    # TODO Use typing.Required when dropping Python 3.10 support.
    # See https://peps.python.org/pep-0655/.
    element: RenderableType
    props: Props
    wrapper: RenderableType
    wrapper_props: Props


# TODO Introduce a type guard when support improves.
# def is_renderable_config(val: dict) -> TypeGuard[RenderableConfig]:
#     return isinstance(val, dict) and "element" in val

ConfigMap: TypeAlias = dict[str, RenderableConfig | RenderableType]
"""Map string keys to renderable configurations or values."""


class Decorator(TypedDict):
    """Pattern and component used to decorate matching text."""

    strategy: re.Pattern[str]
    component: RenderableType


CompositeDecorators: TypeAlias = list[Decorator]
"""List composite decorators applied while rendering blocks."""


class InlineStyleRange(TypedDict):
    """Range of text styled by a single inline style."""

    offset: int
    length: int
    style: str


class EntityRange(TypedDict):
    """Range of text associated with a single entity."""

    offset: int
    length: int
    key: int


class Block(TypedDict, total=False):
    """Single Draft.js block within a content state."""

    key: str
    text: str
    type: str
    depth: int
    data: dict[str, Any]
    inlineStyleRanges: list[InlineStyleRange]
    entityRanges: list[EntityRange]


EntityKey: TypeAlias = str
"""Key used to look up an entity in the entity map."""

Mutability: TypeAlias = Literal["MUTABLE", "IMMUTABLE", "SEGMENTED"]
"""Draft.js entity mutability setting."""


class Entity(TypedDict, total=False):
    """Draft.js entity data referenced by entity ranges."""

    type: str
    data: dict[str, Any]
    mutability: Mutability


EntityMap: TypeAlias = dict[EntityKey, Entity]
"""Map entity keys to their definitions."""


class ContentState(TypedDict, total=False):
    """Top-level Draft.js content state passed to the exporter."""

    blocks: list[Block]
    entityMap: EntityMap
