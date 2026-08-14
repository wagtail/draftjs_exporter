# Migration guide

This page collects the upgrade notes for each major (and selected minor) release of the exporter. Each section describes the breaking changes and the steps to follow when upgrading from the previous version. For the full list of changes in each release, see the [CHANGELOG](https://github.com/wagtail/draftjs_exporter/blob/main/CHANGELOG.md).

## Upgrading to v7.0.0

### Markdown export now escapes text

The Markdown exporter now escapes user-controlled text and link destinations following CommonMark rules, so content like `#`, `[`, `<`, or `&` in block text renders literally instead of being interpreted as Markdown or HTML. Code spans and code blocks are not escaped; their delimiters are instead sized to the content, which also fixes output corruption when code content contains backticks or fences.

Any Markdown output containing metacharacters in text changes. If your tests compare exact Markdown output, update them. Markdown support remains experimental.

## Upgrading to v6.0.0

### Python 3.7, 3.8, and 3.9 support removed

Python 3.7, 3.8, and 3.9 are no longer supported. For projects still on these versions, keep using [v5.2.0](https://github.com/wagtail/draftjs_exporter/tree/v5.2.0).

### Cleaner nested inline style output

The exporter now produces fewer redundant tags in nested and partially nested inline style output. For example, a bold range covering `[0-11]` and an italic range covering `[5-11]` now produce `<strong>Bold <em>Italic</em></strong>` rather than `<strong>Bold </strong><strong><em>Italic</em></strong>`. The output is semantically equivalent but produces different HTML. If your code or tests compare exact output strings, update them. See [Troubleshooting](troubleshooting.md#exporter-behavior) for details.

### lxml lower bound raised

The lower bound of the optional `lxml` dependency is now `>=4.6.5`. If you use the `lxml` engine, make sure your installed version meets this requirement.

## Upgrading to v5.0.0

### Python 3.6 support removed

Python 3.6 is no longer supported, as it has reached its [end of life](https://www.python.org/dev/peps/pep-0494/). For projects needing Python 3.6, keep using [v4.1.2](https://github.com/wagtail/draftjs_exporter/tree/v4.1.2).

### New `string_compat` engine

A new `string_compat` engine is available for maximum output stability. It produces identical output to the first release of the `string` engine, with no backwards-incompatible changes since. To use it, set the `engine` property in your config:

```python
config = {
    "engine": DOM.STRING_COMPAT,
}
```

If you relied on the old `string` engine's output and it changed in a way that breaks your tests, switch to `string_compat` to restore the previous behavior. See [Alternative engines](guides/alternative-engines.md) for the full list of engines.

## Upgrading to v4.0.0

### Python 3.5 support removed

Do not upgrade to this version if you are using the exporter in Python 3.5. Keep using [v3.0.1](https://github.com/wagtail/draftjs_exporter/tree/v3.0.1).

### HTML attributes no longer sorted alphabetically (string engine)

The default `string` engine no longer sorts attributes alphabetically by name in its output HTML. This makes it possible to control the order of attributes as needed, wherever attributes are specified:

```python
def image(props):
    return DOM.create_element(
        "img",
        {
            "src": props.get("src"),
            "width": props.get("width"),
            "height": props.get("height"),
            "alt": props.get("alt"),
        },
    )
```

If you relied on alphabetical sorting, you can either reorder your `props` / `wrapper_props` / `create_element` calls as needed, or subclass the built-in `string` engine and override its `render_attrs` method to add back the sort:

```python
    @staticmethod
    def render_attrs(attr: Attr) -> str:
        attrs = [f' {k}="{escape(v)}"' for k, v in attr.items()]
        attrs.sort()
        return "".join(attrs)
```

### HTML quotes no longer escaped outside attributes (string engine)

The default `string` engine no longer escapes single and double quotes in HTML content (it still escapes quotes inside attributes). If you relied on this behavior, subclass the built-in `string` engine and override its `render_children` method to add back `quote=True`:

```python
@staticmethod
def render_children(children: Sequence[Union[HTML, Elt]]) -> HTML:
    return "".join(
        [
            DOMString.render(c) if isinstance(c, Elt) else escape(c, quote=True)
            for c in children
        ]
    )
```

### Inline style properties no longer sorted alphabetically

The exporter supports passing the `style` attribute as a dictionary with JS-style property names, and automatically converts it to a CSS string. The properties are no longer sorted alphabetically — you can now reorder the dictionary's keys to control the output order.

If you relied on alphabetical sorting, either reorder the keys as needed, or pass the `style` as a string (with standard CSS property syntax).

## Upgrading to v3.0.0

### Python 2.7 and 3.4 support removed

Do not upgrade to this version if you are using the exporter in Python 2.7 or 3.4. Keep using [v2.1.7](https://github.com/wagtail/draftjs_exporter/tree/v2.1.7).

### PEP-484 type annotations

The exporter now ships with [PEP-484](https://www.python.org/dev/peps/pep-0484/) type annotations on its public API. If your codebase uses a type checker, there is a chance these annotations will create conflicts with your project's annotations — if there are discrepancies between the expected input/output of the exporter, or in the configuration. In this case, update your project's type annotations or stubs to match the expected types of the exporter's public API.

If you believe there is a problem with how the public API is typed, [open a new issue](https://github.com/wagtail/draftjs_exporter/issues/new/choose).

## Upgrading to v2.0.0

### New default engine

The default DOM engine changed from `html5lib` to `string` (a dependency-free engine). To start using the new default:

1. Remove the `engine` property from the exporter configuration, or set `'engine': DOM.STRING,`.
2. You can also remove the `html5lib` and `beautifulsoup4` dependencies from your project if they aren't used anywhere else.

To keep using the previous default (html5lib):

1. Set the `engine` property to `'engine': DOM.HTML5LIB,`.
2. Make sure you install the exporter with `pip install draftjs_exporter[html5lib]`.

See [Alternative engines](guides/alternative-engines.md) for the details of each engine.

### Decorator component definitions

Class-based decorators are no longer supported. Decorator components now require the function syntax (see [Custom components](guides/custom-components.md)):

```python
# Before:
class OrderedList:
    def render(self, props):
        depth = props["block"]["depth"]
        return DOM.create_element(
            "ol", {"class": f"list--depth-{depth}"}, props["children"]
        )


# After:
def ordered_list(props):
    depth = props["block"]["depth"]
    return DOM.create_element(
        "ol", {"class": f"list--depth-{depth}"}, props["children"]
    )
```

If you were relying on the configuration capabilities of the class API, switch to composing components instead:

```python
# Before:
class Link:
    def __init__(self, use_new_window=False):
        self.use_new_window = use_new_window

    def render(self, props):
        link_props = {"href": props["url"]}
        if self.use_new_window:
            link_props["target"] = "_blank"
            link_props["rel"] = "noreferrer noopener"
        return DOM.create_element("a", link_props, props["children"])

    # In the config:
    ENTITY_TYPES.LINK: Link(use_new_window=True)


# After:
def link(props):
    return DOM.create_element("a", props, props["children"])


def same_window_link(props):
    return DOM.create_element(
        link,
        {
            "href": props["url"],
        },
        props["children"],
    )


def new_window_link(props):
    return DOM.create_element(
        link,
        {
            "href": props["url"],
            "target": "_blank",
            "rel": "noreferrer noopener",
        },
        props["children"],
    )
```

Composite decorators also changed to a dict format with `strategy` and `component` keys, matching Draft.js:

```python
# Before:
class BR:
    SEARCH_RE = re.compile(r'\n')

    def render(self, props):
        if props['block']['type'] == BLOCK_TYPES.CODE:
            return props['children']
        return DOM.create_element('br')

'composite_decorators': [BR]

# After:
def br(props):
    if props['block']['type'] == BLOCK_TYPES.CODE:
        return props['children']
    return DOM.create_element('br')

'composite_decorators': [
    {'strategy': re.compile(r'\n'), 'component': br},
]
```

See the [Configuration reference](reference/configuration.md) for the current composite decorators format.

### Engine configuration

The `engine` field in the exporter config now requires a dotted-path string pointing to a valid engine, rather than a short name. Use the `DOM` class constants as shorthand:

```diff
  'engine': 'html5lib',
+ 'engine': DOM.HTML5LIB,
```

It is no longer possible to directly provide an engine class — use a dotted path instead:

```diff
  DOM.use(DOMTestImpl)
+ DOM.use('tests.test_dom.DOMTestImpl')
```

## Upgrading to v1.1.0

### String engine opt-in

This release adds a new string-based, dependency-free DOM engine. There is no need to make any changes to keep using the previous engines (`html5lib`, `lxml`). To switch to the new `string` engine, opt in via the config:

```diff
exporter = HTML({
+   'engine': 'string',
})
```

The new engine is faster than both `html5lib` and `lxml`, and outputs functionally identical HTML. Its only drawback is that `DOM.parse_html()` provides no safeguards against malformed or unescaped HTML, whereas `lxml` or `html5lib` sanitize the input. See [Alternative engines](guides/alternative-engines.md) for details.

## Upgrading to v0.9.0

### Composite decorators block type access

The block type for composite decorators has moved from `props['block_type']` to `props['block']['type']`:

```diff
- props['block_type']
+ props['block']['type']
```

### Removed DOM methods

The following DOM methods have been removed:

- `DOM.get_children()` — no longer available.
- `DOM.pretty_print()` — no longer available.

### ConfigException moved

`ConfigException` moved to `draftjs_exporter.error`:

```diff
- from draftjs_exporter.options import ConfigException
+ from draftjs_exporter.error import ConfigException
```

### `className` prop no longer auto-converted to `class`

The exporter no longer automatically converts a `className` prop to a `class` attribute. Use `class` directly:

```diff
- BLOCK_TYPES.BLOCKQUOTE: ['blockquote', {'className': 'c-pullquote'}]
+ BLOCK_TYPES.BLOCKQUOTE: ['blockquote', {'class': 'c-pullquote'}]
```

## Upgrading to v0.8.0

This release overhauled the block and style mapping format. Most declarations need updating.

### Block mapping format

Element-only block declarations can now use a plain string instead of a dict:

```diff
- BLOCK_TYPES.HEADER_TWO: {'element': 'h2'},
+ BLOCK_TYPES.HEADER_TWO: 'h2',
```

Array-style block declarations are replaced with the `element` / `props` format:

```diff
- BLOCK_TYPES.BLOCKQUOTE: ['blockquote', {'class': 'c-pullquote'}]
+ BLOCK_TYPES.BLOCKQUOTE: {'element': 'blockquote', 'props': {'class': 'c-pullquote'}}
```

Block wrapper declarations no longer use array syntax:

```diff
- 'wrapper': ['ul', {'class': 'bullet-list'}],
+ 'wrapper': 'ul',
+ 'wrapper_props': {'class': 'bullet-list'},
```

### Style mapping format

Style declarations follow the same format as block declarations:

```diff
- 'KBD': {'element': 'kbd'},
+ 'KBD': 'kbd',
```

```diff
- 'HIGHLIGHT': {'element': 'strong', 'textDecoration': 'underline'},
+ 'HIGHLIGHT': {'element': 'strong', 'props': {'style': {'textDecoration': 'underline'}}},
```

The default style map changed `STRIKETHROUGH` to the `s` tag and `UNDERLINE` to the `u` tag. To restore the previous behavior, define them explicitly:

```python
'STRIKETHROUGH': {'element': 'span', 'props': {'style': {'textDecoration': 'line-through'}}},
'UNDERLINE': {'element': 'span', 'props': {'style': {'textDecoration': 'underline'}}},
```

### Exception location

`BlockException` was renamed to `ConfigException` and moved:

```diff
- from draftjs_exporter.wrapper_state import BlockException
+ from draftjs_exporter.options import ConfigException
```

### `camel_to_dash` moved

```diff
- from draftjs_exporter.style_state import camel_to_dash
- camel_to_dash()
+ from draftjs_exporter.dom import DOM
+ DOM.camel_to_dash()
```

### Code block default rendering

Code blocks are now rendered inside both `pre` and `code` tags by default. To keep the previous behavior, use the new `PRE` block type:

```diff
- BLOCK_TYPES.CODE: 'pre',
+ BLOCK_TYPES.CODE: lambda props: DOM.create_element('pre', {}, DOM.create_element('code', {}, props['children'])),
+ BLOCK_TYPES.PRE: 'pre',
```

### Entity props

Entities now receive the content of their `data` dict directly as props, instead of the whole entity map:

```diff
  def render(self, props):
-     data = props.get('data', {})
      link_props = {
-         'href': data['url'],
+         'href': props['url'],
      }
```

### Removed DOM methods

The following DOM methods have been removed:

- `DOM.create_text_node(text)` — use the text string directly instead.
- `DOM.create_document_fragment()` — use `DOM.create_element()` instead.
- `DOM.get_text_content(elt)` — no longer available.
- `DOM.set_text_content(elt, text)` — no longer available.
