# Markdown support

> ⚠️ Markdown support is **experimental**. There is no guarantee of API stability at this time.

The exporter can render Draft.js content as Markdown in addition to HTML.

## Quick start

Use the built-in `MARKDOWN_CONFIG` to render Markdown with default settings. The config points the exporter at the Markdown DOM engine (`DOMMarkdown`), so `render` returns Markdown text instead of HTML:

```python
from draftjs_exporter import HTML, MARKDOWN_CONFIG

exporter = HTML(MARKDOWN_CONFIG)
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


def my_block_fallback(props):
    return block(["<!-- unknown --> ", props["children"]])


config = build_markdown_config({
    "block_fallback": my_block_fallback,
    "style_fallback": None,
})
```

In this example, unknown blocks are prefixed with an HTML comment, while unknown styles raise an error instead of falling back to plain text.

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

For cases where `build_markdown_config` is not flexible enough, you can build a config dict manually from the individual component functions. This is the same approach used by the default `CONFIG` and `build_markdown_config` internally. The constants and default maps are available from the top-level package; the Markdown-specific component functions live in submodules:

```python
from draftjs_exporter import BLOCK_MAP as HTML_BLOCK_MAP, BLOCK_TYPES, ENTITY_TYPES, INLINE_STYLES, STYLE_MAP as HTML_STYLE_MAP
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

The Markdown exporter has inherent limitations compared to the HTML exporter. Where the importer can repair or absorb these limitations for round-trip workflows, that's noted inline; see [Importer](#importer) for the full picture.

- **No underline, subscript, or other HTML-only styles**: The exporter's default configuration falls through to inline HTML like `<sup>text</sup>`. The importer parses these back into inline style ranges.
- **No reference-style links**: Links are always rendered inline as `[text](url)`.
- **No table support**: Draft.js has no built-in table block type, and the exporter does not attempt to generate Markdown tables from custom block types.
- **No Setext-style headings**: Headings always use ATX style (`# Heading`).
- **Entity data fidelity**: The Markdown link syntax `[text](url)` preserves the URL and optional title, but other entity data (e.g. `rel`, `data-*` attributes) is lost.
- **No HTML escaping in text**: If your Draft.js content contains literal HTML characters like `<` or `>`, the Markdown output will include them unescaped, which may be interpreted as HTML by Markdown renderers.
- **Inline style nesting edge cases**: When bold and italic styles partially overlap, the exporter may produce markers that some strict Markdown parsers reject (e.g. `**Bold **_Italic_**`). Most renderers handle this correctly, but it is not guaranteed by the CommonMark spec. The importer repairs these by merging adjacent ranges of the same style.

## Importer

> ⚠️ The Markdown importer is **experimental**. There is no guarantee of API stability at this time.

The importer parses Markdown back into Draft.js ContentState, enabling round-trip workflows. It is dependency-free and understands the same subset of Markdown that the exporter produces, including the limitations documented above.

### Quick start

```python
from draftjs_exporter import markdown_to_content_state

content_state = markdown_to_content_state(markdown_text)
```

### Configuring input markers

Pass `MarkdownImporterOptions` matching the options used with `build_markdown_config` to round-trip customized output:

```python
from draftjs_exporter import build_markdown_config, HTML, markdown_to_content_state

options = {"bold": "__", "italic": "*"}
config = build_markdown_config(options)
exporter = HTML(config)

markdown = exporter.render(content_state)
# Pass the same options to the importer.
content_state = markdown_to_content_state(markdown, options)
```

### Importer options

| Option            | Choices                        | Default              |
| ----------------- | ------------------------------ | -------------------- |
| `bold`            | `**`, `__`                     | `**`                 |
| `italic`          | `*`, `_`                       | `_`                  |
| `strikethrough`   | `~`, `~~`                      | `~`                  |
| `html_style_tags` | `dict[str, str]` (tag → style) | Inverse of STYLE_MAP |

