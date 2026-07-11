# Markdown support

> ⚠️ Markdown support is **experimental**. There is no guarantee of API stability at this time.

The exporter can render Draft.js content as Markdown in addition to HTML.

## Quick start

Use the built-in `MARKDOWN_CONFIG` to render Markdown with default settings:

```python
from draftjs_exporter import HTML, MARKDOWN_CONFIG

# Build an exporter configured for Markdown output.
exporter = HTML(MARKDOWN_CONFIG)
# `render` returns Markdown text instead of HTML, because the config
# points the engine at the Markdown DOM (DOMMarkdown).
markdown = exporter.render(content_state)
```

## Configuring output characters

Different Markdown processors and style guides prefer different syntax for the same constructs. Use `build_markdown_config` to choose which characters to use:

```python
from draftjs_exporter import HTML, build_markdown_config

config = build_markdown_config({
    "bold": "__",
    "italic": "*",
    "unordered_list_marker": "*",
    "ordered_list_delimiter": ")",
})
exporter = HTML(config)
```

All are optional. Omitted options use the defaults shown below. All defaults produce valid [CommonMark](https://commonmark.org/) output.

### Exporter output options

| Option                   | Choices             | Default              | Example output |
| ------------------------ | ------------------- | -------------------- | -------------- |
| `bold`                   | `**`, `__`          | `**`                 | `**bold**`     |
| `italic`                 | `*`, `_`            | `_`                  | `_italic_`     |
| `strikethrough`          | `~`, `~~`           | `~`                  | `~struck~`     |
| `unordered_list_marker`  | `-`, `*`, `+`       | `-`                  | `- item`       |
| `ordered_list_delimiter` | `.`, `)`            | `.`                  | `1. item`      |
| `horizontal_rule`        | `---`, `***`, `___` | `---`                | `---`          |
| `code_fence`             | ` ``` `, `~~~`      | ` ``` `              | ` ``` `        |
| `block_fallback`         | `Component`, `None` | Plain text + warning |                |
| `entity_fallback`        | `Component`, `None` | Plain text + warning |                |
| `style_fallback`         | `Component`, `None` | Plain text + warning |                |

The three fallback options control what happens when the exporter encounters a block type, entity type, or inline style that has no explicit mapping. By default, each logs a warning and renders the content as plain text. Pass a custom `Component` function to change this behavior, or `None` to disable the fallback entirely.

```python
from draftjs_exporter import HTML, build_markdown_config
from draftjs_exporter.markdown.helpers import block

# Custom block fallback that prefixes unknown blocks
def my_block_fallback(props):
    return block(["<!-- unknown --> ", props["children"]])

config = build_markdown_config({
    "block_fallback": my_block_fallback,
    "style_fallback": None,  # disable: unknown styles will error
})
```

## Default formatting

The following table shows every Draft.js content type the Markdown exporter handles, and its default Markdown output.

### Block types

| Draft.js block type               | Markdown output                                      |
| --------------------------------- | ---------------------------------------------------- |
| `unstyled`                        | Plain text followed by a blank line                  |
| `header-one` through `header-six` | `# ` through `###### ` prefix                        |
| `blockquote`                      | `> ` prefix                                          |
| `unordered-list-item`             | `- ` prefix, with `  ` indent per depth level        |
| `ordered-list-item`               | `1. `, `2. `, etc., with `  ` indent per depth level |
| `code-block`                      | Wrapped in ` ``` ` fences                            |

### Inline styles

| Draft.js style  | Markdown output |
| --------------- | --------------- |
| `BOLD`          | `**text**`      |
| `ITALIC`        | `_text_`        |
| `CODE`          | `` `text` ``    |
| `STRIKETHROUGH` | `~text~`        |

### Entities

| Draft.js entity type | Markdown output |
| -------------------- | --------------- |
| `LINK`               | `[text](url)`   |
| `IMAGE`              | `![alt](src)`   |
| `HORIZONTAL_RULE`    | `---`           |

## Low-level API

For cases where `build_markdown_config` is not flexible enough, you can build a config dict manually from the individual component functions. This is the same approach used by the default `CONFIG` and `build_markdown_config` internally.

```python
from draftjs_exporter.constants import BLOCK_TYPES, ENTITY_TYPES, INLINE_STYLES
from draftjs_exporter.defaults import BLOCK_MAP as HTML_BLOCK_MAP, STYLE_MAP as HTML_STYLE_MAP
from draftjs_exporter.markdown.blocks import list_wrapper, make_ul, ol, prefixed_block
from draftjs_exporter.markdown.code import code_element, code_wrapper
from draftjs_exporter.markdown.entities import image, link, make_horizontal_rule
from draftjs_exporter.markdown.styles import inline_style

config = {
    "engine": "draftjs_exporter.engines.markdown.DOMMarkdown",
    "block_map": {
        **HTML_BLOCK_MAP,
        BLOCK_TYPES.UNSTYLED: prefixed_block(""),
        BLOCK_TYPES.HEADER_ONE: prefixed_block("# "),
        # ... other headings ...
        BLOCK_TYPES.UNORDERED_LIST_ITEM: {
            "element": make_ul("*"),
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
    },
    "style_map": dict(
        HTML_STYLE_MAP,
        **{
            INLINE_STYLES.BOLD: inline_style("__"),
            INLINE_STYLES.CODE: inline_style("`"),
            INLINE_STYLES.ITALIC: inline_style("*"),
            INLINE_STYLES.STRIKETHROUGH: inline_style("~~"),
        },
    ),
    "entity_decorators": {
        ENTITY_TYPES.IMAGE: image,
        ENTITY_TYPES.LINK: link,
        ENTITY_TYPES.HORIZONTAL_RULE: make_horizontal_rule("***"),
    },
}
```

## Unsupported

The Markdown exporter has inherent limitations compared to the HTML exporter.

- **No underline, subscript, or other HTML-only styles**: The exporter’s default configuration falls through to inline HTML like `<sup>text</sup>`.
- **No reference-style links**: Links are always rendered inline as `[text](url)`.
- **No table support**: Draft.js has no built-in table block type, and the exporter does not attempt to generate Markdown tables from custom block types.
- **No Setext-style headings**: Headings always use ATX style (`# Heading`).
- **Entity data fidelity**: The Markdown link syntax `[text](url)` only preserves the URL.
- **No HTML escaping in text**: If your Draft.js content contains literal HTML characters like like `<` or `>`, the Markdown output will include them unescaped, which may be interpreted as HTML by Markdown renderers.
- **Inline style nesting edge cases**: When bold and italic styles partially overlap, the exporter may produce markers that some strict Markdown parsers reject (e.g. `**Bold **_Italic_**`). Most renderers handle this correctly, but it is not guaranteed by the CommonMark spec.
