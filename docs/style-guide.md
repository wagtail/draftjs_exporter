# Documentation style guide

This style guide defines the standard we aim for across the draftjs_exporter documentation – the README, MkDocs site, contributor docs, and docstrings. Use it as the default for all new content, and as a reference when revising existing pages.

The guide is derived from how the project's documentation has historically been written. When this guide and an existing page disagree, prefer the guide and consider updating the page.

## Design goals

- **Accurate, discoverable, maintainable.** Docs should describe the code as it is, be easy to find, and be cheap to keep up to date.
- **Concise and practical.** Get to the point quickly. Prefer working code examples over long prose explanations. Every page should help the reader accomplish something or understand a concept they need.
- **Two tracks, one voice.** User-facing documentation (getting started, guides, configuration reference) and contributor-facing documentation (architecture, test strategy, CONTRIBUTING) live side by side. The tone stays consistent across both.
- **API docs in docstrings.** The public API is documented in docstrings so it can be extracted by tools like [Griffe](https://mkdocstrings.github.io/griffe/) and [mkdocstrings](https://mkdocstrings.github.io/). Prose docs link into the generated reference rather than duplicating it.
- **No type duplication.** Type information lives in annotations. Docstrings describe semantics, not types.

## Tone of voice

We write in a **direct, professional, and approachable** tone. The guiding principle: help the reader move forward with as little friction as possible.

- Address the reader directly as "you" and "your" (second person). For example: "In your code, create an exporter and use the `render` method to create HTML."
- Use "we" to represent the project or the documentation team, never the reader. For example: "We welcome all support, whether on bug reports, code, design, reviews, tests, documentation, and more." / "We aim for 100% test coverage on all changes."
- Contractions are acceptable where they read naturally: "doesn't", "won't", "It's", "That's", "Don't". Do not force them, and do not avoid them.
- Avoid overly formal or academic phrasing. Sentences stay direct and plain. Prefer "use" over "utilise", "start" over "commence", "show" over "demonstrate" (except where "demonstrate" is the precise word).
- Be honest about limitations and trade-offs. We call out experimental features, known issues, and unsupported cases explicitly rather than glossing over them.
- Friendly sign-offs are welcome where they fit: "Done!", "Please get in touch!", "Hi! 👋". Keep them brief and genuine; avoid forced enthusiasm.

## Target audience

The documentation is written for **developers** integrating the exporter into a Python application, and **contributors** working on the library itself.

- We assume working knowledge of Python, HTML, and general web development concepts. Code examples use Python without explaining basic syntax.
- We do not assume prior knowledge of Draft.js. When a Draft.js concept (ContentState, blocks, entities, inline styles) is introduced, we explain it briefly and link to external resources for the full picture.
- We do not assume familiarity with the Wagtail or Django ecosystems, but we acknowledge them as the primary integration context. When a feature is particularly relevant to Wagtail users, we say so.
- Contributor docs assume familiarity with the project's development tooling (`uv`, `just`, `pytest`, `ruff`, `mypy`). We link to those tools' documentation rather than re-explaining them.
- We do not write for end users or content editors. The exporter is a developer library, not an end-user product.

## Content structure

### Page layout

Every page follows a predictable shape:

1. **H1 page title** – concise, descriptive, in Sentence case.
2. **Opening paragraph** – one or two sentences that tell the reader what the page covers and whether they are in the right place.
3. **Sections** – H2 for major sections, H3 for sub-sections within an H2. Use H4 and below sparingly; if a section needs five levels, consider splitting the page.
4. **Code examples** – placed immediately after the explanation they illustrate, not collected at the end of the page.

### Code examples

- Code blocks use fenced syntax (` ``` `) with a language identifier: `python`, `sh`, `bash`, `html`, `txt`.
- Examples should be self-contained where possible: a reader should be able to copy, paste, and run them.
- Inline comments inside code blocks are acceptable when they clarify non-obvious lines, but keep them short. Match the comment style used in the surrounding codebase (see [Coding style](CONTRIBUTING.md#coding-style-conventions)).
- Prefer showing the happy path first. Document edge cases, fallbacks, and advanced configuration in a separate sub-section or callout.

### Tables

- Use Markdown tables for structured reference data: configuration options, default mappings, supported versions, engine differences.
- Every column should have a header row.
- Keep table cells short. If a cell needs a paragraph of explanation, move it into prose below the table.

### Callouts and blockquotes

We use Markdown blockquotes for short, scoped callouts:

- **Experimental or status notes** at the top of a page:

  ```markdown
  > ⚠️ Markdown support is **experimental**. There is no guarantee of API stability at this time.
  ```

- **Code of Conduct reminders**:

  ```markdown
  > This project follows a [Code of Conduct](https://wagtail.org/code-of-conduct/).
  ```

- **Closing remarks** at the end of a procedure:

  ```markdown
  > As a last step, you may want to go update the [Draftail Playground](...) to this new release to check that all is well in a fully separate project.
  ```

Keep callouts to one or two sentences. Use them when the information directly affects how the reader proceeds, not as a general aside.

## Formatting

- Do not hard-wrap lines in prose. Let the editor handle wrapping. Prettier is configured with `proseWrap: "preserve"` and will not rewrap prose for you, so wrapping is a review-level concern rather than something `just format` fixes.
- Match the formatting of the document you are editing: heading levels, list styles, sentence structure, and how code spans and links are used. When an existing document and this guide disagree, prefer the document's conventions.
- Comments in code blocks follow the source code rule: avoid hard-wrapping, except at full stops or other natural punctuation breaks.

## Links

- Use **inline links** in prose. Prefer `[link text](url)` over bare URLs.
- Link to internal documentation with **relative paths**: `[contribution guidelines](CONTRIBUTING.md)`, `[test strategy](contributing/test-strategy.md)`.
- On first or prominent mention of a key concept, product, or external resource, link to its canonical source. Repeat links only when the repetition genuinely helps scanning in a longer section.
- External links should point to **official, stable resources**: the project's own GitHub repository and blog posts, the Draft.js docs, Wagtail documentation, Python packaging guides. Avoid linking to transient content (forum threads, personal gists) unless there is no canonical alternative.
- Link text should be descriptive. Avoid "click here" or "this link". Prefer the name of the target: "[introductory blog post](https://www.draftail.org/blog/2018/03/13/rethinking-rich-text-pipelines-with-draft-js)".
- Do not add links inside headings. They are harder to identify for screen reader users and break heading navigation.

## Headings and titles

- **H1** is used exactly once per page, for the page title.
- **H2** is the primary sectioning level within a page.
- **H3** is used for sub-sections within an H2. Use deeper levels only when the content genuinely requires it.
- Headings use **Sentence case**: "Getting started", "Custom components", "Project architecture", not "Getting Started" or "Project Architecture".
- Heading text is **plain**. Do not apply bold, italics, code formatting, or links inside headings.
- Prefer **noun phrases** for reference and conceptual pages ("Configuration", "Project architecture", "Test strategy"). Prefer **verb-first phrasing** for task-oriented pages or sub-sections within procedures ("Create an exporter", "Define your configuration").
- Keep headings concise. A heading should fit on a single line and give the reader enough context to decide whether to read the section.

## Terminology and language choices

### Spelling

We use **American English** spelling in prose: `normalization`, `serialization`, `organized`, `customized`, `behavior`. This is consistent with the spelling already used in the codebase and its identifiers.

Exceptions:

- **Proper nouns and product names** keep their own spelling regardless of locale.
- When a prose sentence refers to a specific code symbol, use the symbol's exact spelling.

### Capitalization

- **Sentence case** for headings and titles, always.
- Capitalize proper nouns: Draft.js, ContentState, Wagtail, Django, React, BeautifulSoup, lxml, html5lib.
- "the exporter" is lowercase – it is the project's shorthand for `draftjs_exporter`, not a proper noun.
- Constants and enum values are written in their source form: `BLOCK_TYPES.HEADER_TWO`, `ENTITY_TYPES.LINK`, `INLINE_STYLES.BOLD`.

### Punctuation

- Use an **en dash** (`–`) with surrounding spaces as a separator in lists and inline definitions, matching the existing docs:

  ```markdown
  - **Unit tests** – individual classes and functions in isolation.
  - **Integration tests** – `test_output.py` exercises the full pipeline end-to-end.
  ```

### Referring to the reader

- We say "you" and "your". We do not say "the user" when addressing the reader of the documentation.
- "Users" as a noun refers to other people consuming the exporter's output or integrating it upstream, not the reader: "end users", "integrators".

### Referring to the project

- "the exporter" – the preferred shorthand for `draftjs_exporter` in prose.
- "the library" – acceptable when distinguishing from the application integrating it.
- "the project" – used when referring to the open source effort as a whole (maintenance, roadmap, community).

### Draft.js terminology

- **Draft.js** – always with the period, capital D.
- **ContentState** – capitalized, the Draft.js data model. Always one word.
- **block** – lowercase unless starting a sentence. Draft.js blocks are lines of content.
- **entity** – lowercase. Entities carry data (links, images, embeds).
- **inline style** – lowercase, two words. Inline styles are character-level formatting (bold, italic, code).
- **entity range** / **inline style range** – lowercase. These annotate ranges of text within a block.

### Modal verbs

- Use **"can"** for capability: "You can join the `#draftail` channel on Wagtail's Slack."
- Use **"should"** for recommendations: "All output changes should be covered with unit tests, integration tests, and snapshot tests."
- Reserve **"must"** for hard requirements, especially around security: "`HTML.render()` must not raise on any structurally valid `ContentState`."
- Use **"may"** for possibility or optional behaviors: "You may want to go update the Draftail Playground."

## Warnings, notes, and edge cases

We document limitations and edge cases directly in the relevant page, not hidden in a separate caveats section.

- State limitations as facts, not apologies: "There is no workaround if you need to use a data key called `entity` – it won't be available."
- Call out **experimental** features at the top of their page with a blockquote, so readers see the status before investing in the content.
- When a behavior differs between engines, say so explicitly: "Engine output often differs in small ways. For example, quote escaping in attributes, self-closing tags, and attribute name validation strictness exist between engines by design."
- Security-relevant gotchas go in [SECURITY.md](SECURITY.md) and are cross-linked from the relevant guide pages.
