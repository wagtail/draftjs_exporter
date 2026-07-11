# Custom engines

The exporter supports using custom engines to generate its output via the `DOM` API. This can be useful to implement custom export formats, e.g. [to Markdown (experimental)](../markdown.md).

Here is an example implementation:

```python
from draftjs_exporter import DOMEngine

class DOMListTree(DOMEngine):
    """
    Element tree using nested lists.
    """

    @staticmethod
    def create_tag(t, attr=None):
        return [t, attr, []]

    @staticmethod
    def append_child(elt, child):
        elt[2].append(child)

    @staticmethod
    def render(elt):
        return elt


exporter = HTML({
    # Use the dotted module syntax to point to the DOMEngine implementation.
    'engine': 'my_project.example.DOMListTree'
})
```
