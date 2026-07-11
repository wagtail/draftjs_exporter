# Configuration

The exporter output is extensively configurable to cater for varied rich text requirements.

> This page documents the configuration shape. To see these options used in context, read [Custom components](../guides/custom-components.md) and [Fallback components](../guides/fallback-components.md). For alternative DOM backends, see [Alternative engines](../guides/alternative-engines.md).

```python
# draftjs_exporter provides default configurations and predefined constants for reuse.
from draftjs_exporter.constants import BLOCK_TYPES, ENTITY_TYPES
from draftjs_exporter.defaults import BLOCK_MAP, STYLE_MAP
from draftjs_exporter.dom import DOM

config = {
    # `block_map` is a mapping from Draft.js block types to a definition of their HTML representation.
    # Extend BLOCK_MAP to start with sane defaults, or make your own from scratch.
    'block_map': {
        **BLOCK_MAP,
        # The most basic mapping format, block type to tag name.
        BLOCK_TYPES.HEADER_TWO: 'h2',
        # Use a dict to define props on the block.
        BLOCK_TYPES.HEADER_THREE: {'element': 'h3', 'props': {'class': 'u-text-center'}},
        # Add a wrapper (and wrapper_props) to wrap adjacent blocks.
        BLOCK_TYPES.UNORDERED_LIST_ITEM: {
            'element': 'li',
            'wrapper': 'ul',
            'wrapper_props': {'class': 'bullet-list'},
        },
        # Use a custom component for more flexibility (reading block data or depth).
        # See the Custom components guide for how to write one.
        BLOCK_TYPES.BLOCKQUOTE: blockquote,
        BLOCK_TYPES.ORDERED_LIST_ITEM: {
            'element': list_item,
            'wrapper': ordered_list,
        },
        # Provide a fallback component (advanced).
        # See the Fallback components guide for how to write one.
        BLOCK_TYPES.FALLBACK: block_fallback
    },
    # `style_map` defines the HTML representation of inline elements.
    # Extend STYLE_MAP to start with sane defaults, or make your own from scratch.
    'style_map': {
        **STYLE_MAP,
        # Use the same mapping format as in the `block_map`.
        'KBD': 'kbd',
        # The `style` prop can be defined as a dict, that will automatically be converted to a string.
        'HIGHLIGHT': {'element': 'strong', 'props': {'style': {'textDecoration': 'underline'}}},
        # Provide a fallback component (advanced).
        # See the Fallback components guide for how to write one.
        INLINE_STYLES.FALLBACK: style_fallback,
    },
    'entity_decorators': {
        # Map entities to components so they can be rendered with their data.
        # See the Custom components guide for how to write one.
        ENTITY_TYPES.IMAGE: image,
        ENTITY_TYPES.LINK: link
        # Lambdas work too.
        ENTITY_TYPES.HORIZONTAL_RULE: lambda props: DOM.create_element('hr'),
        # Discard those entities.
        ENTITY_TYPES.EMBED: None,
        # Provide a fallback component (advanced).
        ENTITY_TYPES.FALLBACK: entity_fallback,
    },
    'composite_decorators': [
        # Use composite decorators to replace text based on a regular expression.
        {
            'strategy': re.compile(r'\n'),
            'component': br,
        },
        {
            'strategy': re.compile(r'#\w+'),
            'component': hashtag,
        },
        {
            'strategy': LINKIFY_RE,
            'component': linkify,
        },
    ],
}
```

See [examples.py](https://github.com/wagtail/draftjs_exporter/blob/main/example.py) as a fully-fledged demo of the configuration. For the full list of block types, inline styles, and entity types the exporter recognizes, see the [API reference](api.md).
