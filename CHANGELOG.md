# Changelog

> All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v6.0.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v6.0.0)

### Added

- Add experimental Markdown export via `DOM.MARKDOWN`, with `MARKDOWN_CONFIG` and `build_markdown_config()`.
- Re-export the public API from the `draftjs_exporter` package root (`Exporter`, `HTML_CONFIG`, types, constants).
- Improve static type annotations with `TypedDict` definitions for configuration and ContentState.

### Changed

- Raise the lower bound of the optional `lxml` dependency to `>=4.6.5`.
- Performance improvements when exporting content.
- Move the repository to `wagtail/draftjs_exporter` (same maintainers, new home).
- Reduce redundant tags in nested and partially nested inline style output, producing semantically equivalent but cleaner HTML ([#136](https://github.com/wagtail/draftjs_exporter/issues/136)).

### Removed

- Remove support for Python 3.7, 3.8, 3.9.

### Fixed

- Fix concurrency bug where the DOM engine was shared globally across all `HTML` instances. Each exporter now uses its own engine via a context variable ([#122](https://github.com/wagtail/draftjs_exporter/issues/122)).

## [v5.2.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v5.2.0)

### Added

- Formalize support for Python 3.14, with tentative support for Python 3.15.
- Add support for lxml v6 with the `draftjs_exporter[lxml]` extra.

## [v5.1.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v5.1.0)

### Added

- Formalize support for Python 3.12 and 3.13, with tentative support for Python 3.14.
- Add support for lxml v5 with the `draftjs_exporter[lxml]` extra.

## [v5.0.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v5.0.0)

### Added

- Add tentative support for Python 3.11.
- Add new "string_compat" engine for maximum output stability, with identical output to its first release. To use it, set the `engine` property to `'engine': DOM.STRING_COMPAT,` ([#138](https://github.com/wagtail/draftjs_exporter/pull/138)).

### Removed

- Remove support for Python 3.6.

### How to upgrade

#### Python 3.6 support

Python 3.6 is no longer supported, as it has reached its [end of life](https://www.python.org/dev/peps/pep-0494/). For projects needing Python 3.6, please keep using [v4.1.2](https://github.com/wagtail/draftjs_exporter/tree/v4.1.2) of the exporter.

## [v4.1.2](https://github.com/wagtail/draftjs_exporter/releases/tag/v4.1.2)

### Changed

- Add tentative support for Python 3.10.
- Stop using `extras_require` for development-only dependencies.

## [v4.1.1](https://github.com/wagtail/draftjs_exporter/releases/tag/v4.1.1)

### Changed

- Add support for Python 3.9 ([#134](https://github.com/wagtail/draftjs_exporter/pull/134)).
- Update html5lib upper bound, now defined as `html5lib>=0.999,<2`, to ensure compatibility with Python 3.10 ([#134](https://github.com/wagtail/draftjs_exporter/pull/134)).

## [v4.1.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v4.1.0)

### Added

- Publish the package as a wheel ([#132](https://github.com/wagtail/draftjs_exporter/issues/132), [#133](https://github.com/wagtail/draftjs_exporter/pull/133)). Thanks to [Stormheg](https://github.com/Stormheg).

## [v4.0.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v4.0.0)

This release contains breaking changes. **Be sure to check out the "how to upgrade" section below.**

### Removed

- Remove support for Python 3.5 ([#129](https://github.com/wagtail/draftjs_exporter/pull/129))
- Remove HTML attributes alphabetical sorting of default string engine ([#129](https://github.com/wagtail/draftjs_exporter/pull/129))
- Disable single and double quotes escaping outside of attributes for string engine ([#129](https://github.com/wagtail/draftjs_exporter/pull/129))
- Stop sorting inline styles alphabetically ([#129](https://github.com/wagtail/draftjs_exporter/pull/129))

### How to upgrade

#### Python 3.5 support

Do not upgrade to this version if you are using the exporter in Python 3.5. Please keep using [v3.0.1](https://github.com/wagtail/draftjs_exporter/tree/v3.0.1) of the exporter.

#### HTML attributes sorting

The default `string` engine no longer sorts attributes alphabetically by name in its output HTML. This makes it possible to control the order as needed, wherever attributes can be specified:

```python
def image(props):
    return DOM.create_element('img', {
        'src': props.get('src'),
        'width': props.get('width'),
        'height': props.get('height'),
        'alt': props.get('alt'),
    })
```

If you relied on this behavior, you can either reorder your `props` / `wrapper_props` / `create_element` calls as needed, or subclass the built-in `string` engine and override its `render_attrs` method to add back the `attrs.sort`:

```python
    @staticmethod
    def render_attrs(attr: Attr) -> str:
        attrs = [f' {k}="{escape(v)}"' for k, v in attr.items()]
        attrs.sort()
        return "".join(attrs)
```

### HTML quotes escaping

The default `string` engine no longer escapes single and double quotes in HTML content (it still escapes quotes inside attributes). If you relied on this behavior, subclass the built-in `string` engine and override its `render_children` method to add back `quote=True`:

```python
    @staticmethod
    def render_children(children: Sequence[Union[HTML, Elt]]) -> HTML:
        return "".join(
            [
                DOMString.render(c)
                if isinstance(c, Elt)
                else escape(c, quote=True)
                for c in children
            ]
        )
```

### Inline styles sorting

The exporter supports passing the `style` attribute as a dictionary with JS attributes for style properties, and will automatically convert it to a string. The properties are no longer sorted alphabetically – it’s now possible to reorder the dictionary’s keys to change the order.

If you relied on this behavior, either reorder the keys as needed, or pass the `style` as a string (with CSS properties syntax).

## [v3.0.1](https://github.com/wagtail/draftjs_exporter/releases/tag/v3.0.1)

### Added

- Add `Typing :: Typed` trove classifier to the package.

### Changed

- Small performance improvements (1.5x faster) for blocks that do not have inline styles, and configurations that only use `\n -> <br/>` composite decorators. ([#127](https://github.com/wagtail/draftjs_exporter/pull/127))

## [v3.0.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v3.0.0)

This release contains breaking changes. **Be sure to check out the "how to upgrade" section below.**

### Changed

- Remove support for Python 2.7 and 3.4 ([#111](https://github.com/wagtail/draftjs_exporter/issues/111), [#120](https://github.com/wagtail/draftjs_exporter/pull/120)).
- Add support for Python 3.8.
- Small performance improvements by using lists’ mutable `.sort()` instead of `sorted()`, which is a bit faster. (±2% faster) ([#120](https://github.com/wagtail/draftjs_exporter/pull/120)).

### Added

- Add [PEP-484](https://www.python.org/dev/peps/pep-0484/) type annotations for the project’s public APIs ([#101](https://github.com/wagtail/draftjs_exporter/issues/101), [#123](https://github.com/wagtail/draftjs_exporter/pull/123)).
- Add [PEP-561](https://www.python.org/dev/peps/pep-0561/) metadata so the exporter’s type annotations can be read by type checkers ([#101](https://github.com/wagtail/draftjs_exporter/issues/101), [#123](https://github.com/wagtail/draftjs_exporter/pull/123)).
- Give entity rendering components access to the current `block`, `blocks` list, `mutability`, and key as `entity_range.key` ([#91](https://github.com/wagtail/draftjs_exporter/issues/91), [#124](https://github.com/wagtail/draftjs_exporter/pull/124)).

### How to upgrade

#### Python 2.7 and 3.4 support

Do not upgrade to this version if you are using the exporter in Python 2.7 or 3.4. Please keep using [v2.1.7](https://github.com/wagtail/draftjs_exporter/tree/v2.1.7) of the exporter.

#### PEP-484 type annotations

If you are using the exporter in a codebase using type annotations and a type checker, there is a chance the annotations added in this release will create conflicts with your project’s annotations – if there are discrepancies between the expected input/output of the exporter, or in the configuration. In this case you may need to update your project’s type annotations or stubs to match the expected types of the exporter’s public API.

If you believe there is a problem with how the public API is typed, please [open a new issue](https://github.com/wagtail/draftjs_exporter/issues/new/choose).

## [v2.1.7](https://github.com/wagtail/draftjs_exporter/releases/tag/v2.1.7)

### Changed

- Minor performance improvements (10% speed-up, 30% lower memory consumption) by adding Python [`__slots__`](https://stackoverflow.com/questions/472000/usage-of-slots) and implementing other optimisations.

## [v2.1.6](https://github.com/wagtail/draftjs_exporter/releases/tag/v2.1.6)

### Changed

- Assume same block defaults as Draft.js would when attributes are missing: depth = 0, type = unstyled, no entities, no styles ([#110](https://github.com/wagtail/draftjs_exporter/pull/110), thanks to [@tpict](https://github.com/tpict)).
- Minor performance improvements for text-only blocks ([#112](https://github.com/wagtail/draftjs_exporter/pull/112)).

## [v2.1.5](https://github.com/wagtail/draftjs_exporter/releases/tag/v2.1.5)

### Changed

- Minor performance improvements (8% speed-up, 20% lower memory consumption) ([#108](https://github.com/wagtail/draftjs_exporter/pull/108))

### Fixed

- Fix export bug with adjacent entities - the exporter moved their contents outside of the entities' markup ([#106](https://github.com/wagtail/draftjs_exporter/pull/106), [#107](https://github.com/wagtail/draftjs_exporter/pull/107)). Thanks to [@ericpai](https://github.com/ericpai) for reporting this.

## [v2.1.4](https://github.com/wagtail/draftjs_exporter/releases/tag/v2.1.4)

### Changed

- Attempt to fix project description formatting on [PyPI](https://pypi.org/project/draftjs_exporter/), broken in the last release ([#103](https://github.com/wagtail/draftjs_exporter/issues/103)).

## [v2.1.3](https://github.com/wagtail/draftjs_exporter/releases/tag/v2.1.3)

### Changed

- Increase lower bound of optional lxml dependency to v4.2.0 to guarantee Python 3.7 support ([#88](https://github.com/wagtail/draftjs_exporter/pull/88)).

## [v2.1.2](https://github.com/wagtail/draftjs_exporter/releases/tag/v2.1.2)

### Changed

- Use io.open with utf-8 encoding in setup.py. Fix [#98](https://github.com/wagtail/draftjs_exporter/issues/98) ([#99](https://github.com/wagtail/draftjs_exporter/pull/99))

## [v2.1.1](https://github.com/wagtail/draftjs_exporter/releases/tag/v2.1.1)

### Changed

- Add upper bound to lxml dependency, now defined as `lxml>=3.6.0,<5` ([#75](https://github.com/wagtail/draftjs_exporter/issues/75)).
- Update html5lib upper bound, now defined as `html5lib>=0.999,<=1.0.1`.

## [v2.1.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v2.1.0)

### Added

- Give block rendering components access to the current `block`, when the component is rendered for a block, and the `blocks` list ([#90](https://github.com/wagtail/draftjs_exporter/pull/90)).
- Give text decorators renderers access to the current `block` and `blocks` list ([#90](https://github.com/wagtail/draftjs_exporter/pull/90)).
- Give style rendering components access to the current `block`, `blocks` list, and current style type as `inline_style_range.style` ([#87](https://github.com/wagtail/draftjs_exporter/issues/87), [#90](https://github.com/wagtail/draftjs_exporter/pull/90)).

### Changed

- Performance improvements for text-only (no inline styles, no entities) blocks ([#89](https://github.com/wagtail/draftjs_exporter/pull/89)).

## [v2.0.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v2.0.0)

This release contains breaking changes that will require updating the exporter's configurations. **Be sure to check out the "how to upgrade" section below.**

### Changed

- Change default DOM engine to `DOMString` ([#79](https://github.com/wagtail/draftjs_exporter/issues/79), [#85](https://github.com/wagtail/draftjs_exporter/pull/85)).
- Add extra install for html5lib ([#79](https://github.com/wagtail/draftjs_exporter/issues/79), [#85](https://github.com/wagtail/draftjs_exporter/pull/85)).
- Remove support for class-based decorators ([#73](https://github.com/wagtail/draftjs_exporter/issues/73), [#84](https://github.com/wagtail/draftjs_exporter/pull/84)).
- Switch composite decorators to dict format like that of Draft.js, with `strategy` and `component` attributes.
- Use dotted-path loading for custom engines ([#64](https://github.com/wagtail/draftjs_exporter/issues/64), [#81](https://github.com/wagtail/draftjs_exporter/pull/81)).
- Use dotted-path loading for built-in engines.
- Raise `ImportError` when loading an engine fails, not `ConfigException`.

### Removed

- Calls to `DOM.use` must use a valid engine, there is no default value anymore.
- Stop supporting passing an engine class directly in the `engine` option, or to `DOM.use`.
- Stop including tests in published package.

### Fixed

- Stop loading html5lib engine on every use, even if unused ([#80](https://github.com/wagtail/draftjs_exporter/issues/80)).

### How to upgrade

#### New default engine

The specificities of the new engine are described in the [documentation](https://github.com/wagtail/draftjs_exporter#alternative-backing-engines). To start using the new default,

1. Remove the `engine` property from the exporter configuration, or do `'engine': DOM.STRING,`.
2. You can also remove the `html5lib` and `beautifulsoup4` dependencies from your project if they aren't used anywhere else.

To keep using the previous default, html5lib:

1. Set the `engine` property to `'engine': DOM.HTML5LIB,`.
2. Make sure you install the exporter with `pip install draftjs_exporter[html5lib]`.

#### Decorator component definitions

Decorator components now require the function syntax (see the relevant [documentation](https://github.com/wagtail/draftjs_exporter#custom-components)).

```python
# Before:
class OrderedList:
    def render(self, props):
        depth = props['block']['depth']

        return DOM.create_element('ol', {
            'class': f'list--depth-{depth}'
        }, props['children'])
# After:
def ordered_list(props):
    depth = props['block']['depth']

    return DOM.create_element('ol', {
        'class': f'list--depth-{depth}'
    }, props['children'])
```

If you were relying on the configuration capabilities of the class API, switch to composing components instead:

```python
# Before:
class Link:
    def __init__(self, use_new_window=False):
        self.use_new_window = use_new_window

    def render(self, props):
        link_props = {
            'href': props['url'],
        }

        if self.use_new_window:
            link_props['target'] = '_blank'
            link_props['rel'] = 'noreferrer noopener'

        return DOM.create_element('a', link_props, props['children'])

# In the config:
    ENTITY_TYPES.LINK: Link(use_new_window=True)

# After:
def link(props):
    return DOM.create_element('a', props, props['children'])

def same_window_link(props):
    return DOM.create_element(link, {
        'href': props['url'],
    }, props['children'])
})

def new_window_link(props):
    return DOM.create_element(link, {
        'href': props['url'],
        'target': '_blank',
        'rel': 'noreferrer noopener',
    }, props['children'])
})
```

The composite decorators API now looks closer to that of other decorators, and to Draft.js:

```python
# Before:
class BR:
    SEARCH_RE = re.compile(r'\n')

    def render(self, props):
        if props['block']['type'] == BLOCK_TYPES.CODE:
            return props['children']

        return DOM.create_element('br')


'composite_decorators': [
    BR,
]
# After:

def br(props):
    if props['block']['type'] == BLOCK_TYPES.CODE:
        return props['children']

    return DOM.create_element('br')

# In the config:
'composite_decorators': [
    {
        'strategy': re.compile(r'\n'),
        'component': br,
    },
],
```

#### Engine configuration

```diff
# The `engine` field in the exporter config now has to be a dotted path string pointing to a valid engine.
- 'engine': 'html5lib',
+ 'engine': 'draftjs_exporter.engines.html5lib.DOM_HTML5LIB',
# Or, using the shorthand.
+ 'engine': DOM.HTML5LIB,

# It's not possible either to directly provide an engine implementation - use a dotted path instead.
- DOM.use(DOMTestImpl)
+ DOM.use('tests.test_dom.DOMTestImpl')
```

## [v1.1.1](https://github.com/wagtail/draftjs_exporter/releases/tag/v1.1.1)

### Fixed

- Fix string engine incorrectly skipping identical elements at the same depth level ([#83](https://github.com/wagtail/draftjs_exporter/pull/83)).

## [v1.1.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v1.1.0)

### Added

- Add new string-based dependency-free DOM backing engine, with much better performance, thanks to the expertise of @BertrandBordage (#77).

### Changed

- Pre-compile regexes in html5lib engine for performance improvements (#76).

### How to upgrade

There is no need to make any changes to keep using the previous engines (html5lib, lxml). To switch to the new string engine, opt-in via the config:

```diff
exporter = HTML({
+    # Specify which DOM backing engine to use.
+    'engine': 'string',
})
```

The new engine is faster than both `html5lib` and `lxml`, and outputs a functionally identical HTML (see a list of all known engine differences at [`test_engine_differences.py`](https://github.com/wagtail/draftjs_exporter/blob/main/tests/engines/test_engines_differences.py)). Its only drawback is that when using the `DOM.parse_html()` no safeguards are provided against malformed or unescaped HTML, whereas lxml or html5lib sanitise the input.

## [v1.0.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v1.0.0)

> This release is functionally identical to the previous one, `v0.9.0`.

The project has reached a high-enough level of stability to be used in production, and breaking changes will now be reflected via major version changes.

## [v0.9.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.9.0)

### Added

- Add configuration options to determine handling of missing blocks #52.
- Add configuration options to determine handling of missing styles.
- Add configuration options to determine handling of missing entities.
- Block components now have access to the block type via `props['block']['type']`.
- Entity components now have access to the entity type via `props['entity']['type']`.
- Composite decorators now have access to the current block depth and data via `props['block']['depth']`, `props['block']['data']`.
- Allow discarding component children by returning `None` in `render`.
- Add support for `lxml` as a DOM backing engine, with `pip install draftjs_exporter[lxml]` pip extra.
- Add support for custom DOM backing engines.
- Add support for None content state in HTML.render #67.

### Changed

- For composite decorators, the block type has moved from `props['block_type']` to `props['block']['type']`.
- Move `ConfigException` to `draftjs_exporter.error`.

### Removed

- Remove `DOM.get_children` method.
- Remove `DOM.pretty_print` method.
- Remove automatic conversion from `className` prop to `class`.

### Fixed

- Stop rendering decorators when there is no text to decorate.
- Remove extra HTML serialisation steps.

### How to upgrade

```diff
# Change composite decorators block type access
- props['block_type']
+ props['block']['type']
# Stop using DOM.get_children directly.
- DOM.get_children()
# Stop using DOM.pretty_print directly.
- DOM.pretty_print()
# Move `ConfigException` to `draftjs_exporter.error`.
- from draftjs_exporter.options import ConfigException
+ from draftjs_exporter.error import ConfigException
# Remove automatic conversion from `className` prop to `class` attribute.
- BLOCK_TYPES.BLOCKQUOTE: ['blockquote', {'className': 'c-pullquote'}]
+ BLOCK_TYPES.BLOCKQUOTE: ['blockquote', {'class': 'c-pullquote'}]
```

## [v0.8.1](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.8.1)

### Fixed

- Fix KeyError when the content state is empty.

## [v0.8.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.8.0)

### Added

- Add simplified block mapping format: `BLOCK_TYPES.HEADER_TWO: 'h2'`.
- Raise exception when `style_map` does not define an `element` for the style.
- Add support for any props on `style_map`.
- Automatically convert `style` prop from a dict of camelCase properties to a string, on all elements (if `style` is already a string, it will be output as is).
- Support components (`render` function returning `create_element` nodes) in `style_map`.
- Add more defaults in the style map:

```python
BOLD = 'strong'
CODE = 'code'
ITALIC = 'em'
UNDERLINE = 'u'
STRIKETHROUGH = 's'
SUPERSCRIPT = 'sup'
SUBSCRIPT = 'sub'
MARK = 'mark'
QUOTATION = 'q'
SMALL = 'small'
SAMPLE = 'samp'
INSERT = 'ins'
DELETE = 'del'
KEYBOARD = 'kbd'
```

- Add new `pre` block type.
- Support components (`render` function returning `create_element` nodes) in `block_map`, for both `element` and `wrapper`.

### Removed

- Remove array-style block element and wrapper declarations (`['ul']`, `['ul', {'class': 'bullet-list'}]`).
- Remove `DOM.create_text_node` method.

### Changed

- Replace array-style mapping declarations of block element and wrapper props with `props` and `wrapper_props` attributes (dictionaries of props).
- Moved and renamed `BlockException` to `ConfigException`.
- Replace `style_map` config format to the one of the `block_map`.
- Move internal `camel_to_dash` method to `DOM` for official use.
- Change ordering of inline styles - now using alphabetical ordering of style key instead of tag name.
- `STRIKETHROUGH` styles in default style map now map to `s` tag.
- `UNDERLINE` styles in default style map now map to `u` tag.
- By default, `code-block` blocks are now rendered inside a combination of `pre` and `code` tags.
- For entities, directly pass `data` dict as props instead of whole entity map declaration.

### Fixed

- Fix block ordering with block components and wrapper. Fix #55.

### How to upgrade

```diff
# Change element-only block declarations:
- BLOCK_TYPES.HEADER_TWO: {'element': 'h2'},
+ BLOCK_TYPES.HEADER_TWO: 'h2',
# Change array-style block declarations:
- BLOCK_TYPES.BLOCKQUOTE: ['blockquote', {'class': 'c-pullquote'}]
+ BLOCK_TYPES.BLOCKQUOTE: {'element': 'blockquote', 'props': {'class': 'c-pullquote'}}
# Change block wrapper declarations:
- 'wrapper': ['ul', {'class': 'bullet-list'}],
+ 'wrapper': 'ul',
+ 'wrapper_props': {'class': 'bullet-list'},
# Change location and name of exceptions:
- from draftjs_exporter.wrapper_state import BlockException
+ from draftjs_exporter.options import ConfigException
# Change element-only style declarations:
- 'KBD': {'element': 'kbd'},
+ 'KBD': 'kbd',
# Change object-style style declarations:
- 'HIGHLIGHT': {'element': 'strong', 'textDecoration': 'underline'},
+ 'HIGHLIGHT': {'element': 'strong', 'props': {'style': {'textDecoration': 'underline'}}},
# Create custom STRIKETHROUGH styles:
+ 'STRIKETHROUGH': {'element': 'span', 'props': {'style': {'textDecoration': 'line-through'}}},
# Create custom UNDERLINE styles:
+ 'UNDERLINE': {'element': 'span', 'props': {'style': {'textDecoration': 'underline'}}},
# New camel_to_dash location:
- from draftjs_exporter.style_state import camel_to_dash
- camel_to_dash()
+ from draftjs_exporter.dom import DOM
+ DOM.camel_to_dash()
# New default rendering for code-block:
- BLOCK_TYPES.CODE: 'pre',
+ BLOCK_TYPES.CODE: lambda props: DOM.create_element('pre', {}, DOM.create_element('code', {}, props['children'])),
# Use the new pre block to produce the previous result, or override the default for code-block.
+ BLOCK_TYPES.PRE: 'pre',
# Entities now receive the content of `data` directly, instead of the whole entity:
  def render(self, props):
-     data = props.get('data', {})
      link_props = {
-         'href': data['url'],
+         'href': props['url'],
      }
# Remove wrapping around text items.
- DOM.create_text_node(text)
+ text
# Remove fragment calls.
- DOM.create_document_fragment()
+ DOM.create_element()
# Remove text getters and setters. This is not supported anymore.
- DOM.get_text_content(elt)
- DOM.set_text_content(elt, text)
```

## [v0.7.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.7.0)

### Added

- Add support for decorators thanks to [@su27](https://github.com/su27) (#16, #17).
- Add support for configurable decorators and entities.
- Add support for decorators and entities in function form.

### Changed

- Stop lowercasing HTML attributes. `*ngFor` will now be exported as `*ngFor`.

### Removed

- Drop Python 3.3 support (likely still runs fine, but tests are not ran on it).

## [v0.6.2](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.6.2)

### Added

- Add profiling tooling thanks to [@su27](https://github.com/su27) (#31).
- Add more common entity types in constants (#34).

### Fixed

- Stop mutating entity data when rendering entities (#36).

## [v0.6.1](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.6.1)

### Added

- Automatically convert line breaks to `br` elements.

## [v0.6.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.6.0)

This release is likely to be a **breaking change**. It is not released as such because the exporter has not [reached 1.0 yet](http://semver.org/#spec-item-4).

### Changed

- Change `hr` rendering to be done with entities instead of block types. Instead of having a `TOKEN` entity rendering as `Null` inside a `horizontal-rule` block rendering as `hr`, we now have a `HORIZONTAL_RULE` entitiy rendering as `HR` inside an `atomic` block rendering as `fragment`.

### Removed

- Remove custom block type `pullquote`

## [v0.5.2](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.5.2)

### Fixed

- Fix state being kept between exports, causing blocks to be duplicated in re-runs.

## [v0.5.1](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.5.1)

### Fixed

- Fix broken link in README

## [v0.5.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.5.0)

This release is likely to be a **breaking change**. It is not released as such because the exporter has not [reached 1.0 yet](http://semver.org/#spec-item-4).

### Added

- Add support for more scenarios with nested blocks. Jumping depths eg. 0, 2, 3. Starting directly above 0 eg. 2, 2, 0. Not using 0 at all eg. 3, 3, 3.

### Changed

- Entity decorators now have complete control on where their content (markup, not just text) is inserted into the DOM. This is done via the `children` prop in a similar fashion to React's.

### Removed

- Built-in entities are no longer available as part of the library. They should be defined in userland.

## [v0.4.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.4.0)

This release is likely to be a **breaking change**. It is not released as such because the exporter has not [reached 1.0 yet](http://semver.org/#spec-item-4).

### Changed

- Now using [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) and the [html5lib](https://github.com/html5lib/html5lib-python) parser instead of lxml.
- Entities are now available from `draftjs_exporter.entities` instead of `draftjs_exporter.entities.<entity>`

### Added

- Support for simpler `wrapper` options definition: `{'unordered-list-item' : { 'element': 'li', 'wrapper': 'ul'}}`
- Support for options definition for every element, not just wrappers: `{'header-two' : { 'element': ['h2', {'class': 'c-amazing-heading'}]}}`
- Support for None in the children of an element in `DOM.create_element`, for conditional rendering like what React does.
- Support for entity class in `DOM.create_element`.

### Fixed

- Fix behavior of wrapper stack in nested wrappers ([#15](https://github.com/wagtail/draftjs_exporter/issues/15))

## [v0.3.3](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.3.3)

Last release before switching to BeautifulSoup4 / html5lib. If we ever need to switch back to lxml, it should be as simple as looking at the code at [v0.3.3](https://github.com/wagtail/draftjs_exporter/tree/v0.3.3).

### Added

- Add wrapper method to create new elements.
- Add wrapper method to retrieve an element's list of classes.

## [v0.3.2](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.3.2)

### Fixed

- Fix exporter crashing on empty blocks (renders empty string instead)

## [v0.3.1](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.3.1)

### Fixed

- Use HTML parser instead of XML for DOM API

## [v0.3.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.3.0)

### Added

- Automatic conversion of entity data to HTML attributes (int & boolean to string, `class` to `class`).
- Default, extensible block & inline style maps for common HTML elements.
- React-like API to create custom entity decorators.
- DOM API to abstract HTML building code.
- Dynamically generate test cases from JSON fixture
- Raise exception for undefined entity decorators

### Changed

- (Breaking change) Exporter API changed to be closer to React's
- (Breaking change) Entity decorator API changed to be closer to React's

### Fixed

- Nested blocks backtracking creating multiple wrappers at the same depths instead of reusing existing ones ([#9](https://github.com/wagtail/draftjs_exporter/issues/9))

### Removed

- Removed Token entity (identical as Null)

## [v0.2.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.2.0)

### Added

- Support for `<hr/>` tag / `TOKEN` entities
- Support for wrapped item nesting (arbitrary depth)

## [v0.1.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v0.1.0)

First usable release!

---

## [vx.y.z](https://github.com/wagtail/draftjs_exporter/releases/tag/x.y.z) (Template: http://keepachangelog.com/)

### Added

- Something was added to the API / a new feature was introduced.

### Changed

### Fixed

### Removed

### How to upgrade
