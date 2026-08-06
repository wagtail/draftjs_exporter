# Markdown importer

> ⚠️ Markdown import is **experimental**. There is no guarantee of API stability at this time.

The importer converts Markdown text into a Draft.js [ContentState](content-state.md), complementing the [Markdown export](markdown.md). It works in two phases: parsing (Markdown to ContentState) then filtering (content policy on the result). Both phases are configurable, and the filter can also be used on its own.

## Quick start

Use `MarkdownImporter` with no configuration to import standard Markdown:

```python
from draftjs_exporter import MarkdownImporter

importer = MarkdownImporter()
content_state = importer.import_markdown("# Hello\n\nWorld")
```

The result is a regular ContentState, ready to store or render with the exporter:

```python
{
    "blocks": [
        {
            "key": "00000",
            "text": "Hello",
            "type": "header-one",
            "depth": 0,
            "inlineStyleRanges": [],
            "entityRanges": [],
        },
        {
            "key": "00001",
            "text": "World",
            "type": "unstyled",
            "depth": 0,
            "inlineStyleRanges": [],
            "entityRanges": [],
        },
    ],
    "entityMap": {},
}
```

## Supported Markdown

The importer supports the CommonMark core — the constructs most real-world Markdown uses:

| Construct                              | ContentState output                                            |
| -------------------------------------- | -------------------------------------------------------------- |
| Paragraph                              | `unstyled` block                                               |
| ATX headings (`#` through `######`)    | `header-one` through `header-six`                              |
| `>` blockquote                         | `blockquote` block                                             |
| Fenced code (` ``` ` or `~~~`)         | `code-block` block                                             |
| `---` / `***` / `___` thematic break   | `atomic` block with `HORIZONTAL_RULE` entity                   |
| `* ` / `- ` / `+ ` lists               | `unordered-list-item` blocks with depth                        |
| `1. ` / `1) ` lists                    | `ordered-list-item` blocks with depth                          |
| `**bold**` / `__bold__`                | `BOLD` inline style range                                      |
| `*italic*` / `_italic_`                | `ITALIC` inline style range                                    |
| `` `code` ``                           | `CODE` inline style range                                      |
| `[text](url)`                          | `LINK` entity (data from [resolver chain](#entity-resolution)) |
| `![alt](url)`                          | `IMAGE` entity (data from resolver chain)                      |
| Hard line break (two spaces + newline) | `\n` in block text                                             |

Not supported: reference-style links, Setext headings, indented code blocks, tables, autolinks, list item continuation lines, and arbitrary HTML. Every input still parses — unsupported constructs become plain text.

## Parser configuration

`parser_config` controls which constructs the parser recognizes, and how entities are created:

| Option               | Default | Effect                                         |
| -------------------- | ------- | ---------------------------------------------- |
| `headings`           | `True`  | Parse ATX headings                             |
| `blockquote`         | `True`  | Parse `>` blockquotes                          |
| `code_fenced`        | `True`  | Parse fenced code blocks                       |
| `thematic_break`     | `True`  | Parse thematic breaks                          |
| `unordered_list`     | `True`  | Parse unordered lists                          |
| `ordered_list`       | `True`  | Parse ordered lists                            |
| `emphasis`           | `True`  | Parse bold and italic                          |
| `code_inline`        | `True`  | Parse backtick code spans                      |
| `links`              | `True`  | Parse `[text](url)` links                      |
| `images`             | `True`  | Parse `![alt](url)` images                     |
| `line_breaks`        | `True`  | Strip two-space hard break markers             |
| `link_resolvers`     | `[]`    | Resolver chain for link URLs                   |
| `image_resolvers`    | `[]`    | Resolver chain for image URLs                  |
| `inline_html_styles` | `{}`    | Whitelist of HTML tags mapped to inline styles |

Disabled constructs pass through as plain text. For example, with `"headings": False`, the source `# Title` imports as a paragraph containing the literal text `# Title`.

