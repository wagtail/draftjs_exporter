# Project architecture

Understanding the high-level architecture will help you navigate the codebase and find where to make changes.

## Module organization

```ba
draftjs_exporter/
    html.py              # Entry point. HTML class orchestrates the full rendering pipeline.
    dom.py               # Virtual DOM abstraction. Static facade over interchangeable engines.
    command.py           # Command model – operations derived from Draft.js ranges.
    entity_state.py      # Entity (link, image, embed) rendering state machine.
    style_state.py       # Inline style (bold, italic) nesting state machine.
    wrapper_state.py     # Block wrapper nesting (e.g. <ul>/<ol> around <li>).
    options.py           # Configuration normalization – converts user config to internal format.
    composite_decorators.py  # Regex-based text decorators (line breaks, mentions, linkify).
    constants.py         # BLOCK_TYPES, ENTITY_TYPES, INLINE_STYLES enums.
    defaults.py          # Default BLOCK_MAP and STYLE_MAP for HTML.
    types.py             # Type aliases and TypedDicts for the public API.
    error.py             # Exception base classes.
    engines/
        base.py          # DOMEngine abstract base class.
        string.py        # String-concatenation engine (fast, no dependencies, default).
        string_compat.py # Backward-compatible variant of the string engine.
        html5lib.py      # BeautifulSoup / html5lib engine.
        lxml.py          # lxml engine.
        markdown.py      # Non-escaping string engine for Markdown output.
    markdown/            # Markdown-specific components, config builder, importer, and helpers.
        importer.py      # Markdown importer – parses Markdown into ContentState.
    utils/
        module_loading.py  # import_string() for dotted-path class resolution.
```

Tests mirror this structure under `tests/`, with sub-packages for `engines/`, `markdown/`, and `utils/`.

## Rendering pipeline

The core flow lives in `HTML.render()` and proceeds as follows:

1. **Engine setup** – `DOM.engine()` resolves the engine string to a class (via `import_string`), caches it, and sets it in a thread-safe `ContextVar`.
2. **Option normalization** – `Options.map_blocks()`, `Options.map_styles()`, `Options.map_entities()` convert the user-friendly config maps into flat `OptionsMap` dicts of type → normalized `Options` objects.
3. **Block iteration** – `HTML.render()` creates a `WrapperState` instance and an empty document fragment, then iterates over each block.
4. **Per-block rendering** – For each block, `render_block()` extracts text, inline styles, entity ranges, and composite decorators. It builds a sorted list of `Command` objects from the Draft.js ranges, groups consecutive commands by character offset, and processes each group through:
   - **EntityState** – manages an entity stack; on `start_entity`/`stop_entity` pairs it wraps children in entity components.
   - **StyleState** – tracks active inline styles; `start_segment()` keeps style elements open across text segments where styles continue (reducing redundant tags), while `render_styles()` wraps text in nested inline elements from innermost to outermost as a fallback for entity-active segments and callable component styles.
   - **Composite decorators** – regex-based text transformations (e.g. `\n` → `<br>`).
5. **Wrapper resolution** – `wrapper_state.element_for()` resolves each block to a DOM element, managing nesting of wrapper elements (e.g. `<ul>`/`<ol>` for list items) based on block depth.
6. **Final rendering** – All block elements are appended to the document fragment, then `DOM.render()` serialises the virtual DOM tree to the output string (HTML or Markdown).

## Importer pipeline

The reverse direction — Markdown → Draft.js ContentState — lives in `markdown/importer.py` and is exposed as `markdown_to_content_state(markdown, options=None)`. It is a dependency-free parser that does not reuse the export pipeline's `Command`/`EntityState`/`StyleState` abstractions (those consume ranges; the importer must _produce_ ranges from a different source representation).

The flow:

1. **Block splitting** – `_split_blocks()` splits Markdown into raw block strings, handling code fences, paragraph joining, and continuation lines.
2. **Block parsing** – `_parse_block()` dispatches each raw block to the right handler (heading, blockquote, list, code fence, HR, image, or unstyled fallback) via regex matching.
3. **Inline parsing** – `_InlineParser` walks block text character-by-character, tracking opening/closing of style markers, inline HTML tags, and link syntax. It produces plain text, `inlineStyleRanges`, `entityRanges`, and entity definitions.
4. **Style merging** – `_merge_style_ranges()` merges adjacent or overlapping ranges of the same style. This compensates for the exporter's inline style nesting behavior: when styles partially overlap (e.g. bold 0-5, italic 3-8), the exporter must close and reopen the outer marker to produce valid Markdown (`**Bold ****_Italic_**`), producing two BOLD ranges in the imported output that should be a single continuous range. This is an intentional round-trip trade-off, coupling the importer to the exporter's marker-emission quirks.

The importer accepts `MarkdownImporterOptions` with the three inline style markers (`bold`, `italic`, `strikethrough`) and a custom `html_style_tags` mapping. Block-level syntax (list markers, horizontal rule variants, code fence variants) is recognized polymorphically rather than configured – the importer accepts any valid variant the exporter might produce. See [Markdown support](../markdown.md#importer) for the user-facing options reference.

## Engine system

The exporter uses a **Strategy pattern** for output generation. All engines implement the `DOMEngine` interface (five static methods: `create_tag`, `parse_html`, `append_child`, `render`, `render_debug`). The `DOM` class delegates to the active engine, selected at runtime via dotted-path strings stored as class constants (`DOM.STRING`, `DOM.HTML5LIB`, `DOM.LXML`, `DOM.MARKDOWN`, `DOM.STRING_COMPAT`). Engine selection is thread-safe through a `ContextVar`.

Engines share the same interface and general behavior, but **are not guaranteed to produce byte-identical output** for the same input. Each engine delegates serialization to a different underlying library (or none, for `string`), so real, accepted differences exist.

## Key design patterns

- **Strategy** – swappable engines, selected at runtime.
- **Facade** – `DOM` class hides engine-specific details.
- **State machine** – `EntityState` tracks entity open/close via a stack.
- **Command pattern** – operations on text are modeled as `Command` objects, sorted, grouped, and applied in order.
- **Pipeline** – text passes through decorators → inline styles → entity wrapping → wrapper nesting, each stage wrapping the previous.
- **Null object** – `WrapperStack.head()` returns a default `Wrapper(-1)` when the stack is empty.
- **Slots for performance** – core classes use `__slots__` to reduce memory overhead.
