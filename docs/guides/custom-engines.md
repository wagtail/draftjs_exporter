---
description: "Implement a custom draftjs_exporter engine through the DOM API, to generate output other than HTML or reuse an existing tree library."
---

# Custom engines

The exporter supports using custom engines to generate its output via the `DOM` API. This can be useful to implement custom export formats, e.g. [to Markdown (experimental)](../markdown.md).

A custom engine is a subclass of `DOMEngine` that implements the `create_tag`, `append_child`, and `render` methods. `DOMEngine` is not exported from the package root. Here is a minimal example that represents the DOM as nested Python lists:

```python
from draftjs_exporter.engines.base import DOMEngine


class DOMListTree(DOMEngine):
    """Element tree using nested lists."""

    @staticmethod
    def create_tag(t, attr=None):
        return [t, attr, []]

    @staticmethod
    def append_child(elt, child):
        elt[2].append(child)

    @staticmethod
    def render(elt):
        return elt
```

Reference your engine in the exporter config using dotted module syntax, so the exporter can import it at runtime:

```python
exporter = HTML(
    {
        "engine": "my_project.example.DOMListTree",
    }
)
```