```python
importer = MarkdownImporter({
    "parser_config": {"blockquote": False},
})
```

## Entity resolution

When the parser encounters a link or image, it passes the URL (and the label or alt text) through a chain of resolvers. Each resolver either returns a resolution — entity type, data, and mutability — or `None` to defer to the next resolver. If no resolver matches, the default applies:

- Links: `LINK` entity with `{"url": url}`
- Images: `IMAGE` entity with `{"src": url, "alt": alt}`

Resolvers can return any entity type, so a single chain can route different URL shapes to different entities. This makes it possible to import internal representations of links and media, for example a CMS that references pages and images by ID rather than URL.

### The `scheme_resolver` helper

`scheme_resolver` builds a resolver for URLs of the form `scheme://kind?key=value`:

```python
from draftjs_exporter import MarkdownImporter, scheme_resolver

importer = MarkdownImporter({
    "parser_config": {
        "link_resolvers": [
            scheme_resolver(
                "wagtail",
                {"page": "LINK", "document": "DOCUMENT"},
                coerce={"id": int},
            ),
        ],
        "image_resolvers": [
            scheme_resolver(
                "wagtail",
                {"image": "IMAGE", "media": "EMBED"},
                coerce={"id": int},
                label_key="alt",
                mutability="IMMUTABLE",
            ),
        ],
    },
})
```

With this configuration:

- `[label](wagtail://page?id=3)` imports as a `LINK` entity with data `{"id": 3}`.
- `[label](wagtail://document?id=1)` imports as a `DOCUMENT` entity.
- `![alt](wagtail://image?id=10&format=left)` imports as an `IMAGE` entity with data `{"id": 10, "format": "left", "alt": "alt"}` — the `label_key` fills `alt` from the Markdown alt text when the query string omits it.
- `![alt](/media/example.jpg)` matches no resolver, so it imports with the default `{"src": "/media/example.jpg", "alt": "alt"}`.

Parameters:

- `scheme`: the URL scheme to match, such as `"wagtail"`.
- `type_map`: maps the URL host to an entity type.
- `coerce`: optional per-key converters for query string values, such as `{"id": int}`.
- `label_key`: optional data key filled from the Markdown label. Use it for image alt text; leave it unset for links, whose label is link text rather than entity data.
- `mutability`: mutability for produced entities, `"MUTABLE"` by default.

### Custom resolvers

A resolver is any callable taking `(url, label)` and returning a resolution or `None`:

```python
def user_mentions(url, label):
    if url.startswith("wagtail://user"):
        username = url.partition("username=")[2]
        return {"type": "LINK", "data": {"username": username}}
    return None

importer = MarkdownImporter({
    "parser_config": {"link_resolvers": [user_mentions]},
})
```

Resolvers run in order; the first non-`None` result wins. A resolution must include a `type`, and `data` must be a dict when present — anything else raises `MarkdownParseError`.

## Inline HTML

Markdown has no syntax for some inline styles, such as superscript and subscript. The `inline_html_styles` option whitelists paired HTML tags to import as inline styles:

```python
from draftjs_exporter import INLINE_STYLES, MarkdownImporter

importer = MarkdownImporter({
    "parser_config": {
        "inline_html_styles": {
            "sup": INLINE_STYLES.SUPERSCRIPT,
            "sub": INLINE_STYLES.SUBSCRIPT,
        },
    },
})
content_state = importer.import_markdown("E = mc<sup>2</sup>")
```

Tag content is parsed recursively, so `<sup>**bold**</sup>` produces both `SUPERSCRIPT` and `BOLD` ranges. Tags with attributes, unclosed tags, and tags outside the whitelist pass through as literal text — the importer never interprets arbitrary HTML, so there is no markup injection surface. The default whitelist is empty.

## Filtering

`filter_rules` apply content policy to the parsed ContentState — removing or transforming blocks, inline styles, and entities. Each rule has a `type` (what to match), a `match` (the type to match), and an `action`:

