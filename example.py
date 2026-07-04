#!/usr/bin/env -S uv run
"""Example usage of draftjs_exporter with custom components and fallbacks."""

import argparse
import cProfile
import json
import logging
import re
from pstats import Stats

from bs4 import BeautifulSoup

# draftjs_exporter provides default configurations and predefined constants for reuse.
from draftjs_exporter import (
    BLOCK_MAP,
    BLOCK_TYPES,
    DOM,
    ENTITY_TYPES,
    INLINE_STYLES,
    MARKDOWN_CONFIG,
    STYLE_MAP,
    ContentState,
    Element,
    Exporter,
    ExporterConfig,
    Props,
)
from draftjs_exporter.markdown.entities import link as markdown_link


def blockquote(props: Props) -> Element:
    """Render a blockquote with an optional cite attribute."""
    block_data = props["block"]["data"]

    return DOM.create_element(
        "blockquote", {"cite": block_data.get("cite")}, props["children"]
    )


def list_item(props: Props) -> Element:
    """Render a list item with a class reflecting its nesting depth."""
    depth = props["block"]["depth"]

    return DOM.create_element(
        "li", {"class": f"list-item--depth-{depth}"}, props["children"]
    )


def ordered_list(props: Props) -> Element:
    """Render an ordered list with a class reflecting its nesting depth."""
    depth = props["block"]["depth"]

    return DOM.create_element(
        "ol", {"class": f"list--depth-{depth}"}, props["children"]
    )


def image(props: Props) -> Element:
    """Render an image element from entity data."""
    return DOM.create_element(
        "img",
        {
            "src": props.get("src"),
            "width": props.get("width"),
            "height": props.get("height"),
            "alt": props.get("alt"),
        },
    )


def link(props: Props) -> Element:
    """Render a link entity as an anchor element."""
    return DOM.create_element("a", {"href": props["url"]}, props["children"])


def br(props: Props) -> Element:
    r"""Replace line breaks (\n) with br tags."""
    # Do not process matches inside code blocks.
    if props["block"]["type"] == BLOCK_TYPES.CODE:
        return props["children"]

    return DOM.create_element("br")


def hashtag(props: Props) -> Element:
    """Wrap hashtags in spans with a specific class."""
    # Do not process matches inside code blocks.
    if props["block"]["type"] == BLOCK_TYPES.CODE:
        return props["children"]

    return DOM.create_element("span", {"class": "hashtag"}, props["children"])


# See http://pythex.org/?regex=(http%3A%2F%2F%7Chttps%3A%2F%2F%7Cwww%5C.)(%5Ba-zA-Z0-9%5C.%5C-%25%2F%5C%3F%26_%3D%5C%2B%23%3A~!%2C%5C%27%5C*%5C%5E%24%5D%2B)&test_string=search%20http%3A%2F%2Fa.us%20or%20https%3A%2F%2Fyahoo.com%20or%20www.google.com%20for%20%23github%20and%20%23facebook&ignorecase=0&multiline=0&dotall=0&verbose=0
LINKIFY_RE = re.compile(
    r"(http://|https://|www\.)([a-zA-Z0-9\.\-%/\?&_=\+#:~!,\'\*\^$]+)"
)


def linkify(props: Props) -> Element:
    """Wrap plain URLs with link tags."""
    match = props["match"]
    protocol = match.group(1)
    url = match.group(2)
    href = protocol + url

    if props["block"]["type"] == BLOCK_TYPES.CODE:
        return href

    link_props = {"href": href}

    if href.startswith("www"):
        link_props["href"] = "http://" + href

    return DOM.create_element("a", link_props, href)


def linkify_markdown(props: Props) -> Element:
    """Wrap plain URLs with Markdown link syntax."""
    match = props["match"]
    protocol = match.group(1)
    url = match.group(2)
    href = protocol + url

    if props["block"]["type"] == BLOCK_TYPES.CODE:
        return href

    link_props = {
        "url": href,
        "children": href,
    }

    if href.startswith("www"):
        link_props["url"] = "http://" + href

    return markdown_link(link_props)


