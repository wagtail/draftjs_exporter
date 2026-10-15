---
description: "Choose a draftjs_exporter DOM engine: string, string_compat, lxml or html5lib. Trade-offs in speed, dependencies, and output."
---

# Alternative engines

By default, the exporter uses a dependency-free engine called `string` to build the DOM tree. There are alternatives:

- `html5lib` (via BeautifulSoup)
- `lxml`.
- `string_compat` (A variant of `string` with no backwards-incompatible changes since its first release).

The `string` engine is the fastest, and does not have any dependencies. Its only drawback is that the `parse_html` method does not escape/sanitize HTML like that of other engines.

Engine output often differs in small ways. For example quote escaping in attributes, self-closing tags, and attribute name validation strictness exist between engines by design. If you switch engines on an existing site, expect some minor output differences, and re-check any code or tests that compare rendered HTML exactly. See [Troubleshooting](../troubleshooting.md#exporter-behavior) for the full list of engine-specific behaviors.

- For `html5lib`, do `pip install draftjs_exporter[html5lib]`.
- For `lxml`, do `pip install draftjs_exporter[lxml]`. It also requires `libxml2` and `libxslt` to be available on your system.
- There are no additional dependencies for `string_compat`.

Then, use the `engine` attribute of the exporter config. Built-in engines can be referenced by short name, or via the constants exposed by the `DOM` class:

```python
config = {
    "engine": "html5lib",
}

# Or, equivalently:
config = {
    "engine": DOM.HTML5LIB,
}
```

Replace `DOM.HTML5LIB` with `DOM.LXML` for the lxml engine, or `DOM.STRING_COMPAT` for the maximum-output-stability variant of the default `string` engine.

To use the `lxml` or `html5lib` engines with arbitrary versions of those dependencies, simply install `draftjs_exporter` without the extras, and separately install the desired versions of the dependencies.