| Action     | Effect                                                                    |
| ---------- | ------------------------------------------------------------------------- |
| `"remove"` | Delete matching objects                                                   |
| `"keep"`   | No-op                                                                     |
| `"demote"` | Headings only: `header-one` becomes `header-two`, and so on               |
| callable   | Receives the matched object, returns a replacement or `None` to remove it |

For example, to demote all level-1 headings on import:

```python
from draftjs_exporter import BLOCK_TYPES, MarkdownImporter

importer = MarkdownImporter({
    "filter_rules": [
        {"type": "block", "match": BLOCK_TYPES.HEADER_ONE, "action": "demote"},
    ],
})
```

Objects without a matching rule are kept. The filter always produces a valid ContentState: entity ranges and the entity map stay in sync, and list depths are re-normalized when items are removed.

`ContentStateFilter` can also be used standalone, on any ContentState:

```python
from draftjs_exporter import ContentStateFilter

filter_ = ContentStateFilter([
    {"type": "entity", "match": "LINK", "action": "remove"},
])
filtered = filter_.apply(content_state)
```

## Errors

`MarkdownParseError` is raised when input cannot be imported, carrying a `line` number and `message`. With the built-in parser, this happens when an entity resolver raises an exception or returns a malformed resolution. Nearly all text is valid Markdown, so other inputs parse successfully — by design, there are no "invalid Markdown" errors.

```python
from draftjs_exporter import MarkdownImporter, MarkdownParseError

try:
    content_state = MarkdownImporter().import_markdown(markdown)
except MarkdownParseError as e:
    print(f"Import failed at line {e.line}: {e.message}")
```

## Custom parser engines

The parser is referenced by dotted path in the importer config, so an alternative engine — for example one backed by a full CommonMark parser — can replace the built-in one:

```python
importer = MarkdownImporter({
    "parser": "my_project.markdown.MistuneParser",
})
```

A parser engine is a class accepting a config dict (or `None`) and exposing `parse(markdown: str) -> ContentState`. Filtering applies to the engine's output as usual.

## Escaping

The importer inverts [CommonMark backslash escapes](https://spec.commonmark.org/current/#backslash-escapes): any ASCII punctuation character preceded by `\` is imported as that literal character. This mirrors the [Markdown exporter's text escaping](markdown.md#escaping) so that Markdown the exporter produces round-trips back to the original text.

```python
MarkdownImporter().import_markdown(r"\# Not a heading, \*not emphasis\*")
# text: "# Not a heading, *not emphasis*" (paragraph, no styles)
```

Link and image destinations are also unescaped: `\(`, `\)`, and `\\` inside `](…)` revert to the literal characters, matching what the exporter emits for URLs containing parentheses.

### Known round-trip limitations

- **Underscore emphasis and mid-word italic.** The exporter's default italic marker is `_`, and it leaves intraword `_` runs unescaped (treating them as inert per CommonMark flanking). The importer cannot apply full CommonMark flanking to invert this, because the exporter also emits intraword `_` markers for legitimate mid-word italic (e.g. `fan_tastic_` for italic on "tastic"). Those two cases are structurally identical to plain identifiers like `foo_bar_baz`, so the importer has no way to tell them apart. As a result, multi-underscore identifiers may import as spurious emphasis. Resolving this fully requires an exporter-side change (use `*` for italic when the marker would be intraword, or default italic to `*`).

Percent-encoding the exporter applies to whitespace and control characters inside link destinations is left intact: `%20` is a valid URL byte sequence, not a Markdown escape, so it is not decoded.

## Safety guarantees

- **Structural integrity**: the parser always produces valid ContentState (unique block keys, entity ranges backed by the entity map, in-bounds ranges) or raises `MarkdownParseError`.
- **Content control**: filtering is declarative and always produces valid ContentState.
- **No markup injection**: unrecognized HTML passes through as literal text; only whitelisted inline tags are interpreted.
