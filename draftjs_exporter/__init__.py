"""Public API and metadata of draftjs_exporter.

This module gathers metadata, core classes, default configuration maps,
type aliases, and helpers so callers can import everything from
``draftjs_exporter`` directly.
"""

__title__ = "draftjs_exporter"
__version__ = "6.0.0"
__uri__ = "https://wagtail.github.io/draftjs_exporter/"
__author__ = "Springload and Contributors"
__license__ = "MIT"
__copyright__ = "Copyright 2016-present Springload and Contributors"

from draftjs_exporter.constants import BLOCK_TYPES as BLOCK_TYPES
from draftjs_exporter.constants import ENTITY_TYPES as ENTITY_TYPES
from draftjs_exporter.constants import INLINE_STYLES as INLINE_STYLES
from draftjs_exporter.defaults import BLOCK_MAP as BLOCK_MAP
from draftjs_exporter.defaults import STYLE_MAP as STYLE_MAP
from draftjs_exporter.dom import DOM as DOM
from draftjs_exporter.html import HTML as HTML
from draftjs_exporter.html import ExporterConfig as ExporterConfig
from draftjs_exporter.markdown import CONFIG as MARKDOWN_CONFIG
from draftjs_exporter.markdown import MarkdownOptions as MarkdownOptions
from draftjs_exporter.markdown import build_markdown_config as build_markdown_config
from draftjs_exporter.types import Block as Block
from draftjs_exporter.types import Component as Component
from draftjs_exporter.types import CompositeDecorators as CompositeDecorators
from draftjs_exporter.types import ConfigMap as ConfigMap
from draftjs_exporter.types import ContentState as ContentState
from draftjs_exporter.types import Decorator as Decorator
from draftjs_exporter.types import Element as Element
from draftjs_exporter.types import Entity as Entity
from draftjs_exporter.types import EntityKey as EntityKey
from draftjs_exporter.types import EntityMap as EntityMap
from draftjs_exporter.types import EntityRange as EntityRange
from draftjs_exporter.types import InlineStyleRange as InlineStyleRange
from draftjs_exporter.types import Mutability as Mutability
from draftjs_exporter.types import Props as Props
from draftjs_exporter.types import RenderableConfig as RenderableConfig
from draftjs_exporter.types import RenderableType as RenderableType
from draftjs_exporter.types import Tag as Tag

__all__ = [
    # Metadata
    "__title__",
    "__version__",
    "__uri__",
    "__author__",
    "__license__",
    "__copyright__",
    # Core
    "Exporter",
    "HTML",
    "ExporterConfig",
    "ContentState",
    "DOM",
    # Configs
    "HTML_CONFIG",
    "MARKDOWN_CONFIG",
    "MarkdownOptions",
    "build_markdown_config",
    # Constants
    "BLOCK_TYPES",
    "ENTITY_TYPES",
    "INLINE_STYLES",
    # Default maps
    "BLOCK_MAP",
    "STYLE_MAP",
    # Types
    "Block",
    "Component",
    "CompositeDecorators",
    "ConfigMap",
    "ContentState",
    "Decorator",
    "Element",
    "Entity",
    "EntityKey",
    "EntityMap",
    "EntityRange",
    "InlineStyleRange",
    "Mutability",
    "Props",
    "RenderableConfig",
    "RenderableType",
    "Tag",
]

Exporter = HTML
"""Compatibility alias for the HTML exporter."""

HTML_CONFIG: ExporterConfig = {
    "block_map": BLOCK_MAP,
    "style_map": STYLE_MAP,
    "engine": DOM.STRING,
}
"""Default exporter configuration using the built-in maps and string engine."""