def block_fallback(props: Props) -> Element:
    """Provide example fallback behavior for unknown block types."""
    type_ = props["block"]["type"]

    if type_ == "example-discard":
        logging.warning(
            f'Missing config for "{type_}". Discarding block, keeping content.'
        )
        # Directly return the block's children to keep its content.
        return props["children"]
    elif type_ == "example-delete":
        logging.error(f'Missing config for "{type_}". Deleting block.')
        # Return None to not render anything, removing the whole block.
        return None
    else:
        logging.warning(f'Missing config for "{type_}". Using div instead.')
        # Provide a fallback.
        return DOM.create_element("div", {}, props["children"])


def entity_fallback(props: Props) -> Element:
    """Provide example fallback behavior for unknown entity types."""
    type_ = props["entity"]["type"]
    key = props["entity"]["entity_range"]["key"]
    logging.warning(f'Missing config for "{type_}", key "{key}".')
    return DOM.create_element("span", {"class": "missing-entity"}, props["children"])


def style_fallback(props: Props) -> Element:
    """Provide example fallback behavior for unknown inline styles."""
    type_ = props["inline_style_range"]["style"]
    logging.warning(f'Missing config for "{type_}". Deleting style.')
    return props["children"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export Draft.js JSON to HTML and Markdown."
    )
    parser.add_argument(
        "infile",
        nargs="?",
        type=argparse.FileType("r"),
        default=None,
        help="Draft.js JSON file to convert, or - for STDIN",
    )
    args = parser.parse_args()

    config: ExporterConfig = {
        # `block_map` is a mapping from Draft.js block types to a definition of their HTML representation.
        # Extend BLOCK_MAP to start with sane defaults, or make your own from scratch.
        "block_map": {
            **BLOCK_MAP,
            # The most basic mapping format, block type to tag name.
            BLOCK_TYPES.HEADER_TWO: "h2",
            # Use a dict to define props on the block.
            BLOCK_TYPES.HEADER_THREE: {
                "element": "h3",
                "props": {"class": "u-text-center"},
            },
            # Add a wrapper (and wrapper_props) to wrap adjacent blocks.
            BLOCK_TYPES.UNORDERED_LIST_ITEM: {
                "element": "li",
                "wrapper": "ul",
                "wrapper_props": {"class": "bullet-list"},
            },
            # Use a custom component for more flexibility (reading block data or depth).
            BLOCK_TYPES.BLOCKQUOTE: blockquote,
            BLOCK_TYPES.ORDERED_LIST_ITEM: {
                "element": list_item,
                "wrapper": ordered_list,
            },
            # Provide a fallback component (advanced).
            BLOCK_TYPES.FALLBACK: block_fallback,
        },
        # `style_map` defines the HTML representation of inline elements.
        # Extend STYLE_MAP to start with sane defaults, or make your own from scratch.
        "style_map": {
            **STYLE_MAP,
            # Use the same mapping format as in the `block_map`.
            "KBD": "kbd",
            # The `style` prop can be defined as a dict, that will automatically be converted to a string.
            "HIGHLIGHT": {
                "element": "strong",
                "props": {"style": {"textDecoration": "underline"}},
            },
            # Provide a fallback component (advanced).
            INLINE_STYLES.FALLBACK: style_fallback,
        },
        "entity_decorators": {
            # Map entities to components so they can be rendered with their data.
            ENTITY_TYPES.IMAGE: image,
            ENTITY_TYPES.LINK: link,
            # Lambdas work too.
            ENTITY_TYPES.HORIZONTAL_RULE: lambda props: DOM.create_element("hr"),
            # Discard those entities.
            ENTITY_TYPES.EMBED: None,
            # Provide a fallback component (advanced).
            ENTITY_TYPES.FALLBACK: entity_fallback,
        },
        "composite_decorators": [
            # Use composite decorators to replace text based on a regular expression.
            {"strategy": re.compile(r"\n"), "component": br},
            {"strategy": re.compile(r"#\w+"), "component": hashtag},
            {"strategy": LINKIFY_RE, "component": linkify},
        ],
        # Specify which DOM backing engine to use.
        "engine": DOM.STRING,
    }

    exporter = Exporter(config)

    content_state: ContentState = {
        "entityMap": {
            "0": {
                "type": "LINK",
                "mutability": "MUTABLE",
                "data": {"url": "https://github.com/facebook/draft-js"},
            },
            "1": {
                "type": "LINK",
                "mutability": "MUTABLE",
                "data": {
                    "url": "https://facebook.github.io/react/docs/top-level-api.html#react.createelement"
                },
            },
            "2": {
                "type": "HORIZONTAL_RULE",
                "mutability": "IMMUTABLE",
                "data": {},
            },
            "3": {
                "type": "LINK",
                "mutability": "MUTABLE",
                "data": {
                    "url": "https://facebook.github.io/react/docs/jsx-in-depth.html"
                },
            },
            "4": {
                "type": "LINK",
                "mutability": "MUTABLE",
                "data": {"url": "https://github.com/wagtail/draftjs_exporter/pull/17"},
            },
            "5": {
                "type": "IMAGE",
                "mutability": "IMMUTABLE",
                "data": {
                    "alt": "Test image alt text",
                    "src": "https://placekitten.com/g/300/200",
                    "width": 300,
                    "height": 200,
                },
            },
            "6": {
                "type": "LINK",
                "mutability": "MUTABLE",
                "data": {"url": "http://embed.ly/"},
            },
            "7": {
                "type": "EMBED",
                "mutability": "IMMUTABLE",
                "data": {
                    "url": "http://www.youtube.com/watch?v=feUYwoLhE_4",
                    "title": "React.js Conf 2016 - Isaac Salier-Hellendag - Rich Text Editing with React",
                    "providerName": "YouTube",
                    "authorName": "Facebook Developers",
                    "thumbnail": "https://i.ytimg.com/vi/feUYwoLhE_4/hqdefault.jpg",
                },
            },
            "8": {
                "type": "EXAMPLE_MISSING",
                "mutability": "MUTABLE",
                "data": {"url": "http://www.youtube.com/watch?v=feUYwoLhE_4"},
            },
        },
        "blocks": [
            {
                "key": "b0ei9",
                "text": "draftjs_exporter is an HTML exporter for Draft.js content",
                "type": "header-two",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [{"offset": 41, "length": 8, "key": 0}],
                "data": {},
            },
            {
                "key": "74al",
                "text": "Try it out by running this file!",
                "type": "blockquote",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {"cite": "http://example.com/"},
            },
            {
                "key": "7htbd",
                "text": "Features 📝🍸",
                "type": "header-three",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "32lnv",
                "text": "The exporter aims to provide sensible defaults from basic block types and inline styles to HTML, that can easily be customised when required. For more advanced scenarios, an API is provided (mimicking React's createElement) to create custom rendering components of arbitrary complexity.",
                "type": "unstyled",
                "depth": 0,
                "inlineStyleRanges": [{"offset": 209, "length": 13, "style": "CODE"}],
                "entityRanges": [{"offset": 209, "length": 13, "key": 1}],
                "data": {},
            },
            {
                "key": "eqjvu",
                "text": " ",
                "type": "atomic",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [{"offset": 0, "length": 1, "key": 2}],
                "data": {},
            },
            {"text": "Here are some features worth highlighting:"},
            {
                "key": "2mhgt",
                "text": "Convert line breaks to <br>\nelements.",
                "type": "unordered-list-item",
                "depth": 0,
                "inlineStyleRanges": [{"offset": 23, "length": 4, "style": "CODE"}],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "f4gp0",
                "text": "Automatic conversion of entity data to HTML attributes (int & boolean to string, style object to style string).",
                "type": "unordered-list-item",
                "depth": 0,
                "inlineStyleRanges": [
                    {"offset": 81, "length": 12, "style": "CODE"},
                    {"offset": 97, "length": 12, "style": "CODE"},
                ],
                "entityRanges": [{"offset": 81, "length": 28, "key": 3}],
                "data": {},
            },
            {
                "key": "3cnm0",
                "text": "Wrapped blocks (<li> elements go inside <ul> or <ol>).",
                "type": "unordered-list-item",
                "depth": 0,
                "inlineStyleRanges": [
                    {"offset": 16, "length": 4, "style": "CODE"},
                    {"offset": 40, "length": 4, "style": "CODE"},
                    {"offset": 48, "length": 4, "style": "CODE"},
                ],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "h5rn",
                "text": "With arbitrary nesting.",
                "type": "unordered-list-item",
                "depth": 1,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "5qfeb",
                "text": "Common text styles: Bold, Italic, Underline, Monospace, Strikethrough. cmd + b",
                "type": "unordered-list-item",
                "depth": 2,
                "inlineStyleRanges": [
                    {"offset": 20, "length": 4, "style": "BOLD"},
                    {"offset": 26, "length": 6, "style": "ITALIC"},
                    {"offset": 34, "length": 9, "style": "UNDERLINE"},
                    {"offset": 45, "length": 9, "style": "CODE"},
                    {"offset": 56, "length": 14, "style": "STRIKETHROUGH"},
                    {"offset": 71, "length": 7, "style": "KBD"},
                ],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "2ol8n",
                "text": "Overlapping text styles. Custom styles too!",
                "type": "unordered-list-item",
                "depth": 2,
                "inlineStyleRanges": [
                    {"offset": 0, "length": 14, "style": "STRIKETHROUGH"},
                    {"offset": 12, "length": 4, "style": "BOLD"},
                    {"offset": 14, "length": 11, "style": "ITALIC"},
                    {"offset": 25, "length": 13, "style": "HIGHLIGHT"},
                ],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "2lno0",
                "text": "#hashtag support via #CompositeDecorators.",
                "type": "unordered-list-item",
                "depth": 3,
                "inlineStyleRanges": [],
                "entityRanges": [{"offset": 21, "length": 20, "key": 4}],
                "data": {},
            },
            {
                "key": "37n0m",
                "text": "Linkify URLs too! http://example.com/",
                "type": "unordered-list-item",
                "depth": 4,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "37n01",
                "text": "Depth can go back and forth, it works fiiine (1)",
                "type": "unordered-list-item",
                "depth": 2,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "37n02",
                "text": "Depth can go back and forth, it works fiiine (2)",
                "type": "unordered-list-item",
                "depth": 1,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "37n03",
                "text": "Depth can go back and forth, it works fiiine (3)",
                "type": "unordered-list-item",
                "depth": 2,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "37n04",
                "text": "Depth can go back and forth, it works fiiine (4)",
                "type": "unordered-list-item",
                "depth": 1,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "37n05",
                "text": "Depth can go back and forth, it works fiiine (5)",
                "type": "unordered-list-item",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "3tbpg",
                "text": " ",
                "type": "atomic",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [{"offset": 0, "length": 1, "key": 5}],
                "data": {},
            },
            {
                "key": "f7s8c",
                "text": " ",
                "type": "atomic",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [{"offset": 0, "length": 1, "key": 7}],
                "data": {},
            },
            {
                "key": "5t6c9",
                "text": "For developers 🚀",
                "type": "header-three",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "2nb2a",
                "text": "Import the library",
                "type": "ordered-list-item",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "cfom5",
                "text": "Define your configuration",
                "type": "ordered-list-item",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "e2114",
                "text": "Go!",
                "type": "ordered-list-item",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "adt4j",
                "text": "Optionally, define your custom components.",
                "type": "ordered-list-item",
                "depth": 1,
                "inlineStyleRanges": [
                    {"offset": 0, "length": 10, "style": "EXAMPLE_DISCARD"}
                ],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "ed7hu",
                "text": "def blockquote(props):\n    block_data = props['block']['data']\n    return DOM.create_element('blockquote', {\n        'cite': block_data.get('cite')\n    }, props['children'])\n",
                "type": "code-block",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "2nols",
                "text": "Discarded block but the content stays.",
                "type": "example-discard",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "3nols",
                "text": "Removed block.",
                "type": "example-delete",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
            {
                "key": "4nols",
                "text": "Render as div",
                "type": "example-fallback",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [{"offset": 10, "length": 3, "key": 8}],
                "data": {},
            },
            {
                "key": "1nols",
                "text": "Voilà!",
                "type": "unstyled",
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": [],
                "data": {},
            },
        ],
    }

    # Use file/STDIN input if provided, otherwise run the built-in demo.
    if args.infile is not None:
        content_state: ContentState = json.load(args.infile)

    # --- HTML export ---

    pr = cProfile.Profile()
    pr.enable()

    markup = exporter.render(content_state)

    pr.disable()
    p = Stats(pr)

    def prettify(markup: str) -> str:
        """Prettify HTML by stripping html/body/head wrappers."""
        return re.sub(
            r"</?(body|html|head)>",
            "",
            BeautifulSoup(markup, "html5lib").prettify(),
        ).strip()

    pretty = prettify(markup)

    print("=== HTML ===")  # noqa: T201
    print(pretty)  # noqa: T201

    p.strip_dirs().sort_stats("cumulative").print_stats(0)

    # --- Markdown export ---
    # Use the built-in Markdown config for a quick, opinionated conversion.
    # Extend it with fallbacks to handle custom types from the content state above.

    markdown_exporter = Exporter(
        {
            **MARKDOWN_CONFIG,
            "style_map": {
                **MARKDOWN_CONFIG["style_map"],
                INLINE_STYLES.FALLBACK: style_fallback,
            },
            "entity_decorators": {
                **MARKDOWN_CONFIG["entity_decorators"],
                ENTITY_TYPES.EMBED: None,
                ENTITY_TYPES.FALLBACK: entity_fallback,
            },
            "block_map": {
                **MARKDOWN_CONFIG["block_map"],
                BLOCK_TYPES.FALLBACK: block_fallback,
            },
            "composite_decorators": [
                {"strategy": LINKIFY_RE, "component": linkify_markdown},
            ],
        }
    )
    markdown_output = markdown_exporter.render(content_state)

    print("=== Markdown ===")  # noqa: T201
    print(markdown_output)  # noqa: T201

    styles = """
    /* Tacit CSS framework https://yegor256.github.io/tacit/ */
    input,textarea,select,button,html,body{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-size:18px;font-stretch:normal;font-style:normal;font-weight:300;line-height:29.7px}input,textarea,select,button,html,body{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-size:18px;font-stretch:normal;font-style:normal;font-weight:300;line-height:29.7px}th{font-weight:600}td,th{border-bottom:1.08px solid #ccc;padding:14.85px 18px}thead th{border-bottom-width:2.16px;padding-bottom:6.3px}table{display:block;max-width:100%;overflow-x:auto}input,textarea,select,button,html,body{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-size:18px;font-stretch:normal;font-style:normal;font-weight:300;line-height:29.7px}input,textarea,select,button{display:block;max-width:100%;padding:9.9px}label{display:block;margin-bottom:14.76px}input[type="submit"],input[type="reset"],button{background:#f2f2f2;border-radius:3.6px;color:#8c8c8c;cursor:pointer;display:inline;margin-bottom:18px;margin-right:7.2px;padding:6.525px 23.4px;text-align:center}input[type="submit"]:hover,input[type="reset"]:hover,button:hover{background:#d9d9d9;color:#000}input[type="submit"][disabled],input[type="reset"][disabled],button[disabled]{background:#e6e6e6;color:#b3b3b3;cursor:not-allowed}input[type="submit"],button[type="submit"]{background:#367ac3;color:#fff}input[type="submit"]:hover,button[type="submit"]:hover{background:#255587;color:#bfbfbf}input[type="text"],input[type="password"],input[type="email"],input[type="url"],input[type="phone"],input[type="tel"],input[type="number"],input[type="datetime"],input[type="date"],input[type="month"],input[type="week"],input[type="color"],input[type="time"],input[type="search"],input[type="range"],input[type="file"],input[type="datetime-local"],select,textarea{border:1px solid #ccc;margin-bottom:18px;padding:5.4px 6.3px}input[type="checkbox"],input[type="radio"]{float:left;line-height:36px;margin-right:9px;margin-top:8.1px}input,textarea,select,button,html,body{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-size:18px;font-stretch:normal;font-style:normal;font-weight:300;line-height:29.7px}pre,code,kbd,samp,var,output{font-family:Menlo,Monaco,Consolas,"Courier New",monospace;font-size:16.2px}pre{border-left:1.8px solid #96bbe2;line-height:25.2px;margin-top:29.7px;overflow:auto;padding-left:18px}pre code{background:none;border:0;line-height:29.7px;padding:0}code{background:#ededed;border:1.8px solid #ccc;border-radius:3.6px;display:inline-block;line-height:18px;padding:3px 6px 2px}input,textarea,select,button,html,body{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-size:18px;font-stretch:normal;font-style:normal;font-weight:300;line-height:29.7px}h1,h2,h3,h4,h5,h6{color:#000;margin-bottom:18px}h1{font-size:36px;font-weight:500;margin-top:36px}h2{font-size:25.2px;font-weight:400;margin-top:27px}h3{font-size:21.6px;margin-top:21.6px}h4{font-size:18px;margin-top:18px}h5{font-size:14.4px;font-weight:bold;margin-top:18px;text-transform:uppercase}h6{color:#ccc;font-size:14.4px;font-weight:bold;margin-top:18px;text-transform:uppercase}input,textarea,select,button,html,body{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-size:18px;font-stretch:normal;font-style:normal;font-weight:300;line-height:29.7px}a{color:#367ac3;text-decoration:none}a:hover{text-decoration:underline}hr{border-bottom:1px solid #ccc}small{font-size:15.3px}em,i{font-style:italic}strong,b{font-weight:600}*{border:0;border-collapse:separate;border-spacing:0;box-sizing:border-box;margin:0;outline:0;padding:0;text-align:left;vertical-align:baseline}html,body{height:100%;width:100%}body{background:#f5f5f5;color:#1a1a1a;padding:36px}p,ul,ol,dl,blockquote,hr,pre,table,form,fieldset,figure,address{margin-bottom:29.7px}section{margin-left:auto;margin-right:auto;max-width:100%;width:900px}article{background:#fff;border:1.8px solid #d9d9d9;border-radius:7.2px;padding:43.2px}header{margin-bottom:36px}footer{margin-top:36px}nav{text-align:center}nav ul{list-style:none;margin-left:0;text-align:center}nav ul li{display:inline;margin-left:9px;margin-right:9px}nav ul li:first-child{margin-left:0}nav ul li:last-child{margin-right:0}ol,ul{margin-left:29.7px}li ol,li ul{margin-bottom:0}@media (max-width: 767px){body{padding:18px}article{border-radius:0;margin:-18px;padding:18px}textarea,input,select{max-width:100%}fieldset{min-width:0}section{width:auto}fieldset,x:-moz-any-link{display:table-cell}}
    /* Custom styles to help with debugging */
    blockquote { border-left: 0.25rem solid #aaa; padding-left: 1rem; font-style: italic; }
    .u-text-center { text-align: center; }
    a:hover, a:focus { outline: 1px solid red; }
    .hashtag { color: pink; }
    .list-item--depth-1 { margin-left: 5rem; }
    """

    # Output to a styled HTML file for development.
    with open("example.html", "w", encoding="utf-8") as file:
        file.write(
            f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>draftjs_exporter test page</title>
<style>{styles}</style>
</head>
<body>
    {markup}
</body>
</html>
"""
        )

    # Output to a Markdown file to showcase the HTML output in GitHub (and see changes in git).
    with open("docs/example.md", "w", encoding="utf-8") as file:
        file.write(
            f"""
# Example output (generated by [`example.py`](../example.py))

## HTML

```html
{pretty}
```

## Markdown

{markdown_output}
"""
        )
