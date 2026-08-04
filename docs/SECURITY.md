# Security policy

We take security issues seriously. We appreciate your efforts to responsibly disclose your findings, and will make every effort to acknowledge your contributions.

## Supported versions

This project doesn’t have formal support targets for non-latest versions. Backporting security fixes to affected releases will be decided on a case-by-case basis, based on effort involved and known usage of affected versions.

## Reporting a vulnerability

To report a vulnerability, please follow [Wagtail’s security reporting guidance](https://docs.wagtail.org/en/latest/contributing/security.html).

## Threat model

`draftjs_exporter` converts a Draft.js `ContentState` (blocks, inline style ranges, entity ranges, an entity map) into an HTML or Markdown string, via a pluggable rendering engine (`string`, `html5lib`, `lxml`, `markdown`) and a set of maps/decorators/entity handlers supplied by the integrating application.

Two things cross a trust boundary on every call:

- **`ContentState`** is the untrusted input. In a typical integration (like Wagtail), it comes from a rich text editor or external API integration, might be stored in a database, and later re-rendered for arbitrary site visitors. Soo it must be treated as attacker-controlled, including block text, `inlineStyleRanges`, `entityRanges`, and the `data` payload of each entity.
- **The rendered HTML string** is the output, which is often embedded directly into a page served to end users without further escaping. Anything that reaches that string unescaped is a potential vector for those end users.

By contrast, the `ExporterConfig` (`block_map`, `style_map`, `entity_decorators`, `composite_decorators`, `engine`) is developer-supplied, trusted code, not attacker input. The library assumes these are wired up by the integrating application, not derived from request data. As a diagram:

```txt
 Untrusted zone                    Trusted zone                     Untrusted zone
┌──────────────────┐   render()  ┌──────────────────────┐  string  ┌────────────────────┐
│ ContentState     │ ───────────▶│ HTML / DOM / engines │─────────▶│ Rendered HTML page │
│ (blocks, styles, │             │ (escaping happens    │          │ (viewed by other   │
│  entities, data) │             │  here)               │          │  end users)        │
└──────────────────┘             └──────────────────────┘          └────────────────────┘
                                            ▲
                                            │ configures
                                  ┌──────────────────────────┐
                                  │ ExporterConfig           │
                                  │ (block/style maps,       │
                                  │  entity decorators,      │
                                  │  engine, developer code) │
                                  └──────────────────────────┘
```

### Spoofing

Out of scope. Depends entirely on the integrating application.

### Tampering

- **Entity `data` is passed straight through into element attributes.** [`EntityState.render_entities`](https://github.com/wagtail/draftjs_exporter/blob/main/draftjs_exporter/entity_state.py) copies `entity_details["data"]` into the props of the element the entity decorator renders, e.g. a `LINK` entity's `url` typically becomes an `href`. Attribute values are HTML-escaped by every engine (`html.escape` in the `string` engine, BeautifulSoup/lxml elsewhere), which prevents attribute/quote breakout, but the library doesn't validate URL schemes. A malicious `"data": {"url": "javascript:alert(1)"}` will render as `href="javascript:alert(1)"` verbatim. Entity decorators that emit `href`, `src`, or similar URL-bearing attributes must validate the scheme (allow-list `http`/`https`/`mailto`) themselves.
- **`style` props are interpolated without CSS validation.** A style dict is converted to an inline `style="..."` string by joining property/value pairs; values aren’t validated as safe CSS, only escaped for the surrounding attribute quotes. Entity/decorator code that forwards untrusted `data` into `style` props can inject arbitrary CSS declarations (e.g. `url()`-based exfiltration).
- **`DOM.parse_html()` / `Elt.from_html()` intentionally bypass escaping.** This exists so integrators can render pre-sanitized, developer-controlled HTML fragments. If a decorator instead feeds it attacker-controlled text (e.g. raw entity data), that text is emitted into the page unescaped. That’s a stored-XSS vector. Never call `parse_html` with data sourced from ContentState.
- **The Markdown engine escapes user-controlled text and link destinations.** Block text is backslash-escaped following CommonMark rules (including at line starts, so attacker text cannot inject headings, lists, blockquotes, or link syntax), and URLs emitted into `](…)` destinations have `\`, `(`, `)` escaped and control characters percent-encoded. URL scheme validation remains the integrator's responsibility, exactly as for HTML output: a `"data": {"url": "javascript:alert(1)"}` renders as `[text](javascript:alert(1))` verbatim.

### Repudiation

The library does no logging and keeps no audit trail. Those can be added by implementers. Exceptions (`EntityException`, `WrapperException`, etc.) carry entity keys and, indirectly, fragments of the input; applications that surface these messages to end users (like via debug pages) could leak content that should not be exposed. Treat exporter exceptions as internal diagnostics and avoid exposing raw exception messages in production error pages.

### Information disclosure

The exporter does not perform network or filesystem access itself. Parsing raw markup with the `lxml` engine (`html.fromstring`) does not resolve external entities/DTDs by default, so classic XXE-style disclosure is not applicable there. The main disclosure risk is the exception-message leakage described under Repudiation, and, more generally, whatever an integrator's own entity decorators choose to do with entity `data`.

### Denial of service

ContentState should be treated as untrusted input. Please report any input that evades the project's [property-based tests](contributing/test-strategy.md#property-based-tests) that assess handling of anomalous content.

Another possible vector is `composite_decorators` strategies, that use developer-supplied regex patterns running against attacker-controlled block text on every render ([`composite_decorators.py`](https://github.com/wagtail/draftjs_exporter/blob/main/draftjs_exporter/composite_decorators.py)). Keep decorator regexes simple and anchored to avoid ReDoS, and enforce your own ContentState size/depth limits upstream if you accept documents from untrusted users.

### Elevation of privilege

This is out of scope as long as the exporter configuration is defined in code rather than from user input.

## Recommendations for integrators

1. Never construct exporter options from user/request data. Treat them as trusted, developer-authored configuration only.
2. In every entity decorator that emits a URL-bearing attribute (`href`, `src`, `poster`, …), validate the scheme against an allow-list before rendering it.
3. Avoid `parse_html()` with anything derived from untrusted input. Reserve it for static, developer-controlled markup.
4. Keep composite decorator `strategy` regexes simple and anchored, since they run against attacker-controlled block text on every render.
5. Don’t surface raw exporter exception messages to end users; log them internally instead.
6. If accepting arbitrarily large ContentState documents from untrusted users, enforce your own size/depth limits upstream of the exporter.
