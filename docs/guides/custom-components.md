# Custom components

To generate arbitrary markup with dynamic data, the exporter comes with an API to create rendering components. This API mirrors React's [createElement](https://facebook.github.io/react/docs/top-level-api.html#react.createelement) API (what JSX compiles to). Components are referenced from your [configuration](../reference/configuration.md) under `block_map`, `style_map`, and `entity_decorators`.

All of the API is available from a single `DOM` namespace:

```python
from draftjs_exporter import DOM
```

Components are simple functions that take a `props` dict as parameter and return DOM elements. The shape of `props` depends on what the component is rendering: entities, blocks, or inline styles each pass different data.

## Entity components

Entity components render things like links, images, or embeds. They receive the entity's `data` dict as `props`. For example, an `IMAGE` entity whose Draft.js `data` is `{"src": ..., "width": ..., "height": ..., "alt": ...}` can be rendered as an `<img>` element:

```python
def image(props):
    return DOM.create_element('img', {
        'src': props.get('src'),
        'width': props.get('width'),
        'height': props.get('height'),
        'alt': props.get('alt'),
    })
```

Wire the component into your [configuration](../reference/configuration.md) under `entity_decorators`, keyed by the entity type it handles.

> The `entity` and `children` keys in `props` are reserved by the exporter and override any value your entity `data` might carry under the same key. See [Entity props override](../troubleshooting.md#entity-props-override) for details and workarounds.

## Block components

Block components render block-level elements like headings, paragraphs, or blockquotes. They receive two things in `props`: `block`, the Draft.js block object (with its `type`, `data`, `depth`, etc.), and `children`, the already-rendered content for this block.

For example, to render a blockquote that uses the block's `cite` data:

```python
def blockquote(props):
    block_data = props['block']['data']
    return DOM.create_element('blockquote', {
        'cite': block_data.get('cite')
    }, props['children'])
```

Pass `props['children']` as the last argument to `DOM.create_element` so the block's content is displayed inside the element you create.

The package also ships two reusable block components you can import from the root:

```python
from draftjs_exporter import code_block, render_children
```

- `code_block` wraps children in `<pre><code>…</code></pre>` (used by default for `BLOCK_TYPES.CODE`).
- `render_children` returns children with no wrapping markup (used by default for `BLOCK_TYPES.ATOMIC`).

Reuse them when extending `BLOCK_MAP`, or as a starting point for your own components.

## Nesting and reusing components

`DOM.create_element` accepts any number of children after the props dict. Children can be strings, DOM elements, other components, or `None` (which renders nothing). This lets you compose components the same way you would compose HTML tags.

The following component renders a link with an optional icon. When an icon name is present, it renders the `icon` component alongside the text inside a wrapper `<a>`; otherwise, it renders the text alone:

```python
def button(props):
    href = props.get('href', '#')
    icon_name = props.get('icon', None)
    text = props.get('text', '')

    return DOM.create_element('a', {
        'class': 'icon-text' if icon_name else None,
        'href': href,
    },
        DOM.create_element(icon, {'name': icon_name}) if icon_name else None,
        DOM.create_element('span', {'class': 'icon-text'}, text) if icon_name else text,
    )
```

## Other DOM methods

Apart from `create_element`, a `parse_html` method is also available. Use it to interface with other HTML generators, like template engines – at your own risk: that method does not sanitize the input.

## Next steps

- See [`example.py`](https://github.com/wagtail/draftjs_exporter/blob/main/example.py) for a fully-fledged demo of custom components.
- For the full list of block types, inline styles, and entity types, see the [API reference](../reference/api.md).
- To handle missing block, style, or entity types, read [Fallback components](fallback-components.md).
