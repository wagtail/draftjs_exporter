---
description: "API reference for draftjs_exporter: the HTML exporter, DOM, constants, types, and the Markdown toolchain."
---

# API reference

This reference is generated from the package's public API, so it always matches what `draftjs_exporter` exports. Everything documented here is importable from the package root:

```python
from draftjs_exporter import HTML, DOM, BLOCK_TYPES
```

::: draftjs_exporter

    options:
      show_source: false
      members:
        - Exporter
        - HTML
        - HTMLExporter
        - ExporterConfig
        - ContentState
        - DOM
        - DOMEngine
        - ExporterEntityException
        - HTML_CONFIG
        - MARKDOWN_CONFIG
        - MarkdownOptions
        - build_markdown_config
        - md_block
        - md_block_fallback
        - md_blockquote
        - md_code_block_fence
        - md_code_element
        - md_code_span
        - md_code_wrapper
        - md_entity_fallback
        - md_escape_link_destination
        - md_escape_text
        - md_horizontal_rule
        - md_image
        - md_inline
        - md_inline_style
        - md_line_break
        - md_link
        - md_link_destination
        - md_list_wrapper
        - md_make_code_element
        - md_make_code_wrapper
        - md_make_horizontal_rule
        - md_make_list_item
        - md_make_ol
        - md_make_ul
        - md_mark_safe
        - md_ol
        - md_prefixed_block
        - md_style_fallback
        - md_ul
        - MarkdownImporter
        - ImporterConfig
        - MarkdownParser
        - ParserConfig
        - ContentStateFilter
        - FilterRule
        - MarkdownParseError
        - EntityResolution
        - EntityResolver
        - scheme_resolver
        - BLOCK_TYPES
        - ENTITY_TYPES
        - INLINE_STYLES
        - BLOCK_MAP
        - STYLE_MAP
        - code_block
        - render_children
        - Block
        - Component
        - CompositeDecorators
        - ConfigMap
        - Decorator
        - Element
        - Entity
        - EntityKey
        - EntityMap
        - EntityRange
        - InlineStyleRange
        - Mutability
        - Props
        - RenderableConfig
        - RenderableType
        - Tag
