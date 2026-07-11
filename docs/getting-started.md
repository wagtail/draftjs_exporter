# Getting started

Draft.js stores data in a JSON representation based on blocks, representing lines of content in the editor, annotated with entities and styles to represent rich text. To understand the data model in depth, read [Content state](content-state.md) first.

This exporter takes the Draft.js ContentState data as input, and outputs HTML based on its [configuration](reference/configuration.md). To get started, install the package:

```sh
pip install draftjs_exporter
```

We support the following Python versions: 3.10, 3.11, 3.12, 3.13, 3.14, 3.15. For legacy Python versions, find compatible releases in the [CHANGELOG](https://github.com/wagtail/draftjs_exporter/blob/main/CHANGELOG.md).

In your code, create an exporter and use the `render` method to produce HTML. Pass an empty config dict to use the default block, style, and entity maps — see [Configuration](reference/configuration.md) to customize them.

```python
from draftjs_exporter import HTML

exporter = HTML({})

html = exporter.render({
    'entityMap': {},
    'blocks': [{
        'key': '6m5fh',
        'text': 'Hello, world!',
        'type': 'unstyled',
        'depth': 0,
        'inlineStyleRanges': [],
        'entityRanges': []
    }]
})

print(html)
```

For details on the ContentState structure of blocks / inline styles / entities, read [our content state overview](content-state.md).

You can also run an example by downloading this repository and then using `python example.py`, or by using our [online Draft.js demo](http://playground.draftail.org/).

> By default, the exporter uses a dependency-free `string` engine to build the DOM tree. If you need HTML escaping and sanitization, or have an existing `lxml`/`html5lib` setup, see [Alternative engines](guides/alternative-engines.md) to pick the right one.

## Type annotations

The exporter's codebase uses static type annotations, checked with mypy and ty. Reusable types are made available so you can annotate your own components:

```python
from draftjs_exporter import DOM, Element, Props

def image(props: Props) -> Element:
    return DOM.create_element('img', {
        'src': props.get('src'),
        'width': props.get('width'),
        'height': props.get('height'),
        'alt': props.get('alt'),
    })
```

See [Custom components](guides/custom-components.md) for the full component API.

## Next steps

- [Configuration](reference/configuration.md) – map Draft.js block types, styles, and entities to HTML.
- [Custom components](guides/custom-components.md) – render arbitrary markup from entity and block data.
- [API reference](reference/api.md) – the full public API.
- [Troubleshooting](troubleshooting.md) – known issues and implementation details.
