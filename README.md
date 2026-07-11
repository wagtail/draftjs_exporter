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

## Documentation

The full documentation is available at [on the docs website](https://wagtail.github.io/draftjs_exporter/). For LLM-assisted tooling, there is also a concise [`llms.txt`](https://wagtail.github.io/draftjs_exporter/llms.txt) and a complete [`llms-full.txt`](https://wagtail.github.io/draftjs_exporter/llms-full.txt).

## Contributing

See anything you like in here? Anything missing? We welcome all support, whether on bug reports, feature requests, code, design, reviews, tests, documentation, and more. Please have a look at our [contribution guidelines](docs/CONTRIBUTING.md).

## Credits

Draftail was created by [Springload](https://github.com/springload/), and is now maintained by Wagtail contributors. View the full list of [contributors](https://github.com/wagtail/draftjs_exporter/graphs/contributors). MIT licensed.
