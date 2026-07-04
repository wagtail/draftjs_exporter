"""Markdown export configuration and preset builders.

Combines block, inline style, entity, and code decorators tuned for
CommonMark-compatible output.
"""

from typing import Literal, TypedDict

from draftjs_exporter.constants import BLOCK_TYPES, ENTITY_TYPES, INLINE_STYLES
from draftjs_exporter.defaults import BLOCK_MAP as HTML_BLOCK_MAP
from draftjs_exporter.defaults import STYLE_MAP as HTML_STYLE_MAP
from draftjs_exporter.html import ExporterConfig
from draftjs_exporter.markdown.blocks import (
    list_wrapper,
    make_ol,
    make_ul,
    ol,
    prefixed_block,
    ul,
)
from draftjs_exporter.markdown.code import (
    code_element,
    code_wrapper,
    make_code_element,
    make_code_wrapper,
)
from draftjs_exporter.markdown.entities import (
    horizontal_rule,
    image,
    link,
    make_horizontal_rule,
)
from draftjs_exporter.markdown.fallbacks import (
    block_fallback,
    entity_fallback,
    style_fallback,
)
from draftjs_exporter.markdown.styles import inline_style
from draftjs_exporter.types import Component, ConfigMap


class MarkdownOptions(TypedDict, total=False):
    """Options available when customizing Markdown renderer output."""

    bold: Literal["**", "__"]
    italic: Literal["*", "_"]
    strikethrough: Literal["~", "~~"]
    unordered_list_marker: Literal["*", "-", "+"]
    ordered_list_delimiter: Literal[".", ")"]
    horizontal_rule: Literal["---", "***", "___"]
    code_fence: Literal["```", "~~~"]
    block_fallback: Component | None
    entity_fallback: Component | None
    style_fallback: Component | None


BLOCK_MAP: ConfigMap = {
    **HTML_BLOCK_MAP,
    **{
        BLOCK_TYPES.UNSTYLED: prefixed_block(""),
        BLOCK_TYPES.HEADER_ONE: prefixed_block("# "),
        BLOCK_TYPES.HEADER_TWO: prefixed_block("## "),
        BLOCK_TYPES.HEADER_THREE: prefixed_block("### "),
        BLOCK_TYPES.HEADER_FOUR: prefixed_block("#### "),
        BLOCK_TYPES.HEADER_FIVE: prefixed_block("##### "),
        BLOCK_TYPES.HEADER_SIX: prefixed_block("###### "),
        BLOCK_TYPES.UNORDERED_LIST_ITEM: {
            "element": ul,
            "wrapper": list_wrapper,
        },
        BLOCK_TYPES.ORDERED_LIST_ITEM: {
            "element": ol,
            "wrapper": list_wrapper,
        },
        BLOCK_TYPES.BLOCKQUOTE: prefixed_block("> "),
        BLOCK_TYPES.CODE: {
            "element": code_element,
            "wrapper": code_wrapper,
        },
        BLOCK_TYPES.FALLBACK: block_fallback,
    },
}

STYLE_MAP: ConfigMap = dict(
    HTML_STYLE_MAP,
    **{
        INLINE_STYLES.BOLD: inline_style("**"),
        INLINE_STYLES.CODE: inline_style("`"),
        INLINE_STYLES.ITALIC: inline_style("_"),
        INLINE_STYLES.STRIKETHROUGH: inline_style("~"),
        INLINE_STYLES.FALLBACK: style_fallback,
    },
)

ENTITY_DECORATORS: ConfigMap = {
    ENTITY_TYPES.IMAGE: image,
    ENTITY_TYPES.LINK: link,
    ENTITY_TYPES.HORIZONTAL_RULE: horizontal_rule,
    ENTITY_TYPES.FALLBACK: entity_fallback,
}

ENGINE = "draftjs_exporter.engines.markdown.DOMMarkdown"

CONFIG: ExporterConfig = {
    "block_map": BLOCK_MAP,
    "style_map": STYLE_MAP,
    "entity_decorators": ENTITY_DECORATORS,
    "engine": ENGINE,
}


