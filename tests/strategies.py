"""Hypothesis strategies for generating Draft.js ContentState fixtures.

Shared building blocks for property-based tests. Keep strategies here rather
than inline in test modules so they can be composed and reused across
`tests/test_properties.py` and any future property-based test module.
"""

from typing import Any

from hypothesis import strategies as st

from draftjs_exporter.constants import BLOCK_TYPES, INLINE_STYLES

# A representative subset of block types/styles – enough to exercise nesting,
# nested lists, and inline style overlap without inflating the search space
# with rarely-interacting variants.
BLOCK_TYPE_VALUES = [
    BLOCK_TYPES.UNSTYLED,
    BLOCK_TYPES.HEADER_ONE,
    BLOCK_TYPES.UNORDERED_LIST_ITEM,
    BLOCK_TYPES.ORDERED_LIST_ITEM,
    BLOCK_TYPES.BLOCKQUOTE,
    BLOCK_TYPES.ATOMIC,
]

STYLE_VALUES = [
    INLINE_STYLES.BOLD,
    INLINE_STYLES.ITALIC,
    INLINE_STYLES.UNDERLINE,
    INLINE_STYLES.STRIKETHROUGH,
]

ENTITY_TYPE_VALUE = "LINK"

# Text likely to trigger offset/length edge cases: empty, unicode, and
# combining characters, alongside plain ASCII. Lone surrogates ("Cs") and
# control characters ("Cc", e.g. NUL) are excluded: they cannot occur in
# text a browser-based rich text editor would produce, and some engines
# (e.g. lxml) reject them outright as invalid XML/HTML content – that is a
# precondition on callers, not a bug in the exporter.
block_text = st.text(
    alphabet=st.characters(blacklist_categories=["Cs", "Cc"]),
    max_size=40,
)


@st.composite
def ranges(
    draw: st.DrawFn, text: str, style_or_key: st.SearchStrategy[dict[str, Any]]
) -> dict[str, Any]:
    """Build a single {offset, length, ...} range valid for the given text."""
    text_length = len(text)
    offset = draw(st.integers(min_value=0, max_value=text_length))
    length = draw(st.integers(min_value=0, max_value=text_length - offset))
    return {"offset": offset, "length": length, **draw(style_or_key)}


def style_ranges(text: str) -> st.SearchStrategy[list[dict[str, Any]]]:
    """Valid, in-bounds inlineStyleRanges for the given block text."""
    style = st.builds(lambda s: {"style": s}, st.sampled_from(STYLE_VALUES))
    # ty doesn't yet model the ParamSpec signature rewrite that @st.composite
    # applies (dropping the leading `draw` parameter for callers) - false positive.
    return st.lists(ranges(text, style), max_size=4)


@st.composite
def entity_ranges(
    draw: st.DrawFn, text: str, entity_keys: list[int]
) -> list[dict[str, Any]]:
    """Valid entityRanges referencing the given entity keys.

    Unlike style ranges, entity ranges are generated non-overlapping: in
    Draft.js's own model each character belongs to at most one entity, so
    two different entities can never share a character. Ranges that
    overlap (whether identical spans or improperly-nested spans) are not
    realistic input from a Draft.js editor - see docs/CONTRIBUTING.md for
    the corresponding "assumes properly nested/disjoint ranges" note on
    EntityState.
    """
    text_length = len(text)
    if not entity_keys or text_length == 0:
        return []

    num_segments = draw(st.integers(min_value=1, max_value=min(4, text_length)))
    cuts = sorted(
        draw(
            st.lists(
                st.integers(min_value=0, max_value=text_length),
                min_size=num_segments - 1,
                max_size=num_segments - 1,
                unique=True,
            )
        )
    )
    bounds = [0, *cuts, text_length]

    entity_ranges_list: list[dict[str, Any]] = []
    for start, stop in zip(bounds, bounds[1:]):
        if start == stop:
            continue
        if draw(st.booleans()):
            entity_ranges_list.append(
                {
                    "offset": start,
                    "length": stop - start,
                    "key": draw(st.sampled_from(entity_keys)),
                }
            )

    return entity_ranges_list


@st.composite
def blocks(draw: st.DrawFn, entity_keys: list[int]) -> dict[str, Any]:
    """A single Draft.js block, with in-bounds style/entity ranges."""
    text = draw(block_text)
    return {
        "key": draw(
            st.text(
                alphabet=st.characters(min_codepoint=97, max_codepoint=122),
                min_size=5,
                max_size=5,
            )
        ),
        "text": text,
        "type": draw(st.sampled_from(BLOCK_TYPE_VALUES)),
        "depth": draw(st.integers(min_value=0, max_value=4)),
        "inlineStyleRanges": draw(style_ranges(text)),
        "entityRanges": draw(entity_ranges(text, entity_keys)),
    }