Only inline style markers are configurable. Block-level syntax (list markers, horizontal rule variants, code fence variants, ordered list delimiters) is **recognized polymorphically** – the importer accepts any of `-`/`*`/`+` for unordered lists, `.`/`)` for ordered lists, `---`/`***`/`___` for horizontal rules, and ` ``` `/`~~~` for code fences. Any block-level keys you pass through from `MarkdownOptions` (`unordered_list_marker`, `ordered_list_delimiter`, `horizontal_rule`, `code_fence`) are simply ignored.

The `html_style_tags` option extends the default HTML tag → style mapping (e.g. `<u>` → `UNDERLINE`). Custom tags are merged with the defaults, so built-in tags still work alongside user-defined ones. This lets you round-trip non-default inline styles configured on the exporter side:

```python
from draftjs_exporter import HTML, build_markdown_config, markdown_to_content_state
from draftjs_exporter.defaults import STYLE_MAP
from draftjs_exporter.dom import DOM

# Register a custom "KBD" inline style on the exporter side.
# (defaults.py ships "KEYBOARD" -> <kbd>; here we re-map it to a custom name.)
STYLE_MAP["KBD"] = lambda props: DOM.create_element("kbd", {}, props["children"])

options = {"html_style_tags": {"kbd": "KBD"}}
config = build_markdown_config(options)
exporter = HTML(config)

markdown = exporter.render(content_state)
# The importer parses <kbd> back as "KBD" rather than the default "KEYBOARD".
content_state = markdown_to_content_state(markdown, options)
```

### Fallback behavior

If the importer encounters a block-level construct it doesn't recognize (anything that doesn't match the heading, list, blockquote, code fence, horizontal rule, or image patterns), the block falls through to `unstyled` and is logged at debug level. This is the expected path for hand-written Markdown (plain paragraphs don't match any of the block-level patterns), so the importer doesn't emit warnings on normal input. Inline syntax that isn't recognized (unknown HTML tags, mismatched markers, unterminated links) is emitted as literal text rather than dropping content.

### Round-trip guarantees

`ContentState → Markdown → ContentState` preserves the following when the default exporter config is used:

- Block types (`unstyled`, headings 1-6, blockquote, list items with depth, code-block, atomic).
- Block text, including soft line breaks within block-level elements.
- `inlineStyleRanges` (offsets, lengths, and style names) for the four Markdown markers (`BOLD`, `ITALIC`, `CODE`, `STRIKETHROUGH`) and the ten inline HTML tag styles (`UNDERLINE`, `SUPERSCRIPT`, `SUBSCRIPT`, `MARK`, `QUOTATION`, `SMALL`, `SAMPLE`, `INSERT`, `DELETE`, `KEYBOARD`).
- `entityRanges` (offsets, lengths, and key mappings) for `LINK`, `IMAGE`, and `HORIZONTAL_RULE` entities.
- Entity `data.url` and, for links, an optional `data.title`.

The following are **not** preserved, because Markdown's link syntax cannot represent them:

- Entity data beyond `url` and `title` (e.g. `rel`, `target`, `data-*` attributes on links).
- Structural entities added by composite decorators during export (e.g. linkified URLs). The importer parses them back as `LINK` entities, but they didn't exist in the original ContentState.
- Atomic block internal structure (e.g. embed payloads).
- Block keys (the importer generates random 5-character keys; Draft.js reassigns keys client-side when loading content into an editor anyway).

### Supported Markdown features

- ATX headings (`#` through `######`)
- Blockquotes (single-line and multi-line)
- Unordered lists (`-`, `*`, `+` with 2-space indent per depth)
- Ordered lists (`.` and `)` delimiters)
- Fenced code blocks (` ``` ` and `~~~`, with optional info strings)
- Horizontal rules (`---`, `***`, `___`)
- Images (`![alt](src)`)
- Links (`[text](url)`, with optional `"title"`)
- Inline styles: bold, italic, code, strikethrough
- Inline HTML tags: `<u>`, `<sup>`, `<sub>`, `<mark>`, `<q>`, `<small>`, `<samp>`, `<ins>`, `<del>`, `<kbd>`
- Backslash escapes for all CommonMark punctuation
- Nested links and styles within link text
- Soft line breaks within block-level elements

The importer does not validate URL schemes. Custom protocols such as `wagtail://core.Page.89` round-trip unchanged in the entity `data.url`. Whether to accept or reject dangerous schemes (e.g. `javascript:`) is the integrating application's responsibility, matching the exporter's behavior – see [SECURITY.md](SECURITY.md).
