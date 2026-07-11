# Troubleshooting

Here are known issues, implementation details, and engine-specific behaviors. For background on engine differences, see [Alternative engines](guides/alternative-engines.md).

## Exporter behavior

Here are smaller implementation details that are important to how the exporter behaves.

- HTML attributes are added in alphabetical order for the `lxml` and `html5` engines, and in the order they are provided as for the default `string` engine.
- `unstyled` blocks without text render as an empty element.
- Inline ranges aiming the same offset and length are always rendered in the same order (alphabetical order of the style type - `BOLD`, `CODE`, `ITALIC`).
- `style` prop is rendered as-is if it is a string, or can also be a dict in which case its properties are converted into a string using `camel_to_dash`.
- Invalid attributes are left for the BeautifulSoup / html5lib parser to handle.
- HTML escaping is automatically done by BeautifulSoup / html5lib.
- The string engine escapes `&`, `<`, `>`, and single/double quotes in attributes, but not outside.

## libxml2 installation error

```sh
pip install draftjs_exporter
# [...]
# *********************************************************************************
# Could not find function xmlCheckVersion in library libxml2. Is libxml2 installed?
#*********************************************************************************
```

Solution: see [How to install lxml on Ubuntu](http://stackoverflow.com/a/6504860/1798491)

```bash
apt-get install libxml2-dev libxslt1-dev python-dev
```

## Entity props override

Entities receive their `data` as props, except for the key `entity` which is overriden with a dict containing additional data (`type`, `mutability`, etc.). This is a known issue (see [#91](https://github.com/wagtail/draftjs_exporter/issues/91)). There is no workaround if you need to use a data key called `entity` – it won’t be available.

This is also a problem if the entity's `data` contains a `children` key – this will also get overriden without any workaround possible.

> If you are writing a [custom entity component](guides/custom-components.md), pick data keys that avoid `entity` and `children`.
