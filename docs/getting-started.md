# Getting started

Draft.js stores data in a JSON representation based on blocks, representing lines of content in the editor, annotated with entities and styles to represent rich text. For more information, [this article](https://medium.com/@rajaraodv/how-draft-js-represents-rich-text-data-eeabb5f25cf2) covers the concepts further.

This exporter takes the Draft.js ContentState data as input, and outputs HTML based on its configuration. To get started, install the package:

```sh
pip install draftjs_exporter
```

We support the following Python versions: 3.10, 3.11, 3.12, 3.13, 3.14, 3.15. For legacy Python versions, find compatible releases in the [CHANGELOG](https://github.com/wagtail/draftjs_exporter/blob/main/CHANGELOG.md).

In your code, create an exporter and use the `render` method to create HTML:

```python
from draftjs_exporter.dom import DOM
from draftjs_exporter.html import HTML

# Configuration options are detailed below.
config = {}

# Initialize the exporter.
exporter = HTML(config)

# Render a Draft.js `contentState`
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

You can also run an example by downloading this repository and then using `python example.py`, or by using our [online Draft.js demo](http://playground.draftail.org/).

## Type annotations

The exporter’s codebase uses static type annotations, checked with mypy and ty. Reusable types are made available:

```python
from draftjs_exporter import DOM, Element, Props


# Components are simple functions that take `props` as parameter and return DOM elements.
def image(props: Props) -> Element:
    # This component creates an image element, with the relevant attributes.
    return DOM.create_element('img', {
        'src': props.get('src'),
        'width': props.get('width'),
        'height': props.get('height'),
        'alt': props.get('alt'),
    })
```
