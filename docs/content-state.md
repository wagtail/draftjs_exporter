# Content state

[Draft.js](https://draftjs.org/) stores rich text in a structured JSON representation called ContentState. The exporter takes this ContentState as input and converts it to HTML (or Markdown), based on its [configuration](reference/configuration.md). This page explains how Draft.js models content, so you know what to feed the exporter and what to expect from each block, entity, and inline style.

## How Draft.js represents rich text

Draft.js uses a fixed schema with predefined rich text types. There are strong constraints on content structure: what is block-level formatting, what is inline, what can carry data, and how. For storage and transport, Draft.js editors output a [raw ContentState](https://www.draftail.org/docs/next/draft-js/api-reference/data-conversion#converttoraw) representation that is serializable as JSON.

Here is a simple rich text example, in the shape you would pass it to the exporter:

```python
from draftjs_exporter import HTML

content_state = {
    # All content is stored as a list of blocks, each representing a line.
    "blocks": [
        {
            # Every block has a unique key, its text, and a type.
            # "unstyled" is the default, used for plain paragraphs.
            "key": "b1ito",
            "text": "Example of the Draft.js ContentState.",
            "type": "unstyled",
            # Depth is greater than 0 when the block is nested (e.g. list items).
            "depth": 0,
            # Inline formatting is stored as ranges over the text.
            # Ranges can overlap.
            "inlineStyleRanges": [
                {
                    # offset and length are character positions within `text`.
                    "offset": 15,
                    "length": 8,
                    "style": "BOLD",
                },
            ],
            # Entities (links, images, embeds) also use ranges, but cannot overlap.
            # Each range points to an entry in `entityMap` by key.
            "entityRanges": [
                {
                    "offset": 24,
                    "length": 12,
                    "key": 0,
                },
            ],
            # Blocks can carry additional data (e.g. a blockquote's `cite` URL).
            "data": {},
        },
    ],
    # The entity map holds the data for every entity referenced from blocks.
    "entityMap": {
        0: {
            "type": "LINK",
            # MUTABLE entities can be edited in place (like a link on text).
            "mutability": "MUTABLE",
            "data": {
                "url": "https://www.draftail.org/docs/next/draft-js/api-reference/content-state",
            },
        },
    },
}

# Pass the ContentState to the exporter's render method.
html = HTML({}).render(content_state)
```

## Blocks

Think of blocks as [block-level elements](https://developer.mozilla.org/en-US/docs/Web/HTML/Block-level_elements) in HTML: headings, paragraphs, embeds, and so on. They direct the flow of the content, taking up the whole width of their containers and following one another vertically. All of the editor's content is stored in the `blocks` array.

Draft.js represents each block with the following attributes:

- `key`, a unique identifier for the block.
- `text`, the block's content in plain-text form.
- `type`, defining how the block behaves in the editor as well as how it should be displayed to end users.
- `depth`, whether the block is visually nested (for example in lists), and if so by how many levels.
- `inlineStyleRanges`, indicating where styles are applied in the text.
- `entityRanges`, indicating where entities are applied.
- `data`, additional data or metadata stored alongside the block.

## Block type

The block `type` generally defines how a block is meant to be used in the editor, and displayed later on in the content lifecycle. Blocks are `unstyled` by default.

Draft.js comes with predefined types, which generally map to HTML elements:

- `unstyled`
- `header-one`
- `header-two`
- `header-three`
- `header-four`
- `header-five`
- `header-six`
- `unordered-list-item`
- `ordered-list-item`
- `blockquote`
- `code-block`
- `atomic`, used for embedded, mostly non-textual content.

The exporter exposes these as the `BLOCK_TYPES` constants. See the [API reference](reference/api.md) for the full list, including the special `BLOCK_TYPES.FALLBACK` used to handle missing block types in your [configuration](reference/configuration.md).

## Inline styles

`inlineStyleRanges` lists all of the locations in the block's text where styles have been applied, based on starting `offset` and `length`. When multiple styles are applied to a given chunk of text, the ranges can overlap.

Draft.js comes with predefined inline styles:

- `BOLD`
- `CODE`
- `ITALIC`
- `STRIKETHROUGH`
- `UNDERLINE`

The exporter recognizes these as the `INLINE_STYLES` constants, and supports additional styles such as `SUPERSCRIPT`, `SUBSCRIPT`, and `KEYBOARD`. See the [API reference](reference/api.md) for the full list.

## Entities

Like for styles, `entityRanges` lists the positions in `text` where entities are applied as an `offset` and `length`. These cannot overlap. Entity ranges point to an entry in the `entityMap` by `key`.

In the `entityMap`, entities are stored as:

- `type`, like for blocks, defining how the entity behaves in the editor and how it should be displayed.
- `mutability` (`MUTABLE` or `IMMUTABLE`), whether changes in the text the entity is applied on are allowed (links on arbitrary text vs. mentions containing a person's full name, for example).
- `data`, to store arbitrary data for the entity.

The exporter exposes common entity categories as the `ENTITY_TYPES` constants (`LINK`, `IMAGE`, `HORIZONTAL_RULE`, and more). See the [API reference](reference/api.md) for the full list, including the special `ENTITY_TYPES.FALLBACK`.

## EditorState vs ContentState

ContentState is what Draft.js uses to represent the editor's content, but content is only one part of the editor's state. [`EditorState`](https://www.draftail.org/docs/next/draft-js/api-reference/editor-state) stores everything else: text selection, the undo/redo stack, and more.

The exporter only consumes ContentState. When an editor saves content, it converts its EditorState to a raw ContentState (the JSON shape above), and that is what you hand to [`HTML.render()`](reference/api.md). You do not need to handle EditorState on the Python side.

## Next steps

- [Getting started](getting-started.md) – render your first ContentState to HTML.
- [Configuration](reference/configuration.md) – map Draft.js block types, styles, and entities to HTML.
- [Custom components](guides/custom-components.md) – render arbitrary markup from entity and block data.
