# Roadmap

This file provides an overview of the direction this project is heading. It contains both likely and more aspirational changes. For more granular improvements, see the [project’s issues backlog](https://github.com/wagtail/draftjs_exporter/issues).

## Planned

> Specific, well-scoped changes that have concrete time-bound implementation plans.

## Ready

> Feasible, near-term improvement ideas that are clear in scope.

### Performance regression baselines in CI

Add representative content fixtures and record `just benchmark` + memray stats per PR to fail builds on slowdowns in string, lxml, and html5lib engines.

### Configuration cookbook and compatibility matrix

Expand docs with end-to-end samples for Django/Wagtail and pure Python usage, plus tables covering supported Python versions, optional parser versions, and Draft.js releases.

### Release and maintenance automation

Add a tagged-release workflow that builds with `uv`, publishes to PyPI, updates `CHANGELOG`, and generates SBOMs; surface renovate rules and dependency review dashboards.

### AI-assisted configuration starter kit

Provide a cookbook showing how to prompt LLMs to draft block maps/entity decorators from HTML samples, and scripts to turn that output into typed configs and fixtures.

### Better automated code review

Improve our AI code review setup (currently OpenCodeReview in CI) based on false-positive patterns observed on real PRs:

- **Require evidence before breakage claims.** Findings that claim behavior is broken ("X will never match") should be verified against the test suite first — several flagged "bugs" were directly refuted by existing passing tests the bot itself cited.
- **Verify type-coercion claims against the code.** Claims about type mismatches should check the actual data flow (e.g. attribute stringification in `DOM.create_element`) before asserting a comparison can never hold.
- **Deduplicate findings.** The same issue was reported three times across two runs (a cosmetic comparison-idiom nit). Group repeats into a single finding.
- **Suppress non-findings.** Comments that suggest exactly the code as written, or conclude "no issue", should not be posted.
- **Calibrate severity by failure mode.** Distinguish "fails safe / cosmetic / hypothetical misuse" from real defects, and only post inline comments for actionable items.
- **Domain-aware reasoning.** Findings about Markdown/CommonMark behavior should be checked against the spec (e.g. what is legal inside a link destination) rather than pattern-matched from HTML escaping.

## Experimental

> Possible changes that require R&D, and high-risk ideas that could bring large benefits but with likely trade-offs.

### Rust-backed DOM engine

Prototype a Rust extension or PyO3 module for DOM construction to outperform the current string/lxml/html5lib engines on large documents.

### Streaming and async export

Explore a streaming API that yields HTML incrementally (sync/async) to reduce memory for very long ContentState exports.

### Python 3.12+ only refactor

After dropping 3.10/3.11, adopt 3.12+ features (faster f-strings, `typing.Self`/`TypeAliasType`, better `match` exhaustiveness) to simplify Options/State internals and improve runtime speed.

### More advanced tests

See:

- [Cosmic Ray](https://cosmic-ray.readthedocs.io/en/latest/)
- [MutMut](https://mutmut.readthedocs.io/en/latest/)
- [Hypothesis - State machines](https://hypothesis.readthedocs.io/en/latest/stateful.html)

## Backlog

> Likely useful but lower-priority or “filler” tasks.

### Demo gallery refresh

Publish a richer set of showcases (static site and notebooks) covering Wagtail, vanilla Django, Flask, and headless integrations with generated screenshots.

### Draft.js export diffing

Diff outputs between engines or configurations or content states.

### Security review cadence

Document a quarterly process to update upper bounds for html5lib/bs4/lxml, run CodeQL/SAST reports, and refresh SECURITY.md with any findings.
