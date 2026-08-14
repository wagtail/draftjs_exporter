# Configuration

The exporter output is extensively configurable to cater for varied rich text requirements.

> This page documents the configuration shape. To see these options used in context, read [Custom components](../guides/custom-components.md) and [Fallback components](../guides/fallback-components.md). For alternative DOM backends, see [Alternative engines](../guides/alternative-engines.md).

The configuration is a single dict passed to `HTML()`. It has four keys: `block_map`, `style_map`, `entity_decorators`, and `composite_decorators`. Each is optional and can be combined with the defaults the exporter provides.

```python
from draftjs_exporter import (
    BLOCK_MAP,
    BLOCK_TYPES,
    DOM,
    ENTITY_TYPES,
    INLINE_STYLES,
    STYLE_MAP,
    code_block,
    render_children,
)
```

The exporter ships with `BLOCK_MAP` and `STYLE_MAP` — sensible defaults for common HTML elements. Extend them with `**` to start from the defaults, or build your own from scratch. The default `CODE` and `ATOMIC` entries use the reusable `code_block` and `render_children` components; import those when you want the same behavior in a custom map.

## Block map

`block_map` maps Draft.js block types to their HTML representation. The simplest mapping is a block type to a tag name:

```python
config = {
    "block_map": {
        **BLOCK_MAP,
        BLOCK_TYPES.HEADER_TWO: "h2",
    },
}
```

Use a dict instead of a string to define props on the element:

```python
BLOCK_TYPES.HEADER_THREE: {'element': 'h3', 'props': {'class': 'u-text-center'}},
```

Add a `wrapper` (and `wrapper_props`) to wrap adjacent blocks. This is how list items get their surrounding `<ul>` or `<ol>`:

```python
BLOCK_TYPES.UNORDERED_LIST_ITEM: {
    'element': 'li',
    'wrapper': 'ul',
    'wrapper_props': {'class': 'bullet-list'},
},
```

For more flexibility — reading block data or depth — point the `element` at a [custom component](../guides/custom-components.md) instead of a tag name:

```python
BLOCK_TYPES.BLOCKQUOTE: blockquote,
BLOCK_TYPES.ORDERED_LIST_ITEM: {
    'element': list_item,
    'wrapper': ordered_list,
},
```

## Style map

`style_map` defines the HTML representation of inline styles. It uses the same mapping format as `block_map`: a string for the simplest case, a dict to add props.

```python
config = {
    "style_map": {
        **STYLE_MAP,
        "KBD": "kbd",
        "HIGHLIGHT": {
            "element": "strong",
            "props": {"style": {"textDecoration": "underline"}},
        },
    },
}
```

The `style` prop can be a string (rendered as-is) or a dict, in which case its properties are converted to a CSS string using `camel_to_dash`.

## Entity decorators

`entity_decorators` maps entity types to components so they can be rendered with their data. Each value is a [custom component](../guides/custom-components.md) function, a lambda, or `None` to discard that entity type entirely.

```python
config = {
    "entity_decorators": {
        ENTITY_TYPES.IMAGE: image,
        ENTITY_TYPES.LINK: link,
        ENTITY_TYPES.HORIZONTAL_RULE: lambda props: DOM.create_element("hr"),
        ENTITY_TYPES.EMBED: None,
    },
}
```

## Composite decorators

Composite decorators replace text based on a regular expression. Use them for line breaks, mentions, linkification, or any text-level transformation that isn't an entity in the Draft.js data.

Each entry is a dict with a `strategy` (compiled regex) and a `component` (a [custom component](../guides/custom-components.md) function):

```python
config = {
    "composite_decorators": [
        {"strategy": re.compile(r"\n"), "component": br},
        {"strategy": re.compile(r"#\w+"), "component": hashtag},
        {"strategy": LINKIFY_RE, "component": linkify},
    ],
}
```

## Fallbacks

Each map accepts a special fallback key — `BLOCK_TYPES.FALLBACK`, `INLINE_STYLES.FALLBACK`, or `ENTITY_TYPES.FALLBACK` — that is triggered when the exporter encounters a type with no explicit mapping. See [Fallback components](../guides/fallback-components.md) for how to write one.

## Putting it all together

See [`example.py`](https://github.com/wagtail/draftjs_exporter/blob/main/example.py) as a fully-fledged demo of the configuration. For the full list of block types, inline styles, and entity types the exporter recognizes, see the [API reference](api.md).
