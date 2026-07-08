# Research and implementation notes

## R&D notes

### Useful resources

#### Draft.js

- https://medium.com/@rajaraodv/how-draft-js-represents-rich-text-data-eeabb5f25cf2
- https://github.com/nikgraf/awesome-draft-js
- https://github.com/rajaraodv/draftjs-examples

### Generating HTML in Python

- http://lxml.de/
- https://www.crummy.com/software/BeautifulSoup/
- https://github.com/html5lib/html5lib-python
- http://www.yattag.org/
- http://markup.sourceforge.net/
- http://pythonhosted.org/pyquery/
- https://wiki.python.org/moin/MiniDom

### Limitations of `lxml`

- Succinct documentation (http://lxml.de/tutorial.html is the best)
- XML parser first, not really meant to build HTML.
- No support for document fragments.
- No support for text nodes (`elt.text` and `elt.tail` attributes instead).

### Limitations of `html5lib`

- Generated HTML is always "made valid" by being wrapped in `<html><head></head><body></body></html>`.

### Limitations of `BeautifulSoup4`

- The API to parse/generate HTML is clunky.

#### Constraints (to be weighted)

- Keeping the coupling between the CMS and the editor low so that we can change the editor's capabilities without having to write back-end code
- Giving the CMS enough control over the generated HTML. Not sure if "the CMS" just means "back-end" or if some JS code next to the editor code counts as well.
- Maintaining this over time with changing Draft.js output formats and unmaintained or wildly changing AST formats
- Regardless of implementation, being on the right spot between: "over the lifetime of the site/CMS, a given piece of content should always render the same HTML" and "a piece of content should always render the _best_ HTML"
- Keeping the coupling between CMS and editor low so that we can swap editors easily (bigger scope than the one of a single site/project here)
- Favour logical completeness over raw speed. A regex parser will be faster than building a DOM. But caching makes that mostly irrelevant. The bottlenecks will all likely be in the DB lookups for inline entities anyway.

### Other approaches to exporting from Draft.js

We have so far discussed a few different strategies to solve the rendering problem. Below are some of our notes.

> We could create the HTML in JS when you save it in draft, then apply a similar strategy to Wagtail’s Rich Text, by iterating over the output with regexes?
> Still get the benefits of a _much_ improved quality of editor and we can make use of existing JS-based draft exporters.

- `contentState` to JSON, Python doing JSON to HTML, with this contentState -> HTML exporter
- `contentState` to AST to JSON, with AST to HTML in Python
- `contentState` to AST to HTML, with extra Python regexes
- `contentState` to HTML, with extra Python regexes

and it's not just contentState but contentState + some config

## History

> This project started as a Python port of the [draftjs_exporter](https://github.com/ignitionworks/draftjs_exporter) ruby library.

### Other Draft.js exporter implementations

> Full list on https://github.com/nikgraf/awesome-draft-js

- [BackDraft.js](https://github.com/evanc/backdraft-js)
- [Draft.js Exporter](https://github.com/rkpasia/draft-js-exporter)
- [Draft.js: Export ContentState to HTML](https://github.com/sstur/draft-js-export-html)
- [Redraft](https://github.com/lokiuz/redraft)
- [Draft.js exporter (Ruby)](https://github.com/ignitionworks/draftjs_exporter)
- [Draft.js AST Exporter](https://github.com/icelab/draft-js-ast-exporter)
- [Draft.js AST Importer](https://github.com/icelab/draft-js-ast-importer)
