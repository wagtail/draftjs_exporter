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
from draftjs_exporter import HTML, build_markdown_config, md_block


def my_block_fallback(props):
    return md_block(["<!-- unknown --> ", props["children"]])


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

For cases where `build_markdown_config` is not flexible enough, you can build a config dict manually from the individual component functions. This is the same approach used by the default `CONFIG` and `build_markdown_config` internally. All Markdown helpers are re-exported from the package root with an `md_` prefix:

```python
from draftjs_exporter import (
    BLOCK_MAP as HTML_BLOCK_MAP,
    BLOCK_TYPES,
    ENTITY_TYPES,
    INLINE_STYLES,
    STYLE_MAP as HTML_STYLE_MAP,
    md_code_element,
    md_code_span,
    md_code_wrapper,
    md_image,
    md_inline_style,
    md_link,
    md_list_wrapper,
    md_make_horizontal_rule,
    md_make_ul,
    md_ol,
    md_prefixed_block,
)

config = {
    "engine": "draftjs_exporter.engines.markdown.DOMMarkdown",
    "block_map": {
        **HTML_BLOCK_MAP,
        BLOCK_TYPES.UNSTYLED: md_prefixed_block(""),
        BLOCK_TYPES.HEADER_ONE: md_prefixed_block("# "),
        # ... other headings ...
        BLOCK_TYPES.UNORDERED_LIST_ITEM: {
            "element": md_make_ul("*"),
            "wrapper": md_list_wrapper,
        },
        BLOCK_TYPES.ORDERED_LIST_ITEM: {
            "element": md_ol,
            "wrapper": md_list_wrapper,
        },
        BLOCK_TYPES.BLOCKQUOTE: md_prefixed_block("> ", block_prefix=True),
        BLOCK_TYPES.CODE: {
            "element": md_code_element,
            "wrapper": md_code_wrapper,
        },
    },
    "style_map": dict(
        HTML_STYLE_MAP,
        **{
            INLINE_STYLES.BOLD: md_inline_style("__"),
            INLINE_STYLES.CODE: md_code_span,
            INLINE_STYLES.ITALIC: md_inline_style("*"),
            INLINE_STYLES.STRIKETHROUGH: md_inline_style("~~"),
        },
    ),
    "entity_decorators": {
        ENTITY_TYPES.IMAGE: md_image,
        ENTITY_TYPES.LINK: md_link,
        ENTITY_TYPES.HORIZONTAL_RULE: md_make_horizontal_rule("***"),
    },
}
```

## Escaping

The Markdown exporter escapes user-controlled text so it renders literally rather than as Markdown syntax, following CommonMark backslash-escape rules. This is always on; there is no configuration option.

- Anywhere in text: `\`, `` ` ``, `*`, `[`, `]`, `<`, plus `_` where it could form emphasis. Intraword underscore runs (as in `snake_case`) are left unescaped — CommonMark's flanking rules guarantee they are inert.
- At the start of a line: `#`, `-`, `+`, `>`, `=`, `|`, `~`, and ordered list markers like `1.` (rendered as `1\.`). "Start of a line" means the start of a block, after any line ending (`\n`, `\r\n`, or a lone `\r`), or after a list/blockquote marker. The line-start rules also apply after any leading run of spaces, since CommonMark allows block constructs to be indented.
- Link and image URLs inside `](…)` get destination-specific escaping: `\`, `(`, `)` are backslash-escaped and whitespace/control characters are percent-encoded. URL scheme validation (`javascript:` etc.) remains the integrating application's responsibility.
- Code spans and code blocks are never escaped. Instead, the exporter sizes the delimiters to the content: a code span containing a backtick is wrapped in double backticks, and a code block containing a fence gets a fence one character longer.

For example, block text that looks like Markdown syntax renders literally:

```python
from draftjs_exporter import HTML, MARKDOWN_CONFIG

exporter = HTML(MARKDOWN_CONFIG)
exporter.render({
    "entityMap": {},
    "blocks": [{
        "key": "6m5fh",
        "text": "# Not a heading, *not emphasis*, <b>not HTML</b>, &copy;",
        "type": "unstyled",
        "depth": 0,
        "inlineStyleRanges": [],
        "entityRanges": [],
    }],
})
# "\\# Not a heading, \\*not emphasis\\*, \\<b>not HTML\\</b>, &copy;\n\n"
```

### Escaping in custom components

When you write custom Markdown components, any plain strings they emit are escaped as user text. Wrap structural syntax with `md_mark_safe` so it renders verbatim, and route URLs through `md_link_destination`:

```python
from draftjs_exporter import DOM, Element, Props, md_link_destination, md_mark_safe


def mention(props: Props) -> Element:
    """Render a mention entity as a Markdown link to a profile."""
    return DOM.create_element(
        "fragment",
        {},
        [
            md_mark_safe("[@"),
            props["children"],  # Plain text, escaped automatically.
            md_mark_safe("]("),
            md_link_destination(props["url"]),  # Escaped for ](…) destinations.
            md_mark_safe(")"),
        ],
    )
```

Use `md_mark_safe(markup, block_prefix=True)` for prefixes after which nested blocks can start (list markers, blockquote `> `), so text following them still gets line-start escaping. The escaping functions are also available directly for lower-level needs:

```python
from draftjs_exporter.markdown.escape import escape_link_destination, escape_text

escape_text("# Not a heading", at_line_start=True)  # "\\# Not a heading"
escape_link_destination("https://example.com/a(b)")  # "https://example.com/a\\(b\\)"
```

Limitations:

- Entity references (`&copy;`, `&#60;`) are not escaped: they decode to their character downstream rather than rendering literally. They cannot inject markup, so this is a fidelity trade-off, not a security issue.
- Text starting with four or more spaces or a tab may render as an indented code block downstream. Backslash escapes cannot protect leading whitespace.
- GFM-only syntax other than tables (`|`) is not escaped — for example autolinkable bare URLs remain autolinkable.

## Unsupported

The Markdown exporter has inherent limitations compared to the HTML exporter.

- **No underline, subscript, or other HTML-only styles**: The exporter’s default configuration falls through to inline HTML like `<sup>text</sup>`.
- **No reference-style links**: Links are always rendered inline as `[text](url)`.
- **No table support**: Draft.js has no built-in table block type, and the exporter does not attempt to generate Markdown tables from custom block types.
- **No Setext-style headings**: Headings always use ATX style (`# Heading`).
- **Entity data fidelity**: The Markdown link syntax `[text](url)` only preserves the URL.
- **Inline style nesting edge cases**: When bold and italic styles partially overlap, the exporter may produce markers that some strict Markdown parsers reject (e.g. `**Bold **_Italic_**`). Most renderers handle this correctly, but it is not guaranteed by the CommonMark spec.
