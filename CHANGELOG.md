# Changelog

> All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v7.0.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v7.0.0)

### Added

- Add experimental [Markdown importer](https://wagtail.github.io/draftjs_exporter/markdown-importer/): `MarkdownImporter` converts Markdown to Draft.js ContentState, with configurable entity resolvers (`scheme_resolver` for internal URL schemes), an inline HTML style whitelist, and `ContentStateFilter` for content policy.

### Changed

- The Markdown export now escapes all content. See [Markdown escaping](https://wagtail.github.io/draftjs_exporter/markdown/#escaping).

## [v6.0.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v6.0.0)

### Added

- Add experimental Markdown export via `DOM.MARKDOWN`, with `MARKDOWN_CONFIG` and `build_markdown_config()`.
- Re-export the public API from the `draftjs_exporter` package root (`Exporter`, `HTML_CONFIG`, types, constants).
- Improve static type annotations with `TypedDict` definitions for configuration and ContentState.
- Add [new documentation website](https://wagtail.github.io/ draftjs_exporter/) with docs for getting started, Markdown export, custom components, and more.
- Add threat model and security guidance in [`SECURITY.md`](https://wagtail.github.io/draftjs_exporter/SECURITY/).

### Changed

- Raise the lower bound of the optional `lxml` dependency to `>=4.6.5`.
- Performance improvements when exporting content.
- Move the repository to `wagtail/draftjs_exporter` (same maintainers, new home).
- Reduce redundant tags in nested and partially nested inline style output, producing semantically equivalent but cleaner HTML ([#136](https://github.com/wagtail/draftjs_exporter/issues/136)). See [troubleshooting](https://wagtail.github.io/draftjs_exporter/troubleshooting/) for details.

### Removed

- Remove support for Python 3.7, 3.8, 3.9.

### Fixed

- Fix concurrency bug where the DOM engine was shared globally across all `HTML` instances. Each exporter now uses its own engine via a context variable ([#122](https://github.com/wagtail/draftjs_exporter/issues/122)).
- Fix crash when rendering blocks that start at a nested depth without a preceding depth-0 block, when the wrapper element is a callable component (e.g. Markdown list items).

For breaking changes and upgrade steps, see the [migration guide](https://wagtail.github.io/draftjs_exporter/migration-guide/).

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

For breaking changes and upgrade steps, see the [migration guide](https://wagtail.github.io/draftjs_exporter/migration-guide/).

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

This release contains breaking changes. **Be sure to check out the [migration guide](https://wagtail.github.io/draftjs_exporter/migration-guide/).**

### Removed

- Remove support for Python 3.5 ([#129](https://github.com/wagtail/draftjs_exporter/pull/129))
- Remove HTML attributes alphabetical sorting of default string engine ([#129](https://github.com/wagtail/draftjs_exporter/pull/129))
- Disable single and double quotes escaping outside of attributes for string engine ([#129](https://github.com/wagtail/draftjs_exporter/pull/129))
- Stop sorting inline styles alphabetically ([#129](https://github.com/wagtail/draftjs_exporter/pull/129))

## [v3.0.1](https://github.com/wagtail/draftjs_exporter/releases/tag/v3.0.1)

### Added

- Add `Typing :: Typed` trove classifier to the package.

### Changed

- Small performance improvements (1.5x faster) for blocks that do not have inline styles, and configurations that only use `\n -> <br/>` composite decorators. ([#127](https://github.com/wagtail/draftjs_exporter/pull/127))

## [v3.0.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v3.0.0)

This release contains breaking changes. **Be sure to check out the [migration guide](https://wagtail.github.io/draftjs_exporter/migration-guide/).**

### Changed

- Remove support for Python 2.7 and 3.4 ([#111](https://github.com/wagtail/draftjs_exporter/issues/111), [#120](https://github.com/wagtail/draftjs_exporter/pull/120)).
- Add support for Python 3.8.
- Small performance improvements by using lists’ mutable `.sort()` instead of `sorted()`, which is a bit faster. (±2% faster) ([#120](https://github.com/wagtail/draftjs_exporter/pull/120)).

### Added

- Add [PEP-484](https://www.python.org/dev/peps/pep-0484/) type annotations for the project’s public APIs ([#101](https://github.com/wagtail/draftjs_exporter/issues/101), [#123](https://github.com/wagtail/draftjs_exporter/pull/123)).
- Add [PEP-561](https://www.python.org/dev/peps/pep-0561/) metadata so the exporter’s type annotations can be read by type checkers ([#101](https://github.com/wagtail/draftjs_exporter/issues/101), [#123](https://github.com/wagtail/draftjs_exporter/pull/123)).
- Give entity rendering components access to the current `block`, `blocks` list, `mutability`, and key as `entity_range.key` ([#91](https://github.com/wagtail/draftjs_exporter/issues/91), [#124](https://github.com/wagtail/draftjs_exporter/pull/124)).

For breaking changes and upgrade steps, see the [migration guide](https://wagtail.github.io/draftjs_exporter/migration-guide/).

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

This release contains breaking changes that will require updating the exporter's configurations. **Be sure to check out the [migration guide](https://wagtail.github.io/draftjs_exporter/migration-guide/).**

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

## [v1.1.1](https://github.com/wagtail/draftjs_exporter/releases/tag/v1.1.1)

### Fixed

- Fix string engine incorrectly skipping identical elements at the same depth level ([#83](https://github.com/wagtail/draftjs_exporter/pull/83)).

## [v1.1.0](https://github.com/wagtail/draftjs_exporter/releases/tag/v1.1.0)

### Added

- Add new string-based dependency-free DOM backing engine, with much better performance, thanks to the expertise of @BertrandBordage (#77).

### Changed

- Pre-compile regexes in html5lib engine for performance improvements (#76).

For breaking changes and upgrade steps, see the [migration guide](https://wagtail.github.io/draftjs_exporter/migration-guide/).

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

For breaking changes and upgrade steps, see the [migration guide](https://wagtail.github.io/draftjs_exporter/migration-guide/).

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

For breaking changes and upgrade steps, see the [migration guide](https://wagtail.github.io/draftjs_exporter/migration-guide/).

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

For breaking changes and upgrade steps, see the [migration guide](https://wagtail.github.io/draftjs_exporter/migration-guide/).
