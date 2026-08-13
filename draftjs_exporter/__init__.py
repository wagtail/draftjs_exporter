"""Public API and metadata of draftjs_exporter.

This module gathers metadata, core classes, default configuration maps,
type aliases, and helpers so callers can import everything from
``draftjs_exporter`` directly.
"""

__title__ = "draftjs_exporter"
__version__ = "7.1.0"
__uri__ = "https://wagtail.github.io/draftjs_exporter/"
__author__ = "Springload and Contributors"
__license__ = "MIT"
__copyright__ = "Copyright 2016-present Springload and Contributors"

from draftjs_exporter.constants import BLOCK_TYPES as BLOCK_TYPES
from draftjs_exporter.constants import ENTITY_TYPES as ENTITY_TYPES
from draftjs_exporter.constants import INLINE_STYLES as INLINE_STYLES
from draftjs_exporter.contentstate_filter import (
    ContentStateFilter as ContentStateFilter,
)
from draftjs_exporter.contentstate_filter import FilterRule as FilterRule
from draftjs_exporter.defaults import BLOCK_MAP as BLOCK_MAP
from draftjs_exporter.defaults import STYLE_MAP as STYLE_MAP
from draftjs_exporter.defaults import code_block as code_block
from draftjs_exporter.defaults import render_children as render_children
from draftjs_exporter.dom import DOM as DOM
from draftjs_exporter.error import MarkdownParseError as MarkdownParseError
from draftjs_exporter.html import HTML as HTML
from draftjs_exporter.html import ExporterConfig as ExporterConfig
from draftjs_exporter.markdown import CONFIG as MARKDOWN_CONFIG
from draftjs_exporter.markdown import MarkdownOptions as MarkdownOptions
from draftjs_exporter.markdown import build_markdown_config as build_markdown_config
from draftjs_exporter.markdown.blocks import md_list_wrapper as md_list_wrapper
from draftjs_exporter.markdown.blocks import md_make_ol as md_make_ol
from draftjs_exporter.markdown.blocks import md_make_ul as md_make_ul
from draftjs_exporter.markdown.blocks import md_ol as md_ol
from draftjs_exporter.markdown.blocks import md_prefixed_block as md_prefixed_block
from draftjs_exporter.markdown.blocks import md_ul as md_ul
from draftjs_exporter.markdown.code import md_code_element as md_code_element
from draftjs_exporter.markdown.code import md_code_wrapper as md_code_wrapper
from draftjs_exporter.markdown.code import md_make_code_element as md_make_code_element
from draftjs_exporter.markdown.code import md_make_code_wrapper as md_make_code_wrapper
from draftjs_exporter.markdown.entities import md_horizontal_rule as md_horizontal_rule
from draftjs_exporter.markdown.entities import md_image as md_image
from draftjs_exporter.markdown.entities import md_link as md_link
from draftjs_exporter.markdown.entities import (
    md_make_horizontal_rule as md_make_horizontal_rule,
)
from draftjs_exporter.markdown.fallbacks import md_block_fallback as md_block_fallback
from draftjs_exporter.markdown.fallbacks import md_entity_fallback as md_entity_fallback
from draftjs_exporter.markdown.fallbacks import md_style_fallback as md_style_fallback
from draftjs_exporter.markdown.helpers import md_block as md_block
from draftjs_exporter.markdown.helpers import md_inline as md_inline
from draftjs_exporter.markdown.helpers import md_link_destination as md_link_destination
from draftjs_exporter.markdown.helpers import md_mark_safe as md_mark_safe
from draftjs_exporter.markdown.styles import md_code_span as md_code_span
from draftjs_exporter.markdown.styles import md_inline_style as md_inline_style
from draftjs_exporter.markdown_importer import ImporterConfig as ImporterConfig
from draftjs_exporter.markdown_importer import MarkdownImporter as MarkdownImporter
from draftjs_exporter.markdown_parser import EntityResolution as EntityResolution
from draftjs_exporter.markdown_parser import EntityResolver as EntityResolver
from draftjs_exporter.markdown_parser import MarkdownParser as MarkdownParser
from draftjs_exporter.markdown_parser import ParserConfig as ParserConfig
from draftjs_exporter.markdown_parser import scheme_resolver as scheme_resolver
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
    "HTMLExporter",
    "ExporterConfig",
    "ContentState",
    "DOM",
    # Configs
    "HTML_CONFIG",
    "MARKDOWN_CONFIG",
    "MarkdownOptions",
    "build_markdown_config",
    # Markdown helpers
    "md_block",
    "md_block_fallback",
    "md_code_element",
    "md_code_span",
    "md_code_wrapper",
    "md_entity_fallback",
    "md_horizontal_rule",
    "md_image",
    "md_inline",
    "md_inline_style",
    "md_link",
    "md_link_destination",
    "md_list_wrapper",
    "md_make_code_element",
    "md_make_code_wrapper",
    "md_make_horizontal_rule",
    "md_make_ol",
    "md_make_ul",
    "md_mark_safe",
    "md_ol",
    "md_prefixed_block",
    "md_style_fallback",
    "md_ul",
    # Importer
    "MarkdownImporter",
    "ImporterConfig",
    "MarkdownParser",
    "ParserConfig",
    "ContentStateFilter",
    "FilterRule",
    "MarkdownParseError",
    "EntityResolution",
    "EntityResolver",
    "scheme_resolver",
    # Constants
    "BLOCK_TYPES",
    "ENTITY_TYPES",
    "INLINE_STYLES",
    # Defaults
    "BLOCK_MAP",
    "STYLE_MAP",
    "code_block",
    "render_children",
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

HTMLExporter = HTML
"""Compatibility alias for the HTML exporter."""

HTML_CONFIG: ExporterConfig = {
    "block_map": BLOCK_MAP,
    "style_map": STYLE_MAP,
    "engine": DOM.STRING,
}
"""Default exporter configuration using the built-in maps and string engine."""
