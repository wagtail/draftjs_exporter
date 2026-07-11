# [Draft.js exporter](https://pypi.org/project/draftjs_exporter/)

> Library to convert rich text from Draft.js raw ContentState to HTML.

## Features

This project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html), and [measures performance](https://thib.me/python-memory-profiling-for-the-draft-js-exporter) and [code coverage](https://coveralls.io/github/wagtail/draftjs_exporter). Code is checked with [mypy](https://mypy.readthedocs.io/en/latest/index.html).

- Extensive configuration of the generated HTML.
- Default, extensible block & inline style maps for common HTML elements.
- Convert line breaks to `<br>` elements with decorators.
- Define any attribute in the block map – custom class names for elements.
- React-like API to create custom components.
- Automatic conversion of entity data to HTML attributes (int & boolean to string, style object to style string).
- Nested lists (`<li>` elements go inside `<ul>` or `<ol>`, with multiple levels).
- Output inline styles as inline elements (`<em>`, `<strong>`, pick and choose, with any attribute).
- Overlapping inline style and entity ranges.
- Static type annotations.

It is developed alongside the [Draftail](https://www.draftail.org/) rich text editor, for [Wagtail](https://github.com/wagtail/wagtail). Check out the [online demo](http://playground.draftail.org/), and our [introductory blog post](https://www.draftail.org/blog/2018/03/13/rethinking-rich-text-pipelines-with-draft-js).

## When to use the exporter

[Draft.js](https://draftjs.org/) is a rich text editor framework for [React](https://reactjs.org/). Its approach is different from most rich text editors because it does not store data as HTML, but rather in its own representation called ContentState. This exporter is useful when the ContentState to HTML conversion has to be done in a Python ecosystem.

The initial use case was to gain more control over the content managed by rich text editors in a Wagtail/Django site. If you want to read the full story, have a look at our blog post: [Rethinking rich text pipelines with Draft.js](https://www.draftail.org/blog/2018/03/13/rethinking-rich-text-pipelines-with-draft-js).

## Where to go next

- **New to Draft.js?** Read [Content state](content-state.md) to understand the data model the exporter consumes.
- **Ready to render?** Follow [Getting started](getting-started.md) to install and render your first ContentState.
- **Configure the output.** See [Configuration](reference/configuration.md) for block, style, and entity maps.
- **Render as Markdown.** The exporter also produces [Markdown output](markdown.md).
- **Write custom components.** Use the React-like [custom components](guides/custom-components.md) API, or define [fallback components](guides/fallback-components.md) for missing block and entity types.
- **Pick an engine.** The default `string` engine is dependency-free. See [Alternative engines](guides/alternative-engines.md) for `html5lib` and `lxml`.
- **Find an error?** See [Troubleshooting](troubleshooting.md) for known issues and implementation details, and the [API reference](reference/api.md) for the full public API.

## Contributing

See anything you like in here? Anything missing? We welcome all support, whether on bug reports, feature requests, code, design, reviews, tests, documentation, and more. Please have a look at our [contribution guidelines](CONTRIBUTING.md).

## Credits

Draftail was created by [Springload](https://github.com/springload/), and is now maintained by Wagtail contributors. View the full list of [contributors](https://github.com/wagtail/draftjs_exporter/graphs/contributors). MIT licensed.