@st.composite
def content_states(draw: st.DrawFn, max_blocks: int = 6) -> dict[str, Any]:
    """A full ContentState: an entityMap plus a list of consistent blocks."""
    num_entities = draw(st.integers(min_value=0, max_value=10))
    # Entity ranges reference entities by integer key; the entityMap looks
    # them up by their string form (see Command.from_entity_ranges).
    entity_keys = list(range(num_entities))
    entity_map = {
        str(key): {
            "type": ENTITY_TYPE_VALUE,
            "mutability": "MUTABLE",
            "data": {"url": "https://example.com"},
        }
        for key in entity_keys
    }

    block_list = draw(st.lists(blocks(entity_keys), min_size=0, max_size=max_blocks))

    return {"entityMap": entity_map, "blocks": block_list}


# Markdown-syntax fragments used to exercise every parser branch in the
# importer (styles, links, images, inline HTML tags, block-level syntax,
# escapes). Combined randomly they produce adversarial inputs that
# stress edge cases the hand-written unit tests don't cover: unterminated
# links, mismatched markers, malformed HTML tags, deeply nested syntax.
MARKDOWN_FRAGMENTS = [
    # Style markers (open/close asymmetries, nesting, intraword).
    "**",
    "__",
    "*",
    "_",
    "~",
    "~~",
    "`",
    "*a",
    "_b",
    "**c",
    "~d",
    "`e",
    # Link / image syntax: well-formed, broken, and exotic schemes.
    "[",
    "]",
    "(",
    ")",
    "![",
    "](http://",
    "![alt](",
    "](url)",
    "http://example.com",
    "wagtail://core.Page.89",
    ' "title"',
    " 'title'",
    '"',
    "'",
    # Inline HTML tags: known style mappings and unknown tags.
    "<u>",
    "</u>",
    "<sup>",
    "</sup>",
    "<mark>",
    "</mark>",
    "<sub>",
    "</sub>",
    "<kbd>",
    "</kbd>",
    "<unknown>",
    "</unknown>",
    "<",
    ">",
    "</",
    "/>",
    # Block-level prefixes.
    "#",
    "##",
    "###",
    "####",
    "#####",
    "######",
    "- ",
    "* ",
    "+ ",
    "1. ",
    "2. ",
    "1) ",
    "2) ",
    "> ",
    ">",
    "---",
    "***",
    "___",
    "```",
    "```python",
    "~~~",
    "~~~python",
    # Escapes (CommonMark set, sampled).
    "\\",
    "\\*",
    "\\_",
    "\\#",
    "\\[",
    "\\]",
    "\\(",
    "\\)",
    "\\`",
    "\\~",
    # Soft line breaks and plain text fillers.
    " ",
    "\n",
    "\n\n",
    "text",
    "hello",
    "world",
    "abc",
]

markdown_text = st.lists(
    st.sampled_from(MARKDOWN_FRAGMENTS), min_size=0, max_size=30
).map("".join)
"""Random Markdown built from syntax fragments for importer crash-safety."""


# Common HTML/JS injection fragments, used to check that block text and
# entity `data` can never break out of the tag/attribute they're rendered
# into (see docs/SECURITY.md#tampering). Each fragment contains at least one
# character (<, >, ", ') that must be escaped for the fragment to stay inert.
DANGEROUS_FRAGMENTS = [
    "<script>alert(1)</script>",
    '"><img src=x onerror=alert(1)>',
    "'><svg onload=alert(1)>",
    "</p><script>alert(1)</script><p>",
    '"',
    "'",
    "<",
    ">",
    "&",
]

dangerous_text = st.lists(
    st.sampled_from(DANGEROUS_FRAGMENTS), min_size=1, max_size=3
).map("".join)
"""Text built from concatenated XSS payload fragments rather than arbitrary unicode."""


@st.composite
def dangerous_content_states(draw: st.DrawFn) -> dict[str, Any]:
    """A single-block ContentState whose block text and entity `url` data
    are drawn from `DANGEROUS_FRAGMENTS`, to check that rendering escapes
    them rather than letting them become real markup or attributes.
    """
    text = draw(dangerous_text)
    entity_url = draw(dangerous_text)

    # An entity range referencing the whole (non-empty) block text, so the
    # `link` entity decorator wraps it in an <a href="{entity_url}">.
    entity_ranges = [{"offset": 0, "length": len(text), "key": 0}] if text else []

    return {
        "entityMap": {
            "0": {
                "type": ENTITY_TYPE_VALUE,
                "mutability": "MUTABLE",
                "data": {"url": entity_url},
            }
        },
        "blocks": [
            {
                "key": "aaaaa",
                "text": text,
                "type": BLOCK_TYPES.UNSTYLED,
                "depth": 0,
                "inlineStyleRanges": [],
                "entityRanges": entity_ranges,
            }
        ],
    }
