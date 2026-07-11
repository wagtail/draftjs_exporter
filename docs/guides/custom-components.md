# Custom components

To generate arbitrary markup with dynamic data, the exporter comes with an API to create rendering components. This API mirrors React's [createElement](https://facebook.github.io/react/docs/top-level-api.html#react.createelement) API (what JSX compiles to). Components are referenced from your [configuration](../reference/configuration.md) under `block_map`, `style_map`, and `entity_decorators`.

```python
# All of the API is available from a single `DOM` namespace
from draftjs_exporter.dom import DOM


# Components are simple functions that take `props` as parameter and return DOM elements.
def image(props):
    # This component creates an image element, with the relevant attributes.
    # `props` is the entity's `data` dict (for entity components),
    # or the block's data + children (for block components).
    return DOM.create_element('img', {
        'src': props.get('src'),
        'width': props.get('width'),
        'height': props.get('height'),
        'alt': props.get('alt'),
    })


def blockquote(props):
    # This component uses block data to render a blockquote.
    # `props['block']` is the Draft.js block object,
    # `props['children']` is the already-rendered content for this block.
    block_data = props['block']['data']

    # Here, we want to display the block's content so we pass the `children` prop as the last parameter.
    return DOM.create_element('blockquote', {
        'cite': block_data.get('cite')
    }, props['children'])


def button(props):
    # Entity components receive the entity's `data` as props.
    # Note: the `entity` and `children` keys are reserved by the exporter.
    # See the "Entity props override" entry in Troubleshooting.
    href = props.get('href', '#')
    icon_name = props.get('icon', None)
    text = props.get('text', '')

    return DOM.create_element('a', {
            'class': 'icon-text' if icon_name else None,
            'href': href,
        },
        # There can be as many `children` as required.
        # It is also possible to reuse other components and render them instead of HTML tags.
        DOM.create_element(icon, {'name': icon_name}) if icon_name else None,
        DOM.create_element('span', {'class': 'icon-text'}, text) if icon_name else text
    )
```

Apart from `create_element`, a `parse_html` method is also available. Use it to interface with other HTML generators, like template engines – at your own risk: that method does not sanitize the input.

See [`example.py`](https://github.com/wagtail/draftjs_exporter/blob/main/example.py) in the repository for more details. For the full list of block types, inline styles, and entity types, see the [API reference](../reference/api.md).