def build_markdown_config(options: MarkdownOptions | None = None) -> ExporterConfig:
    """Build a Markdown exporter config with configurable output characters.

    All options fall back to CommonMark-compatible defaults when omitted.
    Set a fallback to None to disable it.

    Parameters:
        options: Overrides for Markdown characters and fallback components.

    Returns:
        A full exporter config ready for ``HTML``.
    """
    opts = options if options is not None else MarkdownOptions()

    bold = opts.get("bold", "**")
    italic = opts.get("italic", "_")
    strikethrough = opts.get("strikethrough", "~")
    ul_marker = opts.get("unordered_list_marker", "-")
    ol_delimiter = opts.get("ordered_list_delimiter", ".")
    hr = opts.get("horizontal_rule", "---")
    fence = opts.get("code_fence", "```")

    block_map: ConfigMap = {
        BLOCK_TYPES.UNSTYLED: prefixed_block(""),
        BLOCK_TYPES.HEADER_ONE: prefixed_block("# "),
        BLOCK_TYPES.HEADER_TWO: prefixed_block("## "),
        BLOCK_TYPES.HEADER_THREE: prefixed_block("### "),
        BLOCK_TYPES.HEADER_FOUR: prefixed_block("#### "),
        BLOCK_TYPES.HEADER_FIVE: prefixed_block("##### "),
        BLOCK_TYPES.HEADER_SIX: prefixed_block("###### "),
        BLOCK_TYPES.UNORDERED_LIST_ITEM: {
            "element": make_ul(ul_marker),
            "wrapper": list_wrapper,
        },
        BLOCK_TYPES.ORDERED_LIST_ITEM: {
            "element": make_ol(ol_delimiter),
            "wrapper": list_wrapper,
        },
        BLOCK_TYPES.BLOCKQUOTE: prefixed_block("> "),
        BLOCK_TYPES.CODE: {
            "element": make_code_element(fence),
            "wrapper": make_code_wrapper(fence),
        },
        BLOCK_TYPES.ATOMIC: lambda props: props["children"],
    }

    style_map: ConfigMap = {
        **HTML_STYLE_MAP,
        INLINE_STYLES.BOLD: inline_style(bold),
        INLINE_STYLES.CODE: inline_style("`"),
        INLINE_STYLES.ITALIC: inline_style(italic),
        INLINE_STYLES.STRIKETHROUGH: inline_style(strikethrough),
    }

    entity_decorators: ConfigMap = {
        ENTITY_TYPES.IMAGE: image,
        ENTITY_TYPES.LINK: link,
        ENTITY_TYPES.HORIZONTAL_RULE: make_horizontal_rule(hr),
    }

    _apply_fallback(
        block_map,
        BLOCK_TYPES.FALLBACK,
        "block_fallback" in opts,
        opts.get("block_fallback"),
        block_fallback,
    )
    _apply_fallback(
        style_map,
        INLINE_STYLES.FALLBACK,
        "style_fallback" in opts,
        opts.get("style_fallback"),
        style_fallback,
    )
    _apply_fallback(
        entity_decorators,
        ENTITY_TYPES.FALLBACK,
        "entity_fallback" in opts,
        opts.get("entity_fallback"),
        entity_fallback,
    )

    return {
        "block_map": block_map,
        "style_map": style_map,
        "entity_decorators": entity_decorators,
        "engine": ENGINE,
    }


def _apply_fallback(
    config_map: ConfigMap,
    key: str,
    has_option: bool,
    value: Component | None,
    default: Component,
) -> None:
    """Attach or remove a fallback component in a config map.

    Parameters:
        config_map: The map to mutate.
        key: The fallback key to set.
        has_option: Whether the caller explicitly provided a fallback option.
        value: The caller-provided fallback, if any.
        default: The built-in fallback to use when no option was given.
    """
    if has_option:
        if value is not None:
            config_map[key] = value
    else:
        config_map[key] = default
